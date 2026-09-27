"""Dense embeddings of each 10-K Item 1 (bge-small-en-v1.5). Embeds the first 2 x 500-token windows
of the business description and averages them (unit-normalised). One pass over the Item 1 shards not yet embedded;
--follow keeps polling for new shards until data/interim/scrape.log says DONE (to run alongside the scraper).
Env: TFS_DEVICE (default: mps > cuda > cpu), TFS_BATCH (default 64 on GPU, 32 on CPU), TFS_THREADS (CPU threads).
Each filer's own name and ticker are masked first (src/mask_names.py, D2) when data/interim/name_masks.parquet exists;
TFS_MASK=0 turns that off. Filings without a mask entry (not linked to CRSP) are embedded unmasked."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED, SEC_UA
import pandas as pd, numpy as np, glob, os, time, torch
from sentence_transformers import SentenceTransformer
if os.environ.get('TFS_THREADS'): torch.set_num_threads(int(os.environ['TFS_THREADS']))
DEV=os.environ.get('TFS_DEVICE') or ('mps' if torch.backends.mps.is_available() else 'cuda' if torch.cuda.is_available() else 'cpu')
BATCH=int(os.environ.get('TFS_BATCH') or (32 if DEV=='cpu' else 64)); FOLLOW='--follow' in sys.argv
MASKS={}
if os.environ.get('TFS_MASK','1')!='0' and os.path.exists(str(INTERIM/'name_masks.parquet')):
    from mask_names import load_masks, mask; MASKS=load_masks()
print('device',DEV,'batch',BATCH,'follow',FOLLOW,'name masks',len(MASKS),flush=True)
SRC=str(INTERIM/'item1'); OUT=str(INTERIM/'emb'); os.makedirs(OUT,exist_ok=True)
m=SentenceTransformer('BAAI/bge-small-en-v1.5',device=DEV); tok=m.tokenizer; m.max_seq_length=512
def windows(text,k=2,w=500):
    ids=tok(text[:40000],add_special_tokens=False,truncation=False)['input_ids']
    return [tok.decode(ids[i*w:(i+1)*w]) for i in range(k) if len(ids)>i*w+50]
while True:
    shards=sorted(glob.glob(f'{SRC}/shard_*.parquet'))
    todo=[s for s in shards if not os.path.exists(f"{OUT}/{os.path.basename(s)}")]
    if not todo:
        if not FOLLOW or (os.path.exists(str(INTERIM/'scrape.log')) and 'DONE' in open(str(INTERIM/'scrape.log')).read()): break
        time.sleep(60); continue
    for s in todo:
        t0=time.time(); d=pd.read_parquet(s); d=d[d.n_words>=100].reset_index(drop=True)
        chunks=[]; owner=[]
        nmask=0
        for i,(a,t) in enumerate(zip(d.accession,d.item1)):
            if a in MASKS: t,k=mask(t,*MASKS[a]); nmask+=k>0
            ws=windows(t[t.find(' ',20):]); chunks+=ws; owner+=[i]*len(ws)
        E=m.encode(chunks,batch_size=BATCH,normalize_embeddings=True,show_progress_bar=False)
        owner=np.array(owner); V=np.zeros((len(d),E.shape[1]),dtype=np.float32)
        np.add.at(V,owner,E); V/=np.linalg.norm(V,axis=1,keepdims=True)+1e-12
        pd.DataFrame({'accession':d.accession,'emb':list(V)}).to_parquet(f"{OUT}/{os.path.basename(s)}")
        print(os.path.basename(s),len(d),len(chunks),'masked',nmask,f'{time.time()-t0:.0f}s',flush=True)
print('EMB DONE',flush=True)
