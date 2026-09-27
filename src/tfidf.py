"""Hoberg-Phillips-style bag-of-words vectors, one vocabulary per filing year.
HP (2016): binary word vectors over product words, words in >25% of filings dropped, unit-normalised; similarity = cosine.
We keep alphabetic tokens (>=3 chars), drop English stopwords, keep words in >=5 docs and <=25% of docs."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED, SEC_UA
import pandas as pd, numpy as np, glob, scipy.sparse as sp, os
from sklearn.feature_extraction.text import TfidfVectorizer
INT=str(INTERIM); OUT=f'{INT}/tfidf'; os.makedirs(OUT,exist_ok=True)
lk=pd.read_parquet(f'{INT}/tenk_linked.parquet')[['accession','permno','filing_date']]
txt=pd.concat(pd.read_parquet(f,columns=['accession','item1','n_words']) for f in glob.glob(f'{INT}/item1/*.parquet'))
d=lk.merge(txt[txt.n_words>=100],on='accession')
for y,g in d.groupby(d.filing_date.dt.year):
    vec=TfidfVectorizer(lowercase=True,token_pattern=r'(?u)\b[a-z][a-z]{2,}\b',stop_words='english',min_df=5,max_df=0.25,binary=True,use_idf=False,norm='l2',dtype=np.float32)
    X=vec.fit_transform(g.item1.values)
    sp.save_npz(f'{OUT}/X_{y}.npz',X.tocsr()); g[['accession','permno','filing_date']].reset_index(drop=True).to_parquet(f'{OUT}/rows_{y}.parquet')
    pd.Series(vec.get_feature_names_out()).to_frame('word').to_parquet(f'{OUT}/vocab_{y}.parquet')
    print(y,X.shape,f'nnz/doc {X.nnz/X.shape[0]:.0f}',flush=True)
