"""Build the 10-K filing index for the CRSP common-stock universe from SEC bulk submissions.zip."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED, SEC_UA; from universe import common_stock
import pandas as pd, zipfile, json, re
RAW=str(RAW); OUT=str(INTERIM)
m=pd.read_parquet(f'{RAW}/crsp_msf.parquet')
cs=common_stock(m)
cs_perm=set(cs.permno.unique())
lk=pd.read_csv(f'{RAW}/ccm_link.csv.gz',low_memory=False); lk.columns=lk.columns.str.lower()
lk['linkenddt']=pd.to_datetime(lk.linkenddt.replace('E','2099-12-31'),errors='coerce').fillna(pd.Timestamp('2099-12-31'))
lk['linkdt']=pd.to_datetime(lk.linkdt)
lk=lk[lk.lpermno.isin(cs_perm)&(lk.linkenddt>='2011-01-01')&lk.cik.notna()]
ciks=set(lk.cik.astype(int))
print('universe gvkeys',lk.gvkey.nunique(),'ciks',len(ciks))
z=zipfile.ZipFile(f'{RAW}/submissions.zip')
names=set(z.namelist())
rows=[]
def take(cik,block):
    for i,f in enumerate(block['form']):
        if f in ('10-K','10-K405','10-KT'):
            d=block['filingDate'][i]
            if d>='2011-06-01':
                rows.append((cik,f,d,block['reportDate'][i],block['acceptanceDateTime'][i],block['accessionNumber'][i],block['primaryDocument'][i],block['size'][i]))
missing=0
for cik in ciks:
    fn=f'CIK{cik:010d}.json'
    if fn not in names: missing+=1; continue
    s=json.loads(z.read(fn))
    take(cik,s['filings']['recent'])
    for extra in s['filings'].get('files',[]):
        if extra['filingTo']>='2011-06-01' and extra['name'] in names:
            take(cik,json.loads(z.read(extra['name'])))
idx=pd.DataFrame(rows,columns=['cik','form','filing_date','report_date','accept_dt','accession','primary_doc','size']).drop_duplicates('accession')
idx.to_parquet(f'{OUT}/tenk_index.parquet')
print('missing cik files',missing); print(idx.shape); print(idx.groupby(idx.filing_date.str[:4]).size().to_dict()); print(idx.form.value_counts().to_dict())
print((idx.primary_doc=='').sum(),'empty primary docs')
