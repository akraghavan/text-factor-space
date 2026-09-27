"""P0: convert the WRDS .csv.gz extracts in data/raw to the parquet files P1/P3/P4 read.
crsp_msf.parquet: all columns, lower-case names, mthcaldt as datetime. crsp_dsf_<range>.parquet: permno, date, cap, ret
(from PERMNO, DlyCalDt, DlyCap, DlyRet). crsp_dsf_pv_<range>.parquet (D12): permno (int32), date, prc (float32,
|DlyPrc|: CRSP marks a bid/ask midpoint with a minus sign), vol (float32, DlyVol shares); its permno-date keys are
compared with the matching return file. ccm_funda.parquet: all columns, lower-case. ccm_link stays csv (read directly).
Skips outputs newer than their source; --force rebuilds. Prints shapes, ranges and key counts only, never rows."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW
import pandas as pd, numpy as np, glob

def fresh(src, dst, force=False): return os.path.exists(dst) and os.path.getmtime(dst) >= os.path.getmtime(src) and not force
def lower(d): d.columns = d.columns.str.lower(); return d

def convert_msf(src, dst):
    m = lower(pd.read_csv(src, low_memory=False, dtype={'HdrCUSIP': str, 'Ticker': str, 'NAICS': str, 'SICCD': str}))
    m['mthcaldt'] = pd.to_datetime(m.mthcaldt)
    for c in ['mthret', 'mthretx', 'mthprc', 'mthcap', 'mthvol', 'shrout', 'vwretd']: m[c] = pd.to_numeric(m[c], errors='coerce')
    m['siccd'] = pd.to_numeric(m.siccd, errors='coerce').astype('Int32')   # keep SIC numeric; blanks -> <NA>
    m.to_parquet(dst); print('crsp_msf', m.shape, m.mthcaldt.min().date(), m.mthcaldt.max().date(), 'permnos', m.permno.nunique())

def convert_dsf(src, dst):
    d = lower(pd.read_csv(src, usecols=['PERMNO', 'DlyCalDt', 'DlyCap', 'DlyRet'], low_memory=False))
    d = d.rename(columns={'dlycaldt': 'date', 'dlycap': 'cap', 'dlyret': 'ret'})[['permno', 'date', 'cap', 'ret']]
    d['permno'] = d.permno.astype('int32'); d['date'] = pd.to_datetime(d.date)
    d['cap'] = pd.to_numeric(d.cap, errors='coerce'); d['ret'] = pd.to_numeric(d.ret, errors='coerce').astype('float32')
    d.to_parquet(dst); print(os.path.basename(dst), d.shape, d.date.min().date(), d.date.max().date(), 'permnos', d.permno.nunique(), 'ret NaN', int(d.ret.isna().sum()))

def convert_pv(src, dst, ret_file=None):
    """D12 daily price/volume. Returns the frame; prints row count, NaN counts and, if ret_file exists, the key overlap."""
    want = {'permno', 'dlycaldt', 'dlyprc', 'dlyvol'}
    d = lower(pd.read_csv(src, usecols=lambda c: c.lower() in want, low_memory=False))
    d = d.rename(columns={'dlycaldt': 'date', 'dlyprc': 'prc', 'dlyvol': 'vol'})[['permno', 'date', 'prc', 'vol']]
    d['permno'] = d.permno.astype('int32'); d['date'] = pd.to_datetime(d.date)
    d['prc'] = pd.to_numeric(d.prc, errors='coerce').abs().astype('float32')
    d['vol'] = pd.to_numeric(d.vol, errors='coerce').astype('float32')
    d = d.drop_duplicates(['permno', 'date'])
    d.to_parquet(dst)
    msg = (f'{os.path.basename(dst)} {d.shape} {d.date.min().date()} {d.date.max().date()} permnos {d.permno.nunique()} '
           f'prc NaN {int(d.prc.isna().sum())} vol NaN {int(d.vol.isna().sum())} vol == 0 {int((d.vol == 0).sum())}')
    if ret_file and os.path.exists(ret_file):
        r = pd.read_parquet(ret_file, columns=['permno', 'date'])
        k = d[['permno', 'date']].merge(r, how='outer', indicator=True)._merge.value_counts()
        msg += f"; keys vs {os.path.basename(ret_file)}: both {k.get('both', 0)}, pv only {k.get('left_only', 0)}, ret only {k.get('right_only', 0)}"
    print(msg); return d

def convert_funda(src, dst):
    f = lower(pd.read_csv(src, low_memory=False, dtype={'cik': str, 'naicsh': str, 'tic': str}))
    f['datadate'] = pd.to_datetime(f.datadate)
    f.to_parquet(dst); print('ccm_funda', f.shape, f.datadate.min().date(), f.datadate.max().date(), 'gvkeys', f.gvkey.nunique())

def main(raw=str(RAW), force=False):
    pq = lambda p: p.replace('.csv.gz', '.parquet')
    jobs = [(f'{raw}/crsp_msf.csv.gz', convert_msf), (f'{raw}/ccm_funda.csv.gz', convert_funda)]
    jobs += [(p, convert_dsf) for p in sorted(glob.glob(f'{raw}/crsp_dsf_[0-9]*.csv.gz'))]
    for src, fn in jobs:
        if not os.path.exists(src): print('missing', os.path.basename(src)); continue
        if fresh(src, pq(src), force): print('skip', os.path.basename(pq(src))); continue
        fn(src, pq(src))
    for src in sorted(glob.glob(f'{raw}/crsp_dsf_pv_*.csv.gz')):
        if fresh(src, pq(src), force): print('skip', os.path.basename(pq(src))); continue
        convert_pv(src, pq(src), pq(src).replace('crsp_dsf_pv_', 'crsp_dsf_'))
    if not glob.glob(f'{raw}/crsp_dsf_pv_*.csv.gz'): print('no crsp_dsf_pv_*.csv.gz yet (D12 daily price/volume)')

if __name__ == '__main__':
    main(force='--force' in sys.argv)
