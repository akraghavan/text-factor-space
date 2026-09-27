"""Map each 10-K (CIK, filing date) to a CRSP PERMNO valid on the filing date, via Compustat CIK -> gvkey -> CCM link."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED, SEC_UA
import pandas as pd
RAW=str(RAW); INT=str(INTERIM)
m=pd.read_parquet(f'{RAW}/crsp_msf.parquet')
cs=m[(m.sharetype=='NS')&(m.securitytype=='EQTY')&(m.securitysubtype=='COM')&(m.usincflg=='Y')&(m.primaryexch.isin(['N','A','Q']))]
cs_perm=set(cs.permno.unique())
lk=pd.read_csv(f'{RAW}/ccm_link.csv.gz',low_memory=False); lk.columns=lk.columns.str.lower()
lk['linkdt']=pd.to_datetime(lk.linkdt); lk['linkenddt']=pd.to_datetime(lk.linkenddt.replace('E','2099-12-31'),errors='coerce').fillna(pd.Timestamp('2099-12-31'))
lk=lk[lk.cik.notna()&lk.linkprim.isin(['P','C'])&lk.lpermno.isin(cs_perm)].copy(); lk['cik']=lk.cik.astype(int)
idx=pd.read_parquet(f'{INT}/tenk_index.parquet'); idx['filing_date']=pd.to_datetime(idx.filing_date)
j=idx.merge(lk[['cik','gvkey','lpermno','linkdt','linkenddt','sic','gsector','gind','gsubind','conm']],on='cik')
j=j[(j.filing_date>=j.linkdt)&(j.filing_date<=j.linkenddt)]
# one permno per filing: prefer the link whose permno has the largest market cap in the filing month
j['ym']=j.filing_date.dt.to_period('M')
cs2=cs.assign(ym=pd.to_datetime(cs.mthcaldt).dt.to_period('M'))[['permno','ym','mthcap']]
j=j.merge(cs2,left_on=['lpermno','ym'],right_on=['permno','ym'],how='left').sort_values('mthcap',ascending=False).drop_duplicates('accession')
j=j.rename(columns={'lpermno':'permno_link'}).drop(columns=['permno']).rename(columns={'permno_link':'permno'})
print('filings mapped',len(j),'of',len(idx),f'({len(j)/len(idx):.1%})','unique permnos',j.permno.nunique())
# drop amendments-in-same-fiscal-year duplicates: keep the latest 10-K per permno per report year
j['ryear']=pd.to_datetime(j.report_date,errors='coerce').dt.year
j=j.sort_values('filing_date').drop_duplicates(['permno','ryear'],keep='last')
print('after one-per-firm-year',len(j)); print(j.groupby(j.filing_date.dt.year).size().to_dict())
j.to_parquet(f'{INT}/tenk_linked.parquet')
