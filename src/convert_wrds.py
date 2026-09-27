"""P0: convert the WRDS .csv.gz extracts in data/raw to the parquet files P1/P3/P4 read.
crsp_msf.parquet: all columns, lower-case names, mthcaldt as datetime. crsp_dsf_<range>.parquet: permno, date, cap, ret
(from PERMNO, DlyCalDt, DlyCap, DlyRet). ccm_funda.parquet: all columns, lower-case. ccm_link stays csv (read directly).
Skips outputs newer than their source; --force rebuilds. Prints shapes and ranges only, never rows."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW
import pandas as pd, glob
RAW=str(RAW); FORCE='--force' in sys.argv
def fresh(src,dst): return os.path.exists(dst) and os.path.getmtime(dst)>=os.path.getmtime(src) and not FORCE
def lower(d): d.columns=d.columns.str.lower(); return d

src=f'{RAW}/crsp_msf.csv.gz'; dst=src.replace('.csv.gz','.parquet')
if fresh(src,dst): print('skip',os.path.basename(dst))
else:
    m=lower(pd.read_csv(src,low_memory=False,dtype={'HdrCUSIP':str,'Ticker':str,'NAICS':str,'SICCD':str}))
    m['mthcaldt']=pd.to_datetime(m.mthcaldt)
    for c in ['mthret','mthretx','mthprc','mthcap','mthvol','shrout','vwretd']: m[c]=pd.to_numeric(m[c],errors='coerce')
    m['siccd']=pd.to_numeric(m.siccd,errors='coerce').astype('Int32')   # keep SIC numeric; blanks -> <NA>
    m.to_parquet(dst); print('crsp_msf',m.shape,m.mthcaldt.min().date(),m.mthcaldt.max().date(),'permnos',m.permno.nunique())

for src in sorted(glob.glob(f'{RAW}/crsp_dsf_*.csv.gz')):
    dst=src.replace('.csv.gz','.parquet')
    if fresh(src,dst): print('skip',os.path.basename(dst)); continue
    d=lower(pd.read_csv(src,usecols=['PERMNO','DlyCalDt','DlyCap','DlyRet'],low_memory=False))
    d=d.rename(columns={'dlycaldt':'date','dlycap':'cap','dlyret':'ret'})[['permno','date','cap','ret']]
    d['permno']=d.permno.astype('int32'); d['date']=pd.to_datetime(d.date)
    d['cap']=pd.to_numeric(d.cap,errors='coerce'); d['ret']=pd.to_numeric(d.ret,errors='coerce').astype('float32')
    d.to_parquet(dst); print(os.path.basename(dst),d.shape,d.date.min().date(),d.date.max().date(),'permnos',d.permno.nunique(),'ret NaN',int(d.ret.isna().sum()))

src=f'{RAW}/ccm_funda.csv.gz'; dst=src.replace('.csv.gz','.parquet')
if fresh(src,dst): print('skip',os.path.basename(dst))
else:
    f=lower(pd.read_csv(src,low_memory=False,dtype={'cik':str,'naicsh':str,'tic':str}))
    f['datadate']=pd.to_datetime(f.datadate)
    f.to_parquet(dst); print('ccm_funda',f.shape,f.datadate.min().date(),f.datadate.max().date(),'gvkeys',f.gvkey.nunique())
