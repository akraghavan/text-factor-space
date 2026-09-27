"""Clean CRSP common-stock panels (monthly + daily) and Fama-French factors."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED, SEC_UA; from universe import common_stock
import pandas as pd, zipfile, io, os, glob
RAW=str(RAW); OUT=str(PROCESSED); os.makedirs(OUT,exist_ok=True)
def ff(zipname):
    z=zipfile.ZipFile(f'{RAW}/{zipname}'); txt=z.read(z.namelist()[0]).decode('latin1').splitlines()
    rows=[]; hdr=None
    for line in txt:
        p=[x.strip() for x in line.split(',')]
        if hdr is None and len(p)>1 and p[0]=='' : hdr=['date']+p[1:]; continue
        if hdr and p[0].isdigit() and len(p)==len(hdr): rows.append(p)
        elif hdr and rows and not p[0].isdigit(): break   # stop at the annual block
    d=pd.DataFrame(rows,columns=hdr); d[hdr[1:]]=d[hdr[1:]].astype(float)/100; return d
f5d=ff('F-F_Research_Data_5_Factors_2x3_daily_CSV.zip'); momd=ff('F-F_Momentum_Factor_daily_CSV.zip')
ffd=f5d.merge(momd,on='date'); ffd['date']=pd.to_datetime(ffd.date,format='%Y%m%d'); ffd.columns=[c.strip().replace('-','_') for c in ffd.columns]
f5m=ff('F-F_Research_Data_5_Factors_2x3_CSV.zip'); momm=ff('F-F_Momentum_Factor_CSV.zip')
ffm=f5m.merge(momm,on='date'); ffm['ym']=pd.PeriodIndex(pd.to_datetime(ffm.date,format='%Y%m'),freq='M'); ffm=ffm.drop(columns='date'); ffm.columns=[c.strip().replace('-','_') for c in ffm.columns]
ffd.to_parquet(f'{OUT}/ff_daily.parquet'); ffm.to_parquet(f'{OUT}/ff_monthly.parquet')
print('FF daily',ffd.date.min().date(),ffd.date.max().date(),ffd.columns.tolist()); print('FF monthly',ffm.ym.min(),ffm.ym.max())
m=pd.read_parquet(f'{RAW}/crsp_msf.parquet')
cs=common_stock(m).copy()
cs['ym']=pd.PeriodIndex(pd.to_datetime(cs.mthcaldt),freq='M')
cs=cs.rename(columns={'mthret':'ret','mthcap':'me','siccd':'sic'})[['permno','permco','ym','ret','me','mthprc','mthvol','shrout','sic','naics','primaryexch','ticker','issuernm','vwretd']]
cs['me']=cs.me*1000   # CIZ MthCap is in $000s; panels carry market cap in dollars (SPEC §3)
cs=cs.sort_values(['permno','ym']).drop_duplicates(['permno','ym'],keep='last')
cs['me_lag']=cs.groupby('permno').me.shift(1)
cs.to_parquet(f'{OUT}/crsp_monthly.parquet'); print('monthly',cs.shape, cs.ym.min(), cs.ym.max())
perm=set(cs.permno)
parts=[p for p in sorted(glob.glob(f'{RAW}/crsp_dsf_[0-9]*.parquet'))]   # returns/cap; crsp_dsf_pv_* hold price/volume (D12)
d=pd.concat([pd.read_parquet(p) for p in parts]); d=d[d.permno.isin(perm)].drop_duplicates(['permno','date']); d['cap']=d.cap*1000   # DlyCap $000s -> dollars
pv=sorted(glob.glob(f'{RAW}/crsp_dsf_pv_*.parquet'))
if pv:   # D12: |DlyPrc| and DlyVol for daily Amihud
    q=pd.concat([pd.read_parquet(p) for p in pv]).drop_duplicates(['permno','date'])
    d=d.merge(q,on=['permno','date'],how='left'); print('daily price/volume merged: prc',f'{d.prc.notna().mean():.1%}','vol',f'{d.vol.notna().mean():.1%}')
d.to_parquet(f'{OUT}/crsp_daily.parquet'); print('daily',d.shape,d.date.min().date(),d.date.max().date(),d.permno.nunique(), 'parts',parts)
