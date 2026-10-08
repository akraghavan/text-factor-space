"""Element C exploratory specs, the remaining pre-listed robustness checks of H1 plus one post-freeze addition
(SPEC D22, D24; each through src/runner.py, counted for BH). Same months (Jul 2012 - Mar 2026), firms (top 1,000),
outcome and controls as H1 (analysis/c_h1.py, src/c_panel.py, unchanged) unless stated; each spec changes one thing.
  bow_raw         C_x_bow_raw         s~ from the raw (uncorrected) BoW similarity
  binary_network  C_x_binary_network  s~ replaced by 1[pair is a dense peer link]: dense similarity computed over the whole
                                      universe at t (networks.dense centres on the set it is given, so the universe set
                                      is used, as in A and E), cut at its (1 - pi_t) quantile over all universe pairs
                                      (pi_t = SIC-3 pair density); unstandardised, so b-bar is the z-gap of linked pairs
  windows_12m     C_x_12m_windows     13 non-overlapping July-June windows 2012/13 .. 2024/25: top 1,000 at the July
                                      formation, z = Fisher z of the residual correlation pooled over the window's 12
                                      months (>= 126 common days), z_lag and controls from the July formation; FM over the
                                      13 windows, NW(2), one-sided p from t with 12 df
  pre_fy2020      C_x_pre_fy2020      formation months whose top-1,000 vintages were all filed before 2020-11-09 (the
  post_fy2020     C_x_post_fy2020     effective date of the Item 101 amendments) / all on or after it; mixed months
                                      dropped; NW lags by the rule for each T; post also reports post - pre
  dimson          C_x_dimson          residuals on FF6 at lags 0 and 1 (13 regressors) in both the 252-day window and
                                      the month (build_dimson -> data/processed/ff6dim_*, gitignored); |dbeta| from the
                                      lag-0 betas; z and z_lag both use these residuals
  sich            C_x_sich            same-SIC-1..4 dummies from Compustat historical sich (src/industry.py, point in
                                      time, fallback CRSP siccd); share of firms on sich reported
  post_sep2023    C_x_post_sep2023    formation months Oct 2023 - Mar 2026 (after bge-small-en-v1.5's release; added
                                      after the freeze): the dense encoder cannot have seen these filings' returns
Statistic: b-bar on s~ (or the link dummy) with NW t (x T/(T-1)), one-sided p; EWC beside it. Every entry saves its
monthly b_t series (output/c_explore2/series/<spec>.json) for Romano-Wolf (D25)."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import formation as F, networks as N, c_panel as C, c_h1 as H, industry, series_out
from paths import PROCESSED
from tfs_stats.regression import fm_from_moments, ewc, nw_lags_rule, ewc_nu_rule, one_sided_p

OUT = ROOT / 'analysis' / 'output' / 'c_explore2'
CTRL = [c for c in H.X_COLS if c != 's_tilde']
MONTHS = pd.period_range(H.FIRST, H.LAST, freq='M')
ITEM101 = pd.Timestamp('2020-11-09')
DIM_RES, DIM_BET = PROCESSED / 'ff6dim_resid_daily.npy', PROCESSED / 'ff6dim_betas.parquet'

def _moments(t, s_col='s_dense', s_fn=None, hook=None):
    """c_h1.month_moments with the similarity column, its transform and a hook on (f, P) as arguments (defaults
    reproduce it: s~ = s_dense standardised over the month's complete-case pairs)."""
    f, P = C.c_month(t)
    if hook is not None: hook(t, f, P)
    D = P[['z', s_col] + CTRL].astype(np.float64); D = D[np.isfinite(D.to_numpy()).all(1)]
    s = D[s_col]; D['s_tilde'] = (s - s.mean()) / s.std() if s_fn is None else s_fn(s)
    X = np.column_stack([np.ones(len(D)), D[H.X_COLS].to_numpy()]); y = D.z.to_numpy()
    return X.T @ X, X.T @ y, len(D), len(P)

def _stats(labels, XtX, Xty, n, npairs, df=None):
    T = len(labels); L = nw_lags_rule(T); nu = ewc_nu_rule(T)
    r = fm_from_moments(np.stack(XtX), np.stack(Xty), np.array(n), nw_lags=L); b = r['lambdas'][:, 1]; ew = ewc(b, nu)
    res = {'b_bar': float(r['coef'][1]), 'se_nw': float(r['se'][1]), 't_nw': float(r['tstat'][1]), 'nw_lags': L,
           'p_one_sided': float(one_sided_p(r['tstat'][1], df=df)), 't_ewc': float(ew['tstat']), 'ewc_nu': nu,
           'months': int(r['T']), 'first': str(labels[0]), 'last': str(labels[-1]), 'months_skipped': int(r['n_skipped']),
           'median_pairs_used': int(np.median(n)), 'share_pairs_used': float(np.sum(n) / np.sum(npairs)), 'max_cond_XtX': float(np.max(r['cond']))}
    return res, r, b

def _collect(name, labels, moments):
    t0 = time.time(); XtX, Xty, n, npairs = [], [], [], []
    for t in labels:
        a, b, k, m = moments(t); XtX.append(a); Xty.append(b); n.append(k); npairs.append(m)
        if pd.Period(t, 'M').month == 1: print(name, t, k, f'{time.time() - t0:.0f}s', flush=True)
    return XtX, Xty, n, npairs

def _fm(name, labels, moments, spec=None, extra=None, df=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    res, r, b = _stats(labels, *_collect(name, labels, moments), df)
    series_out.save(OUT, spec, name, pd.PeriodIndex(labels)[r['periods']].astype(str), b)
    if extra: res.update(extra() if callable(extra) else extra)
    res['seconds'] = round(time.time() - t0)
    (OUT / f'{name}.json').write_text(json.dumps(res, indent=1)); print(name, res)
    return res

def bow_raw(spec=None): return _fm('bow_raw', MONTHS, lambda t: _moments(t, s_col='s_bow_raw'), spec)

def binary_network(spec=None):
    dens = []
    def hook(t, f, P):
        u = F.universe_at(t); G = N.dense(u.accession.to_numpy()); i, j = np.triu_indices(len(u), 1); pi = N.density(u)
        tau = float(np.nanquantile(G[i, j], 1 - pi)); pos = pd.Index(u.accession).get_indexer(f.accession.to_numpy())
        P['s_link'] = (G[pos[P.i.to_numpy()], pos[P.j.to_numpy()]] > tau).astype(np.float64); dens.append((pi, float(P.s_link.mean())))
    return _fm('binary_network', MONTHS, lambda t: _moments(t, s_col='s_link', s_fn=lambda s: s, hook=hook), spec,
               extra=lambda: {'mean_pi': float(np.mean([a for a, _ in dens])), 'mean_link_share_top1000': float(np.mean([b for _, b in dens]))})

def _window_moments(y0):
    t = pd.Period(f'{y0}-07', 'M'); f, P = C.c_month(t)
    Z = C._fisher_z(C._resid(f.permno.to_numpy(), t, t + 11), C.MIN_LAG_DAYS); P['z'] = Z[P.i.to_numpy(), P.j.to_numpy()]
    D = P[['z', 's_dense'] + CTRL].astype(np.float64); D = D[np.isfinite(D.to_numpy()).all(1)]
    D['s_tilde'] = (D.s_dense - D.s_dense.mean()) / D.s_dense.std()
    X = np.column_stack([np.ones(len(D)), D[H.X_COLS].to_numpy()]); y = D.z.to_numpy()
    return X.T @ X, X.T @ y, len(D), len(P)

def windows_12m(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); years = list(range(2012, 2025)); XtX, Xty, n, npairs = [], [], [], []
    for y0 in years:
        a, b, k, m = _window_moments(y0); XtX.append(a); Xty.append(b); n.append(k); npairs.append(m); print('window', y0, k, f'{time.time() - t0:.0f}s', flush=True)
    labels = [pd.Period(f'{y}-07', 'M') for y in years]
    res, r, b = _stats(labels, XtX, Xty, n, npairs, df=len(years) - 1)
    series_out.save(OUT, spec, 'windows_12m', [f'{y}/{(y + 1) % 100:02d}' for y in np.array(years)[r['periods']]], b)
    res.update({'windows': len(years), 'p_df': len(years) - 1, 'seconds': round(time.time() - t0)})
    (OUT / 'windows_12m.json').write_text(json.dumps(res, indent=1)); print('windows_12m', res)
    return res

def _vintage_split():
    pre, post, mixed = [], [], []
    for t in MONTHS:
        fd = pd.to_datetime(F.universe_at(t).nlargest(1000, 'me').filing_date)
        (pre if (fd < ITEM101).all() else post if (fd >= ITEM101).all() else mixed).append(t)
    return pre, post, mixed

def pre_fy2020(spec=None):
    pre, post, mixed = _vintage_split()
    return _fm('pre_fy2020', pre, _moments, spec, extra={'months_mixed_dropped': len(mixed)})

def post_fy2020(spec=None):
    pre, post, mixed = _vintage_split(); t0 = time.time()
    rp, _, _ = _stats(pre, *_collect('pre arm', pre, _moments))                  # the pre arm, recomputed for the difference
    res = _fm('post_fy2020', post, _moments, spec, extra={'months_mixed_dropped': len(mixed)})
    d = res['b_bar'] - rp['b_bar']; se = float(np.hypot(res['se_nw'], rp['se_nw']))
    res.update({'pre_b_bar': rp['b_bar'], 'pre_months': rp['months'], 'post_minus_pre': d, 'se_diff': se, 't_diff': d / se,
                'seconds_total': round(time.time() - t0)})
    (OUT / 'post_fy2020.json').write_text(json.dumps(res, indent=1))
    return res

def build_dimson(first='2011-01', last='2026-03'):
    """Rolling-beta residuals on FF6 at lags 0 and 1 (Dimson 1979), same windows and rules as c_panel.build_residuals."""
    t0 = time.time(); dates, cols, R = F.daily_wide(); ff = F.factors_daily().reindex(dates)
    _, d0, c0, _ = C._load()
    if not (d0.equals(pd.DatetimeIndex(dates)) and c0.equals(pd.Index(cols))): raise ValueError('daily index changed since the FF6 build')
    X = R.astype(np.float64) - ff.RF.to_numpy()[:, None]; Fm = ff[F.FACTORS].to_numpy(np.float64)
    Fd = np.column_stack([Fm, np.vstack([np.full((1, Fm.shape[1]), np.nan), Fm[:-1]])]); T = C.T_BETA
    E = np.full(R.shape, np.nan, dtype=np.float32); rows = []
    for m in pd.period_range(first, last, freq='M'):
        k0 = dates.searchsorted(m.to_timestamp()); k1 = dates.searchsorted((m + 1).to_timestamp())
        if k0 - T < 1 or k1 <= k0: continue                                    # the first window day needs a lagged factor
        Xw = X[k0 - T:k0]; live = np.flatnonzero(np.isfinite(Xw).sum(0) >= C.MIN_BETA_OBS)
        B, _, nobs = F.residuals(Xw[:, live], Fd[k0 - T:k0], min_obs=C.MIN_BETA_OBS)
        good = np.isfinite(B[:, 0]); idx = live[good]; B = B[good]
        E[k0:k1, idx] = (X[k0:k1][:, idx] - np.column_stack([np.ones(k1 - k0), Fd[k0:k1]]) @ B.T).astype(np.float32)
        rows.append(pd.DataFrame({'permno': cols[idx], 'ym': m, 'alpha': B[:, 0], **{f'b_{f}': B[:, i + 1] for i, f in enumerate(F.FACTORS)},
                                  **{f'b_{f}_lag1': B[:, 7 + i] for i, f in enumerate(F.FACTORS)}, 'nobs': nobs[good]}))
    np.save(DIM_RES, E); pd.concat(rows).to_parquet(DIM_BET); print('dimson residuals built', f'{time.time() - t0:.0f}s')

def dimson(spec=None):
    build_dimson(); old = C.RES, C.BET; C.RES, C.BET = DIM_RES, DIM_BET; C._cache.clear()
    try: return _fm('dimson', MONTHS, _moments, spec)
    finally: C.RES, C.BET = old; C._cache.clear()

def sich(spec=None):
    orig = F.universe_at; share = []
    def ua(t, *a, **k): return industry.with_sich(orig(t, *a, **k), t)
    def hook(t, f, P): share.append(float((f.sic_source == 'sich').mean()))
    F.universe_at = ua
    try: return _fm('sich', MONTHS, lambda t: _moments(t, hook=hook), spec, extra=lambda: {'share_top1000_on_sich': float(np.mean(share))})
    finally: F.universe_at = orig

def post_sep2023(spec=None): return _fm('post_sep2023', pd.period_range('2023-10', H.LAST, freq='M'), _moments, spec)
