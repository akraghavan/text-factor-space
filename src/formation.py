"""Plumbing for Elements B and C (SPEC §6-§7): point-in-time universes, aligned daily excess-return and factor
matrices, residuals via tfs_stats (CLAUDE.md rule 3), and the pair-panel skeleton for C. No estimator lives here: the
only regression, `residuals`, calls tfs_stats.regression.ols_qr, which Abhi writes; until then it raises
NotImplementedError and B/C stop there.

Timing (SPEC §3). Formation month t: formation date = first calendar day of t. Universe, size and SIC from the end of
month t-1 (CRSP monthly, SPAC months excluded (D8), one PERMNO per PERMCO: the largest). Text vintage: the latest linked
10-K filed before the formation date and at most 15 months earlier. Book equity: Davis-Fama-French, fiscal year ending
in calendar year y-1 used from July y (>= 6 months after fiscal year end), over Dec y-1 market equity summed by PERMCO.
Momentum: R(t-12, t-2)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM, PROCESSED
import numpy as np, pandas as pd
from universe import exclude_spacs

FACTORS = ['Mkt_RF', 'SMB', 'HML', 'RMW', 'CMA', 'Mom']
_cache = {}
def _get(name, fn):
    if name not in _cache: _cache[name] = fn()
    return _cache[name]
def monthly(): return _get('m', lambda: pd.read_parquet(PROCESSED / 'crsp_monthly.parquet'))
def linked(): return _get('lk', lambda: pd.read_parquet(INTERIM / 'tenk_linked.parquet'))
def nwords():
    def f():
        r = pd.read_parquet(INTERIM / 'bow' / 'rows.parquet', columns=['accession', 'n_words'])
        return r.set_index('accession').n_words
    return _get('nw', f)

def formation_months(start='2012-07', end='2026-03'):
    """Monthly formation months (D4: networks updated monthly). Daily CRSP ends 2026-03-31."""
    return pd.period_range(start, end, freq='M')

def universe_at(t, text=True):
    """Firms at formation month t (Period[M]); columns permno, permco, me, sic, primaryexch, and with text=True the
    text vintage: accession, filing_date, fye_month (fiscal year end month of that 10-K), n_words."""
    t = pd.Period(t, 'M'); m = monthly()
    u = m[(m.ym == t - 1) & m.me.notna()]
    u = exclude_spacs(u).sort_values('me', ascending=False).drop_duplicates('permco')
    u = u[['permno', 'permco', 'me', 'sic', 'primaryexch']].reset_index(drop=True)
    if not text: return u
    start = t.to_timestamp()
    f = linked(); f = f[(f.filing_date < start) & (f.filing_date >= start - pd.DateOffset(months=15))]
    f = f.sort_values('filing_date').drop_duplicates('permno', keep='last')[['permno', 'accession', 'filing_date', 'report_date']]
    u = u.merge(f, on='permno')
    u['fye_month'] = pd.to_datetime(u.report_date, errors='coerce').dt.month
    u['n_words'] = nwords().reindex(u.accession.to_numpy()).to_numpy()
    return u[u.n_words >= 100].drop(columns='report_date').reset_index(drop=True)

def book_equity():
    """Davis-Fama-French book equity by (lpermno, fiscal year end), primary links only."""
    def f():
        a = pd.read_parquet(RAW / 'ccm_funda.parquet')
        a = a[a.linkprim.isin(['P', 'C'])].copy()
        se = a['seq'].fillna(a['ceq'] + a['pstk']).fillna(a['at'] - a['lt'])
        ps = a.pstkrv.fillna(a.pstkl).fillna(a.pstk).fillna(0)
        a['be'] = se + a.txditc.fillna(0) - ps
        a = a[a.be > 0]
        a['fy_cal'] = a.datadate.dt.year
        return a.sort_values('datadate').drop_duplicates(['lpermno', 'fy_cal'], keep='last')[['lpermno', 'fy_cal', 'be']]
    return _get('be', f)

def book_to_market(t):
    """B/M at formation month t: BE for fiscal years ending in y-1 (y = t.year if t.month >= 7 else t.year - 1),
    over PERMCO-summed market equity in December y-1. Indexed by permno."""
    t = pd.Period(t, 'M'); y = t.year if t.month >= 7 else t.year - 1
    be = book_equity(); be = be[be.fy_cal == y - 1].set_index('lpermno').be
    m = monthly(); d = m[m.ym == pd.Period(f'{y - 1}-12', 'M')]
    me = d.groupby('permco').me.transform('sum'); me.index = d.permno.to_numpy()
    bm = (be * 1e6) / me.reindex(be.index)                        # Compustat $ millions, CRSP me in dollars
    return bm.dropna()

def momentum(t):
    """R(t-12, t-2): compounded monthly return over months t-12..t-2 (>= 8 of 11 observed). Indexed by permno."""
    t = pd.Period(t, 'M'); m = monthly()
    w = m[(m.ym >= t - 12) & (m.ym <= t - 2)]
    g = w.groupby('permno').ret
    r = np.exp(g.apply(lambda s: np.log1p(s.dropna()).sum())) - 1
    return r[g.count() >= 8]

def amihud_monthly(t):
    """Fallback illiquidity (D12 open): mean over months t-12..t-1 of |r_m| / (mthvol x |mthprc|) (CRSP monthly share volume
    and price), >= 6 months observed. Replaced by the daily Amihud measure if DlyVol/DlyPrc are pulled. Indexed by permno."""
    t = pd.Period(t, 'M'); m = monthly()
    w = m[(m.ym >= t - 12) & (m.ym <= t - 1)]
    dv = w.mthvol * w.mthprc.abs()
    a = (w.ret.abs() / dv.where(dv > 0)).groupby(w.permno)
    return a.mean()[a.count() >= 6]

def amihud_from_arrays(R, P, V, min_obs=120):
    """Amihud (2002) illiquidity per column: mean over valid days of |r_d| / (|prc_d| x vol_d). Valid = finite return,
    price > 0, volume > 0 (zero-volume days skipped). Columns with fewer than min_obs valid days get NaN."""
    R, P, V = (np.asarray(a, dtype=np.float64) for a in (R, P, V))
    ok = np.isfinite(R) & np.isfinite(P) & np.isfinite(V) & (P > 0) & (V > 0)
    x = np.where(ok, np.abs(np.where(ok, R, 0)) / np.where(ok, P * V, 1), 0.0)
    n = ok.sum(0)
    with np.errstate(invalid='ignore', divide='ignore'): out = x.sum(0) / n
    out[n < min_obs] = np.nan
    return out

def daily_pv_wide():
    """(dates, permnos, P, V): |DlyPrc| and DlyVol aligned with daily_wide(); None until the D12 files are converted."""
    def f():
        d = pd.read_parquet(PROCESSED / 'crsp_daily.parquet')
        if not {'prc', 'vol'} <= set(d.columns): return None
        dates, cols, _ = daily_wide()
        P = d.pivot(index='date', columns='permno', values='prc').reindex(index=dates, columns=cols).to_numpy(np.float32)
        V = d.pivot(index='date', columns='permno', values='vol').reindex(index=dates, columns=cols).to_numpy(np.float32)
        return dates, cols, P, V
    return _get('pv', f)

def amihud_daily(t, permnos=None, min_obs=120):
    """D12: log Amihud illiquidity over the trading days of the 12 months before formation month t (>= min_obs valid
    days). Indexed by permno; None if daily price/volume are not available (use amihud_monthly as the fallback)."""
    pv = daily_pv_wide()
    if pv is None: return None
    t = pd.Period(t, 'M'); dates, cols, P, V = pv; _, _, R = daily_wide()
    k0, k1 = dates.searchsorted((t - 12).to_timestamp()), dates.searchsorted(t.to_timestamp())
    sel = slice(None) if permnos is None else cols.get_indexer(pd.Index(permnos))
    if permnos is not None: sel = sel[sel >= 0]
    a = amihud_from_arrays(R[k0:k1][:, sel], P[k0:k1][:, sel], V[k0:k1][:, sel], min_obs)
    with np.errstate(divide='ignore'): la = np.log(a)
    return pd.Series(la, index=cols[sel]).dropna()

# ---------------------------------------------------------------- daily matrices
def daily_wide():
    """(dates, permnos, R) with R[d, j] the daily total return of permno j (float32, NaN if missing)."""
    def f():
        d = pd.read_parquet(PROCESSED / 'crsp_daily.parquet', columns=['permno', 'date', 'ret'])
        w = d.pivot(index='date', columns='permno', values='ret').astype(np.float32)
        return w.index, w.columns, w.to_numpy()
    return _get('dw', f)

def factors_daily():
    return _get('ffd', lambda: pd.read_parquet(PROCESSED / 'ff_daily.parquet').set_index('date'))

def daily_window(permnos, end, T, min_obs=None):
    """Excess returns and FF5 + momentum factors over the T trading days ending on `end` (inclusive; the last CRSP
    trading day <= end). Returns (dates [T], permnos kept, X [T x N] excess returns, F [T x 6]); a stock is kept if
    it has >= min_obs returns in the window (default: all T); remaining gaps stay NaN for the caller to handle."""
    dates, cols, R = daily_wide(); ff = factors_daily()
    k = dates.searchsorted(pd.Timestamp(end), side='right')
    if k < T: raise ValueError(f'fewer than {T} trading days before {end}')
    idx = slice(k - T, k); dts = dates[idx]
    pos = cols.get_indexer(pd.Index(permnos)); ok = pos >= 0
    X = R[idx][:, pos[ok]]; perm = np.asarray(permnos)[ok]
    n = np.isfinite(X).sum(0); keep = n >= (T if min_obs is None else min_obs)
    f = ff.reindex(dts)
    if f[FACTORS + ['RF']].isna().any().any(): raise ValueError('factor data missing inside the window')
    X = X[:, keep] - f.RF.to_numpy(np.float32)[:, None]
    return dts, perm[keep], X, f[FACTORS].to_numpy(np.float64)

def residuals(X, F):
    """Time-series OLS of each column of X on [1, F] via tfs_stats.regression.ols_qr (rule 3).
    Returns (B [N x (1 + K)] intercept and betas, E [T x N] residuals). Requires complete columns."""
    from paths import ROOT
    if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
    from tfs_stats.regression import ols_qr
    if not np.isfinite(X).all(): raise ValueError('residuals needs complete columns; filter with daily_window(min_obs=T)')
    Z = np.column_stack([np.ones(len(F)), F])
    B = np.empty((X.shape[1], Z.shape[1])); E = np.empty(X.shape, dtype=np.float64)
    for j in range(X.shape[1]):
        b, e = ols_qr(Z, X[:, j].astype(np.float64)); B[j], E[:, j] = b, e
    return B, E

# ---------------------------------------------------------------- pair panel skeleton (Element C)
def pair_frame(u, t, top=1000, text=True):
    """Static pair covariates for formation month t among the `top` largest firms of universe u (universe_at(t)).
    Pairs i < j over positions in the returned firm frame. Covariates available without regressions:
    same SIC-1..4 (historical CRSP siccd), Anton-Polk percentile-rank distances in size, B/M and momentum, same primary
    exchange, same fiscal-year-end month, log length sum and |difference|, illiquidity rank distance: d_illiq from daily
    Amihud (D12; NaN until DlyPrc/DlyVol are converted) and d_amihud_m from the monthly proxy (fallback).
    With text=True: s_dense, s_bow (BoW nouns, null-corrected, D11) and s_bow_raw (robustness) from networks.build.
    Still to add once tfs_stats exists: outcome z_ij (Fisher-z residual correlation in month t), z_lag (prior 12
    months), |d beta_k|."""
    t = pd.Period(t, 'M')
    f = u.nlargest(top, 'me').reset_index(drop=True)
    f['bm'] = book_to_market(t).reindex(f.permno.to_numpy()).to_numpy()
    f['mom'] = momentum(t).reindex(f.permno.to_numpy()).to_numpy()
    f['amihud_m'] = amihud_monthly(t).reindex(f.permno.to_numpy()).to_numpy()
    ad = amihud_daily(t, f.permno.to_numpy())
    f['illiq'] = np.nan if ad is None else ad.reindex(f.permno.to_numpy()).to_numpy()   # log daily Amihud
    n = len(f); i, j = np.triu_indices(n, 1)
    P = pd.DataFrame({'i': i.astype(np.int32), 'j': j.astype(np.int32)})
    sic = f.sic.to_numpy(dtype=float)
    for l, div in ((1, 1000), (2, 100), (3, 10), (4, 1)):
        c = np.floor(sic / div); P[f'same_sic{l}'] = ((c[i] == c[j]) & (sic[i] > 0) & (sic[j] > 0)).astype(np.int8)
    for v in ('me', 'bm', 'mom', 'illiq', 'amihud_m'):
        r = f[v].rank(pct=True).to_numpy(); P[f'd_{v}'] = np.abs(r[i] - r[j]).astype(np.float32)   # NaN if either missing
    ex = f.primaryexch.to_numpy(); P['same_exch'] = (ex[i] == ex[j]).astype(np.int8)
    fy = f.fye_month.to_numpy(dtype=float); P['same_fye'] = (fy[i] == fy[j]).astype(np.int8)
    ln = np.log(f.n_words.to_numpy(dtype=float)); P['len_sum'] = (ln[i] + ln[j]).astype(np.float32); P['len_diff'] = np.abs(ln[i] - ln[j]).astype(np.float32)
    if text:
        import networks
        S = networks.build(t, f)
        for k, M in S.items(): P[f's_{k}'] = M[i, j]
    return f, P

if __name__ == '__main__':
    import time
    t0 = time.time(); months = formation_months()
    print('formation months', months[0], '-', months[-1], len(months))
    for t in (pd.Period('2014-07', 'M'), pd.Period('2020-01', 'M'), pd.Period('2025-07', 'M')):
        u = universe_at(t); f, P = pair_frame(u, t)
        dts, perm, X, F = daily_window(f.permno, t.to_timestamp() - pd.Timedelta(days=1), 252)
        print(f'{t}: universe {len(u)} firms with text; top-1000 pairs {len(P):,}; B/M coverage {f.bm.notna().mean():.1%}, '
              f'momentum {f.mom.notna().mean():.1%}, daily Amihud {f.illiq.notna().mean():.1%}, monthly proxy {f.amihud_m.notna().mean():.1%}; '
              f'corr(s_dense, s_bow) {P.s_dense.corr(P.s_bow):.2f}; 252-day window {dts[0].date()}..{dts[-1].date()}: {X.shape[1]} of '
              f'{len(f)} complete; share same SIC-3 {P.same_sic3.mean():.2%}')
    try:
        residuals(X[:, :5], F)
    except NotImplementedError:
        print('residuals -> tfs_stats.regression.ols_qr not implemented yet (expected; Abhi writes it)')
    print(f'{time.time() - t0:.0f}s')
