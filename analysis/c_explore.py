"""Element C exploratory specs (each through src/runner.py, counted for BH). Same months (Jul 2012 - Mar 2026), firms
(top 1,000), outcome and controls as the confirmatory H1 run (analysis/c_h1.py and src/c_panel.py, both unchanged);
each spec changes one ingredient:
  bow_null              C_x_bow_null              s~ from the BoW null-corrected similarity (D11) instead of dense
  missing_bm_indicator  C_x_missing_bm_indicator  pairs with a missing B/M kept: d_bm set to the month's median d_bm
                                                  over pairs that have it, plus a 0/1 regressor bm_missing (PREREG D14)
  pc5 / pc10            C_x_pc5 / C_x_pc10        residuals on FF6 + 5 / 10 statistical factors (SPEC §7.7), built by
                                                  build_pc(k) below; the regression is c_h1.month_moments unchanged
Statistic: b-bar on s~ with NW(4) t (x T/(T-1)), one-sided p; EWC(12) beside it. Writes analysis/output/c_explore/.

Statistical-factor residuals, build_pc(k) (data/processed/ff6pc{k}_resid_daily.npy and ff6pc{k}_betas.parquet,
gitignored). For each month m, on the 252 trading days before m (the same window and >= 200-return rule as the FF6
residuals in src/c_panel.py):
  1. FF6 window regression of every live stock (formation.residuals): betas B6 and in-window residuals e.
  2. Stocks with a complete window: standardise e (window mean and SD), take the first k principal components
     (tfs_stats.rmt.pca_factors): loadings V [N x k] and window factor series f_win = Z V [252 x k].
  3. Month m's factor returns: f_m = Z_m V, where Z_m is month m's FF6 residuals (window betas B6, so out of sample)
     standardised with the window mean and SD; a stock missing on a day contributes 0 that day.
  4. Every live stock: regress window excess returns on [1, FF6, f_win] (formation.residuals); month residual =
     x_m - [1, F_m, f_m] B'. As with FF6, month m's own returns never enter its betas or the loadings.
f_win is a linear combination of FF6 residuals, so it is orthogonal to [1, FF6] in the window and the FF6 betas of
complete-window stocks are unchanged (Frisch-Waugh); |dbeta| uses the step-4 FF6 betas. The PCs are built from the
same stocks whose residual correlations form the outcome; with ~3,000-4,000 stocks per window a single firm's weight in
a component is small, so this is a negligible mechanical effect, noted rather than corrected."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import formation as F, c_panel as C, c_h1 as H
from paths import PROCESSED
from tfs_stats.regression import fm_from_moments, ewc, nw_lags_rule, ewc_nu_rule, one_sided_p
from tfs_stats.rmt import pca_factors

OUT = ROOT / 'analysis' / 'output' / 'c_explore'

def month_moments(t, s_col='s_dense', bm_indicator=False):
    """c_h1.month_moments with the similarity column and the missing-B/M rule as arguments (defaults reproduce it)."""
    f, P = C.c_month(t); xc = list(H.X_COLS)
    D = P[['z', s_col] + [c for c in xc if c != 's_tilde']].astype(np.float64)
    if bm_indicator:
        miss = D.d_bm.isna(); D['bm_missing'] = miss.astype(np.float64)
        D.loc[miss, 'd_bm'] = D.d_bm[~miss].median(); xc.append('bm_missing')
    D = D[np.isfinite(D.to_numpy()).all(1)]
    s = D[s_col]; D['s_tilde'] = (s - s.mean()) / s.std()
    X = np.column_stack([np.ones(len(D)), D[xc].to_numpy()]); y = D.z.to_numpy()
    return X.T @ X, X.T @ y, len(D), len(P)

def _fm(name, moments, extra=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    months = pd.period_range(H.FIRST, H.LAST, freq='M'); XtX, Xty, n, npairs = [], [], [], []
    for t in months:
        a, b, k, m = moments(t); XtX.append(a); Xty.append(b); n.append(k); npairs.append(m)
        if t.month == 1: print(name, t, k, f'{time.time() - t0:.0f}s', flush=True)
    T = len(months); L = nw_lags_rule(T); nu = ewc_nu_rule(T)
    r = fm_from_moments(np.stack(XtX), np.stack(Xty), np.array(n), nw_lags=L)
    b = r['lambdas'][:, 1]; ew = ewc(b, nu)
    res = {'b_bar': float(r['coef'][1]), 'se_nw': float(r['se'][1]), 't_nw': float(r['tstat'][1]), 'nw_lags': L,
           'p_one_sided': float(one_sided_p(r['tstat'][1])), 't_ewc': float(ew['tstat']), 'ewc_nu': nu,
           'months': int(r['T']), 'months_skipped': int(r['n_skipped']), 'median_pairs_used': int(np.median(n)),
           'share_pairs_used': float(np.sum(n) / np.sum(npairs)), 'max_cond_XtX': float(np.max(r['cond']))}
    if np.stack(XtX).shape[1] > len(H.X_COLS) + 1: res['b_bar_last_regressor'] = float(r['coef'][-1]); res['t_last_regressor'] = float(r['tstat'][-1])
    res.update(extra or {}); res['seconds'] = round(time.time() - t0)
    (OUT / f'{name}.json').write_text(json.dumps(res, indent=1)); print(name, res)
    return res

def bow_null(spec=None): return _fm('bow_null', lambda t: month_moments(t, s_col='s_bow'))
def missing_bm_indicator(spec=None): return _fm('missing_bm_indicator', lambda t: month_moments(t, bm_indicator=True))

def _pc_paths(k): return PROCESSED / f'ff6pc{k}_resid_daily.npy', PROCESSED / f'ff6pc{k}_betas.parquet'

def build_pc(k, first='2011-01', last='2026-03'):
    """Residuals on FF6 + k statistical factors (module docstring). Returns the mean share of window variance of the
    FF6 residuals that the k components explain."""
    res_path, bet_path = _pc_paths(k); t0 = time.time()
    dates, cols, R = F.daily_wide(); ff = F.factors_daily().reindex(dates)
    _, d0, c0, _ = C._load()                                    # the FF6 files' index must match daily_wide's
    if not (d0.equals(pd.DatetimeIndex(dates)) and c0.equals(pd.Index(cols))): raise ValueError('daily index changed since the FF6 build')
    X = R.astype(np.float64) - ff.RF.to_numpy()[:, None]; Fm = ff[F.FACTORS].to_numpy(np.float64)
    E = np.full(R.shape, np.nan, dtype=np.float32); rows, shares = [], []; T = C.T_BETA
    for m in pd.period_range(first, last, freq='M'):
        k0 = dates.searchsorted(m.to_timestamp()); k1 = dates.searchsorted((m + 1).to_timestamp())
        if k0 < T or k1 <= k0: continue
        Xw, Fw = X[k0 - T:k0], Fm[k0 - T:k0]; live = np.flatnonzero(np.isfinite(Xw).sum(0) >= C.MIN_BETA_OBS)
        B6, e, _ = F.residuals(Xw[:, live], Fw, min_obs=C.MIN_BETA_OBS)
        mu, sd = e.mean(0), e.std(0); full = np.isfinite(e).all(0) & (sd > 0)
        V, f_win, sh = pca_factors((e[:, full] - mu[full]) / sd[full], k); shares.append(float(sh.sum()))
        Z6 = np.column_stack([np.ones(k1 - k0), Fm[k0:k1]]); src = live[full]
        Zm = (X[k0:k1][:, src] - Z6 @ B6[full].T - mu[full]) / sd[full]
        f_m = np.nan_to_num(Zm) @ V
        B, _, nobs = F.residuals(Xw[:, live], np.column_stack([Fw, f_win]), min_obs=C.MIN_BETA_OBS)
        good = np.isfinite(B[:, 0]); idx = live[good]; B = B[good]
        E[k0:k1, idx] = (X[k0:k1][:, idx] - np.column_stack([Z6, f_m]) @ B.T).astype(np.float32)
        rows.append(pd.DataFrame({'permno': cols[idx], 'ym': m, 'alpha': B[:, 0], **{f'b_{f}': B[:, i + 1] for i, f in enumerate(F.FACTORS)},
                                  'nobs': nobs[good]}))
        if m.month == 1: print(f'pc{k}', m, len(idx), f'{time.time() - t0:.0f}s', flush=True)
    np.save(res_path, E); pd.concat(rows).to_parquet(bet_path)
    return float(np.mean(shares))

def _pc(k):
    res_path, bet_path = _pc_paths(k); share = build_pc(k)
    old = C.RES, C.BET; C.RES, C.BET = res_path, bet_path; C._cache.clear()
    try: return _fm(f'pc{k}', H.month_moments, {'k': k, 'mean_window_var_share_of_pcs': share})
    finally: C.RES, C.BET = old; C._cache.clear()

def pc5(spec=None): return _pc(5)
def pc10(spec=None): return _pc(10)
