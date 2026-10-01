"""Regression and inference: the project's estimator layer (D13, 28 Sep 2026). Built on numpy / SciPy / statsmodels;
custom code only where no library does the job (EWC, Fama-MacBeth from sufficient statistics). Every function names the
library call that does the work and every convention it applies, and points to its card in docs/STATS_GUIDE.md.
Tests: tests/test_regression.py (statsmodels, linearmodels, simulations with known answers)."""
import numpy as np
import scipy.linalg as sla
import statsmodels.api as sm
from scipy import stats

__all__ = ['ols_qr', 'vcov', 'fama_macbeth', 'fm_inference', 'fm_from_moments', 'ewc', 'nw_lags_rule', 'ewc_nu_rule', 'one_sided_p']

def nw_lags_rule(T: int) -> int:
    """Newey-West lag rule used throughout the project: L = floor(4 (T/100)^(2/9)) (Newey & West 1994).
    L = 3 at T = 91 (E's test period), 4 at T = 165 (C). Card: docs/STATS_GUIDE.md#fn-fama_macbeth"""
    return int(np.floor(4 * (T / 100) ** (2 / 9)))

def ewc_nu_rule(T: int) -> int:
    """EWC degrees of freedom: nu = floor(0.4 T^(2/3)) (Lazarus, Lewis, Stock & Watson 2018). nu = 8 at T = 91,
    12 at T = 165. Card: docs/STATS_GUIDE.md#fn-ewc"""
    return int(np.floor(0.4 * T ** (2 / 3)))

def ols_qr(X: np.ndarray, y: np.ndarray, rcond: float = 1e-10):
    """OLS via thin QR: X = QR, beta = R^{-1} Q'y, with R^{-1} applied by back-substitution.
    Library calls: np.linalg.qr(X, mode='reduced') and scipy.linalg.solve_triangular(R, Q'y) (upper triangular).
    y may be (n,) or (n, m): one factorisation of X then serves all m response columns (all stocks in a window share
    the factor matrix), which is the speed-up formation.residuals relies on.
    Returns (beta [k] or [k, m], resid [n] or [n, m]); resid = y - X beta.
    Rank check: raises np.linalg.LinAlgError if min |R_ii| <= rcond * max |R_ii| (collinear or empty columns).
    Why QR and not (X'X)^{-1} X'y: cond(X'X) = cond(X)^2, so the normal equations lose twice the digits.
    Card: docs/STATS_GUIDE.md#fn-ols_qr"""
    X = np.asarray(X, dtype=np.float64); y = np.asarray(y, dtype=np.float64)
    if X.ndim != 2: raise ValueError('X must be 2-D (n x k)')
    if X.shape[0] < X.shape[1]: raise np.linalg.LinAlgError(f'fewer rows ({X.shape[0]}) than columns ({X.shape[1]})')
    Q, R = np.linalg.qr(X, mode='reduced')
    d = np.abs(np.diag(R))
    if d.min() <= rcond * d.max(): raise np.linalg.LinAlgError(f'X is rank deficient (min |R_ii| / max |R_ii| = {d.min() / d.max():.2e})')
    beta = sla.solve_triangular(R, Q.T @ y, lower=False)
    return beta, y - X @ beta

def vcov(X: np.ndarray, resid: np.ndarray, kind: str = "classical", groups=None, lags: int | None = None):
    """Covariance matrix of the OLS beta_hat that produced `resid`, as a sandwich (X'X)^{-1} meat (X'X)^{-1}.
    Library call: statsmodels OLS(resid, X).fit(cov_type=...).cov_params(). Regressing the OLS residuals on X
    returns beta = 0 and the same residuals (X'e = 0), so statsmodels' sandwich is evaluated at exactly these e.
      kind='classical' -> cov_type='nonrobust': s^2 (X'X)^{-1}, s^2 = e'e/(n-k)
      kind='HC1'       -> cov_type='HC1': n/(n-k) (X'X)^{-1} (sum e_i^2 x_i x_i') (X'X)^{-1}
      kind='cluster'   -> cov_type='cluster' (use_correction=True): G/(G-1) (n-1)/(n-k) (X'X)^{-1} (sum_g u_g u_g') (X'X)^{-1},
                          u_g = sum_{i in g} x_i e_i; group labels of any type are mapped to integer codes first
      kind='NW'        -> cov_type='HAC', Bartlett kernel, maxlags=lags, use_correction=False (no small-sample factor):
                          S = G_0 + sum_{l=1..L} (1 - l/(L+1)) (G_l + G_l'),  G_l = sum_t e_t e_{t-l} x_t x_{t-l}'
    Rows must be in time order for 'NW'. Card: docs/STATS_GUIDE.md#fn-vcov"""
    X = np.asarray(X, dtype=np.float64); e = np.asarray(resid, dtype=np.float64)
    m = sm.OLS(e, X)
    if kind == 'classical': r = m.fit(cov_type='nonrobust')
    elif kind == 'HC1': r = m.fit(cov_type='HC1')
    elif kind == 'cluster':
        if groups is None: raise ValueError("kind='cluster' needs groups")
        codes = np.unique(np.asarray(groups), return_inverse=True)[1]
        r = m.fit(cov_type='cluster', cov_kwds={'groups': codes})
    elif kind == 'NW':
        if lags is None: raise ValueError("kind='NW' needs lags")
        r = m.fit(cov_type='HAC', cov_kwds={'maxlags': int(lags), 'use_correction': False})
    else: raise ValueError(f'unknown kind {kind!r}')
    return np.asarray(r.cov_params())

