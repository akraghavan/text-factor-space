"""Dense embeddings of each 10-K Item 1 (bge-small-en-v1.5, CPU). Embeds the first 2 x 512-token windows
of the business description and averages them (unit-normalised). Processes scraper shards incrementally."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED, SEC_UA
import pandas as pd, numpy as np, glob, os, time, torch
from sentence_transformers import SentenceTransformer
torch.set_num_threads(2)
SRC=str(INTERIM/'item1'); OUT=str(INTERIM/'emb'); os.makedirs(OUT,exist_ok=True)
m=SentenceTransformer('BAAI/bge-small-en-v1.5',device='cpu'); tok=m.tokenizer; m.max_seq_length=512
def windows(text,k=2,w=500):
    ids=tok(text[:40000],add_special_tokens=False,truncation=False)['input_ids']
    return [tok.decode(ids[i*w:(i+1)*w]) for i in range(k) if len(ids)>i*w+50]
while True:
    shards=sorted(glob.glob(f'{SRC}/shard_*.parquet'))
    todo=[s for s in shards if not os.path.exists(f"{OUT}/{os.path.basename(s)}")]
    if not todo:
        if os.path.exists(str(INTERIM/'scrape.log')) and 'DONE' in open(str(INTERIM/'scrape.log')).read(): break
        time.sleep(60); continue
    for s in todo:
        t0=time.time(); d=pd.read_parquet(s); d=d[d.n_words>=100].reset_index(drop=True)
        chunks=[]; owner=[]
        for i,t in enumerate(d.item1):
            ws=windows(t[t.find(' ',20):]); chunks+=ws; owner+=[i]*len(ws)
        E=m.encode(chunks,batch_size=32,normalize_embeddings=True,show_progress_bar=False)
        owner=np.array(owner); V=np.zeros((len(d),E.shape[1]),dtype=np.float32)
        np.add.at(V,owner,E); V/=np.linalg.norm(V,axis=1,keepdims=True)+1e-12
        pd.DataFrame({'accession':d.accession,'emb':list(V)}).to_parquet(f"{OUT}/{os.path.basename(s)}")
        print(os.path.basename(s),len(d),len(chunks),f'{time.time()-t0:.0f}s',flush=True)
print('EMB DONE',flush=True)
