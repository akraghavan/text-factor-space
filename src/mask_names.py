"""Mask each filer's own name and ticker in its Item 1 before embedding (SPEC §5 pitfalls; Glasserman & Lin 2023: a
pretrained encoder can recognise a named firm and bring in what it learned about it later). Used for the dense network
only (D2: H1 uses dense, names masked); bag-of-words stays unmasked.

Names: CRSP `issuernm` in the filing month and the 12 months before (point in time) plus Compustat `conm`, e.g.
"X P O INC", "FIVE 9 INC", "FARMERS NATL BANC CORP/OH". Variants: legal suffixes and state tags stripped; spaced
letters joined ("XPO", "FIVE9"); CRSP abbreviations expanded (NATL -> NATIONAL); trailing Holdings/Group dropped; the first
word alone ("DEVON") when it has >= 4 letters and is not an English word in WordNet. A variant matches case-insensitively with flexible
punctuation between words, but only where the matched text starts with a capital letter (so "Apple" is masked, "apple"
is not); single-word variants must have >= 3 letters. Tickers (>= 3 letters) match as exact upper-case tokens.
Name matches become "the Company" ("the Company's" for possessives); tickers become "TICKER".
Build: python src/mask_names.py  -> data/interim/name_masks.parquet (accession, patterns) and a coverage report."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import INTERIM, PROCESSED
import re, json
import numpy as np, pandas as pd

SUFFIX = re.compile(r'(?i)(?:[\s,]+(?:inc|incorporated|corp|corporation|co|company|cp|ltd|limited|plc|lp|l\.p|llc|n\.?v|s\.?a|'
                    r'the|trust|bancorp inc|-?cl\s*[a-c]|new|old|de|md|nv|pa|oh|ny|tx|ca))+\.?$')
TAG = re.compile(r'\s*/[A-Za-z]{2,3}/?\s*$|\s*-\s*cl\s*[a-c]\s*$|\s*\(.*?\)\s*$', re.I)
TRAIL = re.compile(r'(?i)\s+(?:holdings?|group|companies|hldgs)$')
ABBR = {'NATL': 'NATIONAL', 'INTL': 'INTERNATIONAL', 'FINL': 'FINANCIAL', 'SVCS': 'SERVICES', 'SYS': 'SYSTEMS', 'TECHS': 'TECHNOLOGIES',
        'HLDGS': 'HOLDINGS', 'MFG': 'MANUFACTURING', 'PPTYS': 'PROPERTIES', 'BANCSHS': 'BANCSHARES', 'PHARMS': 'PHARMACEUTICALS',
        'PHARMA': 'PHARMACEUTICALS', 'AMER': 'AMERICAN', 'INDS': 'INDUSTRIES', 'RES': 'RESOURCES', 'ENTMT': 'ENTERTAINMENT',
        'CMNTY': 'COMMUNITY', 'SVGS': 'SAVINGS', 'BK': 'BANK', 'CTR': 'CENTER', 'SOLNS': 'SOLUTIONS', 'THERAP': 'THERAPEUTICS',
        'COMMUN': 'COMMUNICATIONS', 'COMMS': 'COMMUNICATIONS', 'ELECS': 'ELECTRONICS', 'LABS': 'LABORATORIES', 'MGMT': 'MANAGEMENT',
        'ENTPRS': 'ENTERPRISES', 'INSTRS': 'INSTRUMENTS', 'PRODS': 'PRODUCTS', 'ASSOC': 'ASSOCIATES', 'SCIS': 'SCIENCES', 'TECH': 'TECHNOLOGY', 'MTG': 'MORTGAGE'}
LEGAL = r"(?:,?\s*(?:inc|incorporated|corp|corporation|co|company|ltd|limited|l\.?p|llc|plc|n\.v|s\.a|holdings?)\b\.?)?"
_WN = None
def _english(w):
    """True if w is an English word (any WordNet part of speech): such first words ("First", "American", "Delta") are not masked alone."""
    global _WN
    if _WN is None:
        import nltk; from paths import RAW; nltk.data.path.insert(0, str(RAW / 'nltk_data')); from nltk.corpus import wordnet; _WN = wordnet
    return bool(_WN.synsets(w.lower()))

def variants(name):
    """Name strings to mask for one raw database name."""
    s = str(name).strip()
    for _ in range(3): s = TAG.sub('', s); s = SUFFIX.sub('', s).strip(' .,&-')
    if not s: return set()
    out = {s}
    exp = ' '.join(ABBR.get(w.upper(), w) for w in s.split())
    if exp != s: out.add(exp)
    joined = re.sub(r'\b([A-Za-z0-9])\s(?=[A-Za-z0-9]\b)', r'\1', s)          # "X P O" -> "XPO", "A S T SPACEMOBILE" -> "AST SPACEMOBILE"
    out.add(joined)
    if len(s.split()) == 2 and len(s.replace(' ', '')) <= 12: out.add(s.replace(' ', ''))   # "FIVE 9" -> "FIVE9"
    for v in list(out):
        t = TRAIL.sub('', v).strip()
        if t and t != v: out.add(t)
    first = s.split()[0]
    if len(s.split()) >= 2 and len(first) >= 4 and first.isalpha() and not _english(first): out.add(first)   # "Devon", "Montrose"
    return {v for v in out if len(re.sub(r'[^A-Za-z]', '', v)) >= 3}

def pattern(v):
    words = re.split(r'[\s\-\.,&/]+', v.strip())
    return r'\b' + r'[\s\-\.,&/]*'.join(re.escape(w) for w in words if w) + LEGAL + r"(?:'s|’s)?(?![A-Za-z])"

def mask(text, pats, tickers=()):
    """Return (masked text, number of replacements)."""
    n = 0
    for p in sorted(pats, key=len, reverse=True):                           # longest variant first
        def rep(m):
            nonlocal n
            if not m.group(0)[0].isupper(): return m.group(0)
            n += 1; return "the Company's" if m.group(0)[-2:] in ("'s", '’s') else 'the Company'
        text = re.sub(p, rep, text, flags=re.I)
    for tk in tickers:
        text, k = re.subn(r'\b' + re.escape(tk) + r'\b', 'TICKER', text); n += k
    return text, n

def build():
    lk = pd.read_parquet(INTERIM / 'tenk_linked.parquet', columns=['accession', 'permno', 'filing_date', 'conm'])
    m = pd.read_parquet(PROCESSED / 'crsp_monthly.parquet', columns=['permno', 'ym', 'issuernm', 'ticker'])
    lk['ym'] = lk.filing_date.dt.to_period('M')
    rows = []
    g = m.groupby('permno')
    for r in lk.itertuples():
        h = g.get_group(r.permno) if r.permno in g.groups else m.iloc[:0]
        h = h[(h.ym <= r.ym) & (h.ym > r.ym - 13)]
        names = set(h.issuernm.dropna()) | ({r.conm} if isinstance(r.conm, str) else set())
        pats = sorted({pattern(v) for nm in names for v in variants(nm)})
        tks = sorted({t for t in h.ticker.dropna() if len(t) >= 3 and t.isalpha()})
        rows.append({'accession': r.accession, 'patterns': json.dumps(pats), 'tickers': json.dumps(tks)})
    out = pd.DataFrame(rows); out.to_parquet(INTERIM / 'name_masks.parquet'); return out

def load_masks():
    d = pd.read_parquet(INTERIM / 'name_masks.parquet')
    return {a: (json.loads(p), json.loads(t)) for a, p, t in zip(d.accession, d.patterns, d.tickers)}

if __name__ == '__main__':
    import glob
    out = build(); M = load_masks()
    t = pd.concat(pd.read_parquet(p, columns=['accession', 'item1', 'n_words']) for p in glob.glob(str(INTERIM / 'item1' / 'shard_*.parquet')))
    t = t[(t.n_words >= 100) & t.accession.isin(M)].drop_duplicates('accession', keep='last')
    s = t.sample(min(3000, len(t)), random_state=0)
    cnt, cnt1k = [], []
    for a, x in zip(s.accession, s.item1):
        p, k = M[a]; head = ' '.join(x.split()[:1000])
        cnt.append(mask(x, p, k)[1]); cnt1k.append(mask(head, p, k)[1])
    cnt, cnt1k = np.array(cnt), np.array(cnt1k)
    print(f'name_masks: {len(out)} linked filings; sample {len(s)}: >= 1 mask in Item 1 {np.mean(cnt > 0):.1%}, '
          f'in the first 1,000 words {np.mean(cnt1k > 0):.1%}; masks per filing median {np.median(cnt):.0f} '
          f'(first 1,000 words {np.median(cnt1k):.0f})')