def fm_inference(lambdas: np.ndarray, nw_lags: int = 0):
    """Inference on a Fama-MacBeth slope series (the second FM step), for any number of coefficients.
    coef = mean over periods; Var(mean) = NW long-run variance / T, computed as vcov(ones, lambda - mean, 'NW', lags)
    (a mean is OLS on a constant) and multiplied by T/(T-1).
    Convention (T/(T-1) at every lag): nw_lags=0 then gives exactly std(ddof=1)/sqrt(T), the textbook FM standard error;
    it is Stata's `newey` factor n/(n-k) with k = 1 and matches linearmodels FamaMacBeth(cov_type='kernel', kernel=
    'bartlett', bandwidth=L) at every L (checked in tests). vcov's own 'NW' stays uncorrected.
    Returns dict(coef, se, tstat, T). t-statistics use normal critical values unless stated (C: NW(4); E: NW(3)).
    Card: docs/STATS_GUIDE.md#fn-fama_macbeth"""
    lam = np.asarray(lambdas, dtype=np.float64)
    if lam.ndim == 1: lam = lam[:, None]
    lam = lam[np.isfinite(lam).all(1)]
    T = lam.shape[0]
    if T < 2: raise ValueError('need at least 2 periods')
    coef = lam.mean(0); ones = np.ones((T, 1))
    var = np.array([vcov(ones, lam[:, j] - coef[j], 'NW', lags=nw_lags)[0, 0] for j in range(lam.shape[1])]) * T / (T - 1)
    se = np.sqrt(var)
    return {'coef': coef, 'se': se, 'tstat': coef / se, 'T': T}

def fama_macbeth(y: np.ndarray, X: np.ndarray, t: np.ndarray, nw_lags: int = 0, min_obs: int | None = None):
    """Fama-MacBeth (1973): one cross-sectional OLS of y on [1, X] per period t (ols_qr), then fm_inference on the
    slope series with Newey-West(nw_lags) x T/(T-1). The intercept is added here; callers must not include one.
    Unbalanced panels are fine; period labels can be anything. A period with fewer than max(min_obs, k+1) rows or a
    rank-deficient design is skipped and counted in n_skipped.
    Returns dict(coef [k+1], se [k+1], tstat [k+1], lambdas [T x (k+1)], periods, n_skipped, T).
    Card: docs/STATS_GUIDE.md#fn-fama_macbeth"""
    y = np.asarray(y, dtype=np.float64); X = np.asarray(X, dtype=np.float64); t = np.asarray(t)
    if X.ndim == 1: X = X[:, None]
    k = X.shape[1] + 1; need = max(k, min_obs or 0)
    order = np.argsort(t, kind='stable'); y, X, t = y[order], X[order], t[order]
    periods, start = np.unique(t, return_index=True); stops = np.r_[start[1:], len(t)]
    lam, kept, skipped = [], [], 0
    for p, a, b in zip(periods, start, stops):
        if b - a < need: skipped += 1; continue
        try: beta, _ = ols_qr(np.column_stack([np.ones(b - a), X[a:b]]), y[a:b])
        except np.linalg.LinAlgError: skipped += 1; continue
        lam.append(beta); kept.append(p)
    lam = np.array(lam)
    out = fm_inference(lam, nw_lags)
    out.update({'lambdas': lam, 'periods': np.array(kept), 'n_skipped': skipped})
    return out

