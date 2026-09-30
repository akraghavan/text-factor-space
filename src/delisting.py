"""SPEC §3 delisting-return imputation for Element E (PREREG D14 item 1). Monthly returns only (C and D use daily data).

Source: data/raw/crsp_delist_2009_2026.csv.gz, CRSP Stock v2 (CIZ) Stock Delisting Information (WRDS query 11726815,
docs/WRDS_QUERIES.md): one row per PERMNO with DelistingDt, DelActionType, DelReasonType, PrimaryExch, DelRet,
DelRetMissType.

What CIZ already does (checked 30 Sep on this data, /tmp checks recorded in docs/STATUS.md):
  - The delisting return sits on the single daily row after DelistingDt (the last trading day); when DelRet is present
    that daily return equals DelRet (91.5%), and the monthly MthRet of the DelistingDt month equals
    (1 + return through the last trade) x (1 + DelRet) - 1 (91.5%; the rest are DelRet = 0 or price-based months).
    So a present DelRet is ALREADY in MthRet: it is never added again here (no double counting).
  - When DelRet is missing (DelRetMissType in {DG, DM, DP}; 298 PERMNOs), MthRet of the DelistingDt month is only the
    trading return through the last trade (95.1%): the delisting loss is simply absent.
Rule (SPEC §3, "for performance-related delistings"): in the DelistingDt month of a PERMNO whose DelRet is missing
and whose DelActionType is GDR (dropped by the exchange: financial guidelines, bankruptcy, low price, insufficient
capital, delinquent filings, ...; the CIZ counterpart of legacy codes 500 and 520-584), the month's return becomes
    r = (1 + MthRet) (1 + delta) - 1          (MthRet taken as 0 if missing)
with delta = -30% if PrimaryExch at delisting is N or A (NYSE, NYSE American) and -55% if Q (Nasdaq) (Shumway 1997;
Shumway & Warther 1999). An exchange outside N/A/Q in the delisting file falls back to the firm's CRSP monthly
PrimaryExch that month. Missing DelRet on non-performance delistings (GLI liquidations and going-private, MER, GEX)
is left as CRSP has it and counted. Sensitivity (PREREG): delta = 0, -30% or -100% applied uniformly to the same rows."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW
import numpy as np, pandas as pd

SRC = RAW / 'crsp_delist_2009_2026.csv.gz'
MISSING_TYPES = {'DG', 'DM', 'DP'}
PERFORMANCE = {'GDR'}
DELTA_PRIMARY = {'N': -0.30, 'A': -0.30, 'Q': -0.55}

def load(path=SRC):
    d = pd.read_csv(path, low_memory=False); d.columns = d.columns.str.lower()
    d['delistingdt'] = pd.to_datetime(d.delistingdt); d['ym'] = d.delistingdt.dt.to_period('M')
    d['delret_missing'] = d.delret.isna() | d.delretmisstype.isin(MISSING_TYPES)
    d['performance'] = d.delactiontype.isin(PERFORMANCE)
    return d

def adjust(monthly: pd.DataFrame, delist: pd.DataFrame | None = None, delta='primary'):
    """Return (adjusted copy of the monthly panel, stats). The panel needs permno, ym (Period[M]), ret, primaryexch.
    Adds ret_raw (CRSP MthRet as delivered) and delist_imputed (bool); ret is replaced only on imputed rows.
    delta: 'primary' (exchange-specific -30% / -55%) or a float applied to every imputed row (sensitivity)."""
    d = load() if delist is None else delist
    m = monthly.copy(); m['ret_raw'] = m.ret
    key = pd.MultiIndex.from_frame(m[['permno', 'ym']])
    imp = d[d.delret_missing & d.performance]
    left = d[d.delret_missing & ~d.performance]
    hit = key.isin(pd.MultiIndex.from_frame(imp[['permno', 'ym']]))
    m['delist_imputed'] = hit
    if hit.any():
        rows = m.loc[hit, ['permno', 'ym', 'primaryexch', 'ret']].merge(imp[['permno', 'ym', 'primaryexch']].rename(columns={'primaryexch': 'exch_del'}),
                                                                      on=['permno', 'ym'], how='left')
        exch = rows.exch_del.where(rows.exch_del.isin(list(DELTA_PRIMARY)), rows.primaryexch)
        dl = exch.map(DELTA_PRIMARY).to_numpy() if delta == 'primary' else np.full(len(rows), float(delta))
        if np.isnan(dl).any(): raise ValueError('an imputed delisting has no N/A/Q exchange')
        m.loc[hit, 'ret'] = (1 + rows.ret.fillna(0).to_numpy()) * (1 + dl) - 1
        used = exch.value_counts().to_dict()
    else: used = {}
    # the panel's own PrimaryExch in a delisting month is usually 'X' (CIZ), so report the exchange delta was set from
    stats = {'imputed_rows': int(hit.sum()), 'delta': delta,
             'by_exchange_used': used,
             'missing_nonperformance_left': int(key.isin(pd.MultiIndex.from_frame(left[['permno', 'ym']])).sum()),
             'present_delret_rows_changed': 0}
    # guard: rows whose DelRet is present must be untouched (it is already inside MthRet)
    pres = key.isin(pd.MultiIndex.from_frame(d[~d.delret_missing][['permno', 'ym']]))
    assert (m.loc[pres, 'ret'].fillna(-9) == m.loc[pres, 'ret_raw'].fillna(-9)).all()
    return m, stats
