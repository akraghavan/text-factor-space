"""Element C panel (SPEC §7; PREREG draft, Element C): the monthly pair outcome, the history baseline and the beta
controls, on top of formation.pair_frame (covariates and text similarities).

Step 1, `build_residuals()` (run once; `python src/c_panel.py --build`): for every month m from 2011-01 to 2026-03 and
every CRSP permno, regress daily excess returns on FF5 + momentum over the 252 trading days that end the day before
month m starts (tfs_stats.regression.ols_qr via formation.residuals: one QR for all complete stocks); a stock needs
>= 200 of the 252 returns (PREREG [PROPOSED]). The betas are then applied to the days of month m:
  e_{i,d} = x_{i,d} - alpha_i - beta_i' f_d      (out of sample: month m's own returns never enter its betas)
so every month's residuals come from betas that predate it. Stored in data/processed/ (gitignored):
ff6_resid_daily.npy (dates x permnos, float32), ff6_resid_index.parquet (dates, permnos), ff6_betas.parquet
(permno, ym, alpha, 6 betas, nobs). The intercept does not affect correlations; it is kept so residuals average ~0.

Step 2, `c_month(t)`: for formation month t, the top 1,000 universe firms (pair_frame) and for each pair i < j:
  z      = atanh(rho_ij,t), rho = correlation of the two firms' daily residuals within month t on common days
           (>= 15 required, SPEC §7); rho clipped to +/-0.999999 before atanh
  z_lag  = atanh of the same correlation pooled over the residual days of months t-12..t-1 (>= 126 common days,
           i.e. half a year; design choice recorded here and in STATUS)
  db_<k> = |beta_ik - beta_jk| for each factor k, betas from month t's estimation window (the same ones that produced
           the month-t residuals)
Pearson correlation via pandas DataFrame.corr(min_periods=...) (pairwise-complete), a descriptive statistic, not an
estimator. No association between z and text similarity is computed here (PREREG: b-bar is primary, frozen first)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import PROCESSED
import numpy as np, pandas as pd
import formation as F

T_BETA, MIN_BETA_OBS, MIN_MONTH_DAYS, MIN_LAG_DAYS = 252, 200, 15, 126
RES = PROCESSED / 'ff6_resid_daily.npy'; IDX = PROCESSED / 'ff6_resid_index.parquet'; BET = PROCESSED / 'ff6_betas.parquet'
_cache = {}

def build_residuals(first='2011-01', last='2026-03'):
    dates, cols, R = F.daily_wide(); ff = F.factors_daily().reindex(dates)
    if ff[F.FACTORS + ['RF']].isna().any().any(): raise ValueError('factor data missing on a CRSP trading day')
    X = R.astype(np.float64) - ff.RF.to_numpy()[:, None]; Fm = ff[F.FACTORS].to_numpy(np.float64)
    E = np.full(R.shape, np.nan, dtype=np.float32); rows = []
    for m in pd.period_range(first, last, freq='M'):
        k0 = dates.searchsorted(m.to_timestamp()); k1 = dates.searchsorted((m + 1).to_timestamp())
        if k0 < T_BETA or k1 <= k0: continue
        Xw = X[k0 - T_BETA:k0]; live = np.isfinite(Xw).sum(0) >= MIN_BETA_OBS       # skip permnos not trading then
        B, _, nobs = F.residuals(Xw[:, live], Fm[k0 - T_BETA:k0], min_obs=MIN_BETA_OBS)
        good = np.isfinite(B[:, 0]); idx = np.flatnonzero(live)[good]; B = B[good]
        Zm = np.column_stack([np.ones(k1 - k0), Fm[k0:k1]])
        E[k0:k1, idx] = (X[k0:k1][:, idx] - Zm @ B.T).astype(np.float32)
        rows.append(pd.DataFrame({'permno': cols[idx], 'ym': m, 'alpha': B[:, 0], **{f'b_{f}': B[:, i + 1] for i, f in enumerate(F.FACTORS)},
                                  'nobs': nobs[good]}))
        print(m, len(idx), flush=True) if m.month == 1 else None
    np.save(RES, E)
    pd.DataFrame({'date': dates}).assign(kind='date').to_parquet(IDX)
    pd.DataFrame({'permno': cols}).to_parquet(PROCESSED / 'ff6_resid_permnos.parquet')
    pd.concat(rows).to_parquet(BET)

def _load():
    if 'E' not in _cache:
        _cache['E'] = np.load(RES, mmap_mode='r')
        _cache['dates'] = pd.DatetimeIndex(pd.read_parquet(IDX).date)
        _cache['cols'] = pd.Index(pd.read_parquet(PROCESSED / 'ff6_resid_permnos.parquet').permno)
        _cache['B'] = pd.read_parquet(BET)
    return _cache['E'], _cache['dates'], _cache['cols'], _cache['B']

def _resid(permnos, first, last):
    """Residual block (days x firms) for months first..last (inclusive), columns in the order of permnos (NaN if absent)."""
    E, dates, cols, _ = _load()
    k0 = dates.searchsorted(pd.Period(first, 'M').to_timestamp()); k1 = dates.searchsorted((pd.Period(last, 'M') + 1).to_timestamp())
    pos = cols.get_indexer(pd.Index(permnos)); out = np.full((k1 - k0, len(pos)), np.nan, dtype=np.float32)
    out[:, pos >= 0] = E[k0:k1][:, pos[pos >= 0]]
    return out

def _fisher_z(block, min_days):
    r = pd.DataFrame(block).corr(min_periods=min_days).to_numpy()
    return np.arctanh(np.clip(r, -0.999999, 0.999999))

def c_month(t, top=1000, text=True):
    """Pair panel for formation month t: pair_frame covariates and similarities plus z, z_lag, db_<factor>.
    Returns (firms, P)."""
    t = pd.Period(t, 'M')
    f, P = F.pair_frame(F.universe_at(t), t, top=top, text=text)
    i, j = P.i.to_numpy(), P.j.to_numpy(); perm = f.permno.to_numpy()
    Z = _fisher_z(_resid(perm, t, t), MIN_MONTH_DAYS); P['z'] = Z[i, j].astype(np.float32)
    ZL = _fisher_z(_resid(perm, t - 12, t - 1), MIN_LAG_DAYS); P['z_lag'] = ZL[i, j].astype(np.float32)
    _, _, _, B = _load(); b = B[B.ym == t].set_index('permno').reindex(perm)
    for fac in F.FACTORS:
        v = b[f'b_{fac}'].to_numpy(); P[f'db_{fac}'] = np.abs(v[i] - v[j]).astype(np.float32)
    f['has_beta'] = b.alpha.notna().to_numpy()
    return f, P

if __name__ == '__main__':
    if '--build' in sys.argv: build_residuals()