def fm_from_moments(XtX: np.ndarray, Xty: np.ndarray, n: np.ndarray, nw_lags: int = 0, rcond: float = 1e-10):
    """Fama-MacBeth from per-period sufficient statistics, for panels too large to stack (C: 499,500 pairs x 165
    months, ~10 GB). Inputs per period t: XtX[t] = X_t'X_t (p x p, the design already includes the intercept column),
    Xty[t] = X_t'y_t (p), n[t] = rows. Per-period slopes solve X'X b = X'y by Cholesky (scipy.linalg.cho_factor /
    cho_solve); periods with n < p or cond(X'X) > 1/rcond are skipped. Then fm_inference(nw_lags) as above.
    Numerics: this is the normal-equations route, so cond(X'X) = cond(X)^2 matters; the C design is standardised within
    month (similarity, ranks in [0, 1], dummies) and the condition number of every month is returned for checking.
    Where one month fits in memory, fama_macbeth / ols_qr (QR) is preferred. Card: docs/STATS_GUIDE.md#fn-fm_moments"""
    XtX = np.asarray(XtX, dtype=np.float64); Xty = np.asarray(Xty, dtype=np.float64); n = np.asarray(n)
    p = XtX.shape[1]; lam, kept, cond = [], [], []
    for t in range(len(n)):
        c = np.linalg.cond(XtX[t]) if n[t] >= p else np.inf
        cond.append(c)
        if n[t] < p or not np.isfinite(c) or c > 1 / rcond: continue
        lam.append(sla.cho_solve(sla.cho_factor(XtX[t]), Xty[t])); kept.append(t)
    lam = np.array(lam)
    out = fm_inference(lam, nw_lags)
    out.update({'lambdas': lam, 'periods': np.array(kept), 'n_skipped': len(n) - len(kept), 'cond': np.array(cond)})
    return out

def ewc(u: np.ndarray, nu: int | None = None):
    """Equal-weighted cosine (EWC) long-run variance and t-test for the mean of a series (Lazarus, Lewis, Stock &
    Watson 2018; Mueller 2007). No library implements it, so it is written here and checked by simulation.
      Lambda_j = sqrt(2/T) sum_{t=1..T} cos(pi j (t - 1/2) / T) (u_t - u_bar),   j = 1..nu
      Omega_hat = (1/nu) sum_j Lambda_j^2            (long-run variance of u)
      se(u_bar) = sqrt(Omega_hat / T),  t = u_bar / se,  compared with Student t_nu (exact under Gaussian iid-like
      cosine projections, which is why EWC keeps size where short-lag NW over-rejects).
    Default nu = floor(0.4 T^(2/3)) (ewc_nu_rule). u may be (T,) or (T, p) (each column separately, e.g. an FM slope
    series). Returns dict(mean, se, tstat, df=nu, pvalue two-sided from t_nu). Card: docs/STATS_GUIDE.md#fn-ewc"""
    u = np.asarray(u, dtype=np.float64)
    one = u.ndim == 1
    if one: u = u[:, None]
    T = u.shape[0]; nu = ewc_nu_rule(T) if nu is None else int(nu)
    if not 1 <= nu < T: raise ValueError(f'nu must be in [1, T), got {nu} with T = {T}')
    ub = u.mean(0); tt = np.arange(1, T + 1)
    W = np.sqrt(2 / T) * np.cos(np.pi * np.outer(np.arange(1, nu + 1), tt - 0.5) / T)    # nu x T cosine weights
    Lam = W @ (u - ub)                                                                      # nu x p
    omega = (Lam ** 2).mean(0); se = np.sqrt(omega / T); ts = ub / se
    pv = 2 * stats.t.sf(np.abs(ts), df=nu)
    f = (lambda a: a[0]) if one else (lambda a: a)
    return {'mean': f(ub), 'se': f(se), 'tstat': f(ts), 'df': nu, 'pvalue': f(pv), 'omega': f(omega)}

def one_sided_p(t, df=None, direction: str = '+'):
    """One-sided p-value of a t-statistic for H: effect > 0 (direction '+') or < 0 ('-'). Normal reference when df is
    None (Newey-West Fama-MacBeth t-statistics, as registered), Student t_df otherwise (EWC: df = nu). scipy.stats.
    Card: docs/STATS_GUIDE.md#fn-fama_macbeth"""
    t = np.asarray(t, dtype=float); x = t if direction == '+' else -t
    return stats.norm.sf(x) if df is None else stats.t.sf(x, df)
