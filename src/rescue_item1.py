"""P2b: re-extract Item 1 with the line-aware v2 extractor (item1.extract_item1_v2) where v1 gave < 300 words.
  python src/rescue_item1.py --validate 40   v1 vs v2 on 40 random filings where v1 worked (agreement check only)
  python src/rescue_item1.py                 fetch every filing with v1 < 300 words, keep v2 if it has more words,
                                             write data/interim/item1_v2.parquet, then patch the shards in place
                                             (originals copied to data/interim/item1_v1/ first; column `extractor`
                                             = 'v1'/'v2') and delete the embeddings of patched shards so P5 redoes them.
Same SEC fair-access rate as P2 (<= 8 requests/s, SEC_USER_AGENT)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import INTERIM, SEC_UA
import glob, shutil, threading, time
import numpy as np, pandas as pd, requests
from concurrent.futures import ThreadPoolExecutor
from item1 import to_text, extract_item1, extract_item1_v2
SH = INTERIM / 'item1'; OUT = INTERIM / 'item1_v2.parquet'
lock = threading.Lock(); last = [0.0]; GAP = 1 / 8; sess = threading.local()

def get(url):
    if not hasattr(sess, 's'):
        sess.s = requests.Session(); sess.s.headers.update({"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"})
    for k in range(5):
        with lock:
            w = last[0] + GAP - time.time()
            if w > 0: time.sleep(w)
            last[0] = time.time()
        try:
            r = sess.s.get(url, timeout=90)
            if r.status_code == 200: return r.text
            if r.status_code in (403, 429, 503): time.sleep(10 * (k + 1)); continue
            return None
        except Exception: time.sleep(5 * (k + 1))
    return None

def url(r): return f"https://www.sec.gov/Archives/edgar/data/{r.cik}/{r.accession.replace('-', '')}/{r.primary_doc}"
def nw(t): return len(t.split()) if t else 0

def current():
    s = pd.concat(pd.read_parquet(f, columns=['accession', 'n_words']) for f in glob.glob(f'{SH}/shard_*.parquet'))
    return s.sort_values('n_words').drop_duplicates('accession', keep='last')

def validate(n):
    idx = pd.read_parquet(INTERIM / 'tenk_index.parquet'); ok = current().query('n_words >= 300')
    todo = idx[idx.accession.isin(ok.accession)].sample(n, random_state=7)
    def work(r):
        h = get(url(r))
        if h is None: return None
        a, b = extract_item1(to_text(h)), extract_item1_v2(h)
        A, B = set((a or '').lower().split()), set((b or '').lower().split())
        return nw(a), nw(b), len(A & B) / max(len(A | B), 1)
    with ThreadPoolExecutor(8) as ex: res = [x for x in ex.map(work, todo.itertuples()) if x]
    r = pd.DataFrame(res, columns=['v1', 'v2', 'jaccard'])
    print(f'validate: {len(r)} filings where v1 >= 300 words; word-set Jaccard v1 vs v2 median {r.jaccard.median():.3f}, '
          f'share > 0.8 {(r.jaccard > 0.8).mean():.0%}; v2/v1 words median {(r.v2 / r.v1).median():.2f}; v2 empty {(r.v2 == 0).sum()}')
    print(r.describe().round(2).to_string())

def rescue():
    idx = pd.read_parquet(INTERIM / 'tenk_index.parquet'); cur = current()
    todo = idx.merge(cur[cur.n_words < 300], on='accession')
    print('rescue candidates (v1 < 300 words)', len(todo), 'of which 0 words', int((todo.n_words == 0).sum()), flush=True)
    def work(r):
        h = get(url(r))
        if h is None: return (r.accession, None, -1, 0, r.n_words)
        b = extract_item1_v2(h); return (r.accession, b, nw(b), len(h), r.n_words)
    t0 = time.time()
    with ThreadPoolExecutor(8) as ex: res = list(ex.map(work, todo.itertuples()))
    d = pd.DataFrame(res, columns=['accession', 'item1', 'n_words', 'html_bytes', 'n_words_v1'])
    d.to_parquet(OUT)
    better = d[d.n_words > d.n_words_v1]
    print(f'fetched {len(d)} in {time.time() - t0:.0f}s; download failures {(d.n_words < 0).sum()}; v2 has more words: {len(better)}; '
          f'of the v1-zero: {((d.n_words_v1 == 0) & (d.n_words >= 100)).sum()}/{(d.n_words_v1 == 0).sum()} now >= 100 words, '
          f'{((d.n_words_v1 == 0) & (d.n_words > 300)).sum()} > 300', flush=True)
    apply(better)

def apply(better):
    bk = INTERIM / 'item1_v1'; bk.mkdir(exist_ok=True)
    rep = better.set_index('accession'); patched = 0
    for f in sorted(glob.glob(f'{SH}/shard_*.parquet')):
        s = pd.read_parquet(f)
        if 'extractor' not in s: s['extractor'] = 'v1'
        m = s.accession.isin(rep.index) & (s.n_words >= 0)
        if not m.any(): s.to_parquet(f); continue
        name = os.path.basename(f)
        if not (bk / name).exists(): shutil.copy2(f, bk / name)
        a = s.loc[m, 'accession']
        s.loc[m, 'item1'] = rep.item1.reindex(a).to_numpy(); s.loc[m, 'n_words'] = rep.n_words.reindex(a).to_numpy()
        s.loc[m, 'extractor'] = 'v2'; s.to_parquet(f); patched += 1
        e = INTERIM / 'emb' / name
        if e.exists(): e.unlink()
    print(f'patched {len(rep)} filings in {patched} shards (originals in {bk}); their embeddings deleted, rerun P5 and P6')

if __name__ == '__main__':
    if '--validate' in sys.argv: validate(int(sys.argv[sys.argv.index('--validate') + 1]))
    else: rescue()
