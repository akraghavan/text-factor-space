"""D10: download every 10-K primary document in tenk_index once and keep the raw bytes, gzip-compressed, in
data/raw/edgar_html/<accession>.html.gz, so extractor changes never need SEC again. Resumable (skips stored files;
writes are atomic), <= 8 requests/s (SEC fair access), SEC_USER_AGENT required. data/raw/edgar_html/_manifest.parquet
records accession, HTTP status, byte count and the response's declared encoding (requests' r.encoding, which is what
r.text used in P2), so decoding is a choice made at extraction time.
Run: SEC_USER_AGENT="Name email" caffeinate -i python src/refetch_html.py >> data/interim/refetch.log 2>&1"""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, SEC_UA
import gzip, threading, time
import pandas as pd, requests
from concurrent.futures import ThreadPoolExecutor
OUT = RAW / 'edgar_html'; OUT.mkdir(parents=True, exist_ok=True); MAN = OUT / '_manifest.parquet'
if not os.environ.get('SEC_USER_AGENT'): sys.exit('set SEC_USER_AGENT="Name email" (SEC fair access)')
lock = threading.Lock(); last = [0.0]; GAP = 1 / 8; sess = threading.local()

def get(url):
    if not hasattr(sess, 's'):
        sess.s = requests.Session(); sess.s.headers.update({"User-Agent": SEC_UA, "Accept-Encoding": "gzip, deflate"})
    status = None
    for k in range(5):
        with lock:
            w = last[0] + GAP - time.time()
            if w > 0: time.sleep(w)
            last[0] = time.time()
        try:
            r = sess.s.get(url, timeout=90); status = r.status_code
            if status == 200: return status, r.content, r.encoding
            if status in (403, 429, 503): time.sleep(10 * (k + 1)); continue
            return status, None, None
        except Exception: time.sleep(5 * (k + 1))
    return status or -1, None, None

def work(r):
    status, body, enc = get(f"https://www.sec.gov/Archives/edgar/data/{r.cik}/{r.accession.replace('-', '')}/{r.primary_doc}")
    if body is not None:
        tmp = OUT / f'.{r.accession}.tmp'
        with gzip.open(tmp, 'wb', compresslevel=6) as fh: fh.write(body)
        os.replace(tmp, OUT / f'{r.accession}.html.gz')
    return {'accession': r.accession, 'status': status, 'n_bytes': len(body) if body is not None else 0,
            'encoding': enc, 'fetched_at': pd.Timestamp.now(tz='UTC')}

def save(rows):
    d = pd.DataFrame(rows)
    if MAN.exists(): d = pd.concat([pd.read_parquet(MAN), d]).drop_duplicates('accession', keep='last')
    d.to_parquet(MAN)

if __name__ == '__main__':
    idx = pd.read_parquet(INTERIM / 'tenk_index.parquet').sort_values('filing_date').reset_index(drop=True)
    have = {p.name[:-8] for p in OUT.glob('*.html.gz')}
    todo = idx[~idx.accession.isin(have)]
    t0 = time.time(); print(f'{pd.Timestamp.now():%Y-%m-%d %H:%M:%S} start: todo {len(todo)}, stored {len(have)}', flush=True)
    rows, n = [], 0
    with ThreadPoolExecutor(8) as ex:
        for res in ex.map(work, todo.itertuples(), chunksize=1):
            rows.append(res); n += 1
            if n % 1000 == 0 or n == len(todo):
                save(rows); rows = []; el = time.time() - t0
                print(f'{pd.Timestamp.now():%H:%M:%S} {n}/{len(todo)} {n / el:.2f}/s eta {(len(todo) - n) / (n / el) / 3600:.2f}h', flush=True)
    if rows: save(rows)
    m = pd.read_parquet(MAN); bad = m[m.status != 200]
    print(f'{pd.Timestamp.now():%Y-%m-%d %H:%M:%S} DONE stored {len(list(OUT.glob("*.html.gz")))} of {len(idx)}; '
          f'non-200 {len(bad)} {bad.status.value_counts().to_dict()}; {(time.time() - t0) / 60:.1f} min', flush=True)
