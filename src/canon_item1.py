"""D10 step 3: canonical Item 1 from the stored primary documents (data/raw/edgar_html, src/refetch_html.py).

Decoding: UTF-8, else cp1252, else Latin-1 (P2 used requests' r.text, which is Latin-1 for every SEC response because
SEC sends no charset, so UTF-8 punctuation became mojibake). Both extractors run on every document:
v1 = item1.extract_item1(to_text(html)), v2 = item1.extract_item1_v2(html). A candidate is structurally valid if
  (a) it starts at an Item 1 / Business heading, not at a cross-reference to one ('Item 1. Business” above ...'),
  (b) it ends at the next item heading, not at a cross-reference to one (span cut at 'See “Part I, ' / 'See also "'),
  (c) it contains no unquoted Item 1A "Risk Factors" heading followed by risk-factor preamble (ran into Item 1A),
  (d) 300 <= words <= 40,000.
Rule: take the valid candidate; if both are valid and they differ (word-set Jaccard < 0.8), take v2 (line-aware); if
both are valid and agree, take v1 (the P2 text, so nothing moves without cause); if neither is valid, take the longer
non-empty one and mark extractor '<v>_invalid' (a < 300-word or > 40,000-word Item 1 exists; downstream n_words filters
decide). Output: data/interim/item1_canon/shard_<k>.parquet with the P2 columns (accession, cik, item1, n_words,
html_bytes) plus extractor, v1_words, v2_words, jaccard, v1_valid, v2_valid, encoding, mojibake (UTF-8 document with
non-ASCII bytes, i.e. one that P2's Latin-1 decoding garbled).
Run: python src/canon_item1.py [--sample N]"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM
import gzip, re, time
import numpy as np, pandas as pd
from item1 import to_text, extract_item1, extract_item1_v2

HTML = RAW / 'edgar_html'; OUT = INTERIM / 'item1_canon'
HEAD = re.compile(r'(?i)^\W{0,5}(?:part\s*i\W{0,5})?i\s*t\s*e\s*m\s*s?\s*1\b.{0,120}?b\s*u\s*s\s*i\s*n\s*e\s*s\s*s', re.S)
RF = re.compile(r'(?i)(?<![“"‘\w])item\s*1\s*a[\s\.\:\-–—]{0,6}risk\s*factors(?![”"’])[^“”"]{0,200}?(?:carefully consider|'
                r'following risk factors|risks described below|high degree of risk|investment in our (?:common stock|securities) involves)')
XREF_START = re.compile(r'(?i)^.{0,40}?b\s*u\s*s\s*i\s*n\s*e\s*s\s*s\s*(?:[-–—]\s*[^”"]{1,60})?[”"’]', re.S)   # 'Item 1. Business” (“Item 1”)'
XREF_END = re.compile(r'(?i)\b(?:see|also|in|under|to|of|and)\W{0,3}(?:part\s*i\W{0,3})?$')        # span cut at 'See “Part I, '

def decode(b):
    for enc in ('utf-8', 'cp1252'):
        try: return b.decode(enc), enc
        except UnicodeDecodeError: pass
    return b.decode('latin-1'), 'latin-1'

def valid(t):
    if not t: return False
    w = len(t.split())
    return (bool(HEAD.match(t)) and not XREF_START.match(t) and not XREF_END.search(t[-40:].rstrip())
            and not RF.search(t) and 300 <= w <= 40_000)

def jacc(a, b):
    A, B = set((a or '').lower().split()), set((b or '').lower().split())
    return len(A & B) / max(len(A | B), 1)

def one(acc):
    raw = gzip.open(HTML / f'{acc}.html.gz', 'rb').read(); h, enc = decode(raw)
    a, b = extract_item1(to_text(h)), extract_item1_v2(h)
    va, vb, j = valid(a), valid(b), jacc(a, b)
    if va and vb: pick, name = (b, 'v2') if j < 0.8 else (a, 'v1')
    elif va: pick, name = a, 'v1'
    elif vb: pick, name = b, 'v2'
    else:
        la, lb = len((a or '').split()), len((b or '').split())
        pick, name = (b, 'v2_invalid') if lb >= la and lb > 0 else ((a, 'v1_invalid') if la > 0 else (None, 'none'))
    return {'accession': acc, 'item1': pick, 'n_words': len(pick.split()) if pick else 0, 'html_bytes': len(raw),
            'extractor': name, 'v1_words': len((a or '').split()), 'v2_words': len((b or '').split()), 'jaccard': j,
            'v1_valid': va, 'v2_valid': vb, 'encoding': enc, 'mojibake': enc == 'utf-8' and not raw.isascii(),
            'v1_text': a, 'v2_text': b}

def run(accs, keep_candidates=False):
    from multiprocessing import Pool
    with Pool(min(4, max(1, (os.cpu_count() or 2) - 2))) as p: res = p.map(one, accs, chunksize=20)   # pool capped at 4 workers (thermal limit on the Mac)
    d = pd.DataFrame(res)
    return d if keep_candidates else d.drop(columns=['v1_text', 'v2_text'])

if __name__ == '__main__':
    t0 = time.time()
    idx = pd.read_parquet(INTERIM / 'tenk_index.parquet', columns=['accession', 'cik', 'filing_date']).sort_values('filing_date')
    have = {p.name[:-8] for p in HTML.glob('*.html.gz')}
    accs = [a for a in idx.accession if a in have]
    if '--sample' in sys.argv:
        n = int(sys.argv[sys.argv.index('--sample') + 1]); accs = list(pd.Series(accs).sample(n, random_state=11))
        d = run(accs, keep_candidates=True); d.to_parquet(INTERIM / 'canon_sample.parquet')
    else:
        OUT.mkdir(exist_ok=True); parts = []
        for k in range(0, len(accs), 2000):
            d = run(accs[k:k + 2000]).merge(idx[['accession', 'cik']], on='accession')
            d = d[['accession', 'cik', 'item1', 'n_words', 'html_bytes', 'extractor', 'v1_words', 'v2_words', 'jaccard', 'v1_valid', 'v2_valid', 'encoding', 'mojibake']]
            d.to_parquet(OUT / f'shard_{k // 2000:03d}.parquet'); parts.append(d.drop(columns='item1'))
            print(f'{k + len(d)}/{len(accs)} {time.time() - t0:.0f}s', flush=True)
        d = pd.concat(parts)
    print(f'{len(d)} documents, {time.time() - t0:.0f}s; extractor {d.extractor.value_counts().to_dict()}; encoding {d.encoding.value_counts().to_dict()}; '
          f'UTF-8 with non-ASCII bytes (garbled by P2 Latin-1 decoding) {int(d.mojibake.sum())}')
    print(f'valid v1 {d.v1_valid.mean():.1%}, v2 {d.v2_valid.mean():.1%}; both valid & differ (J < 0.8) {(d.v1_valid & d.v2_valid & (d.jaccard < 0.8)).sum()}; '
          f'> 300 words {(d.n_words > 300).mean():.1%}; median words {d.n_words.median():.0f}')
