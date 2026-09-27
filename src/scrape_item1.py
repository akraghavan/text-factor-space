"""Download every 10-K primary document in tenk_index and keep only the Item 1 (Business) text.
Rate-limited to <=8 req/s (SEC fair-access limit is 10). Checkpoints shards of 1000 filings."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED, SEC_UA
import pandas as pd, requests, time, threading, sys, os, glob
from concurrent.futures import ThreadPoolExecutor
from item1 import to_text, extract_item1
OUT=str(INTERIM/'item1'); os.makedirs(OUT,exist_ok=True)
UA={"User-Agent":SEC_UA,"Accept-Encoding":"gzip, deflate"}
idx=pd.read_parquet(str(INTERIM/'tenk_index.parquet')).sort_values('filing_date').reset_index(drop=True)
done=set()
for f in glob.glob(f'{OUT}/*.parquet'): done|=set(pd.read_parquet(f,columns=['accession']).accession)
todo=idx[~idx.accession.isin(done)]
print('todo',len(todo),'done',len(done),flush=True)
lock=threading.Lock(); last=[0.0]; GAP=1/8
sess=threading.local()
def get(url):
    if not hasattr(sess,'s'): sess.s=requests.Session(); sess.s.headers.update(UA)
    for k in range(5):
        with lock:
            w=last[0]+GAP-time.time()
            if w>0: time.sleep(w)
            last[0]=time.time()
        try:
            r=sess.s.get(url,timeout=90)
            if r.status_code==200: return r.text
            if r.status_code in (403,429,503): time.sleep(10*(k+1)); continue
            return None
        except Exception: time.sleep(5*(k+1))
    return None
def work(r):
    url=f"https://www.sec.gov/Archives/edgar/data/{r.cik}/{r.accession.replace('-','')}/{r.primary_doc}"
    h=get(url)
    if h is None: return (r.accession,r.cik,None,-1,0)
    t=to_text(h); b=extract_item1(t)
    return (r.accession,r.cik,b,len(b.split()) if b else 0,len(h))
shard=[]; n=0; t0=time.time()
with ThreadPoolExecutor(8) as ex:
    for res in ex.map(work, todo.itertuples(), chunksize=1):
        shard.append(res); n+=1
        if len(shard)>=1000:
            pd.DataFrame(shard,columns=['accession','cik','item1','n_words','html_bytes']).to_parquet(f'{OUT}/shard_{int(time.time()*1000)}.parquet'); shard=[]
            el=time.time()-t0; print(f'{n}/{len(todo)} {n/el:.2f}/s eta {(len(todo)-n)/(n/el)/3600:.2f}h',flush=True)
if shard: pd.DataFrame(shard,columns=['accession','cik','item1','n_words','html_bytes']).to_parquet(f'{OUT}/shard_{int(time.time()*1000)}.parquet')
print('DONE',flush=True)
