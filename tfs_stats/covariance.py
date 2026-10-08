"""Covariance and correlation estimators for Element D (SPEC §8; PREREG Element D; decisions D20, D26).
Every estimator returns a correlation matrix R-hat; the horse race combines it with the window's sample variances,
Sigma-hat = D^{1/2} R-hat D^{1/2} (D20(d)), so estimators differ only in correlation structure.
  lw_nonlinear      Ledoit & Wolf (2020, AoS) analytical nonlinear shrinkage (no maintained library; custom, D26)
  nested_target     the text / industry / constant-correlation target T(a, b) = a 11' + b G + (1 - a - b) I
  fit_target_ab     constrained least squares for (a, b) on past correlations
  ss_intensity      Schaefer & Strimmer (2005) eq. 8 shrinkage intensity towards a fixed target
  shrink            delta T + (1 - delta) R
  precondition_nl   text-preconditioned nonlinear shrinkage (Ledoit & Wolf 2017 RFS, eq. 16)
  factor_corr       factor models (FF6 regression or PCA) in correlation form, optionally with a non-diagonal residual
                    correlation
Library calls: numpy.linalg.eigh / svd; tfs_stats.regression.ols_qr for the factor regressions;
tfs_stats.rmt.pca_factors. Tests: tests/test_covariance.py. Cards: docs/STATS_GUIDE.md#fn-lw_nonlinear,
#fn-text_target, #fn-precondition, #fn-factor_corr."""
import numpy as np
from .regression import ols_qr
from .rmt import pca_factors

__all__ = ['lw_nonlinear', 'nested_target', 'fit_target_ab', 'ss_intensity', 'shrink', 'precondition_nl', 'factor_fit',
           'factor_corr', 'to_corr', 'standardise']

def to_corr(S):
    """Rescale a covariance matrix to unit diagonal, symmetrised."""
    S = np.asarray(S, dtype=np.float64); d = np.sqrt(np.diag(S)); R = S / np.outer(d, d); R = (R + R.T) / 2
    np.fill_diagonal(R, 1.0); return R

def standardise(X):
    """Columns demeaned and divided by their sample SD (ddof = 1), so X'X / (n - 1) is the sample correlation."""
    X = np.asarray(X, dtype=np.float64); return (X - X.mean(0)) / X.std(0, ddof=1)

def lw_nonlinear(X, demean: bool = True):
    """Analytical nonlinear shrinkage of the covariance matrix of the n x p data X (Ledoit & Wolf 2020, Annals of
    Statistics, "Analytical nonlinear shrinkage of large-dimensional covariance matrices"; equation numbers of the
    working paper, econwp264). Keeps the sample eigenvectors and replaces each sample eigenvalue by an estimate of the
    oracle u_i' Sigma u_i:
      demean the columns and use n <- n - 1 (the degree of freedom the mean used); S = X'X / n; eigh -> lambda, U;
      the min(p, n) nonzero eigenvalues lambda_j; global bandwidth h = n^{-1/3}, local bandwidths H_j = h lambda_j (4.9);
      x_ij = (lambda_i - lambda_j) / H_j; Epanechnikov kernel density and its Hilbert transform (4.7, 4.8):
        f~_i  = mean_j (3 / (4 sqrt5)) max(1 - x_ij^2 / 5, 0) / H_j
        Hf~_i = mean_j [ -(3 / (10 pi)) x_ij + (3 / (4 sqrt5 pi)) (1 - x_ij^2 / 5) log|(sqrt5 - x_ij) / (sqrt5 + x_ij)| ] / H_j
        (at |x| = sqrt5 the log term has limit 0 and only the first term remains);
      p <= n: d_i = lambda_i / [ (pi c lambda_i f~_i)^2 + (1 - c - pi c lambda_i Hf~_i)^2 ],  c = p / n   (4.3)
      p >  n: the p - n null eigenvalues get d0 = 1 / (pi (p - n)/n Hf~0) with
              Hf~0 = (1/pi) [3/(10 h^2) + 3/(4 sqrt5 h) (1 - 1/(5 h^2)) log((1 + sqrt5 h)/(1 - sqrt5 h))] mean(1/lambda) (C.5, C.8);
              the nonzero ones d_i = lambda_i / (pi^2 lambda_i^2 (f~_i^2 + Hf~_i^2))   (C.4).
    Returns U diag(d) U'. demean=False skips the demeaning and keeps n (data already centred). Needs n >= 12
    (sqrt5 h < 1). The min(p, n) eigenvalues used must be numerically positive (relative to the trace, > 1e-12): when p is
    close to n the smallest is legitimately tiny (D's N = 500, T = 504 has q ~ 0.99), so the guard only catches zeros.
    Checked against the authors' published algorithm as ported in `nonlinshrink` (tests/test_covariance.py).
    Card: docs/STATS_GUIDE.md#fn-lw_nonlinear"""
    X = np.asarray(X, dtype=np.float64); n, p = X.shape
    if demean: X = X - X.mean(0); n = n - 1
    if n < 12: raise ValueError('lw_nonlinear needs an effective sample size n >= 12')
    lam, U = np.linalg.eigh(X.T @ X / n)
    lz = lam[max(0, p - n):]
    if np.any(lz / lz.sum() < 1e-12): raise ValueError('a numerically zero eigenvalue among the min(p, n) nonzero ones')   # p ~ n is fine
    h = n ** (-1 / 3); H = h * lz[None, :]; x = (lz[:, None] - lz[None, :]) / H; s5 = np.sqrt(5.0)
    ft = (3 / (4 * s5)) * np.mean(np.maximum(1 - x ** 2 / 5, 0) / H, axis=1)
    with np.errstate(divide='ignore', invalid='ignore'):
        Hf = (-3 / (10 * np.pi)) * x + (3 / (4 * s5 * np.pi)) * (1 - x ** 2 / 5) * np.log(np.abs((s5 - x) / (s5 + x)))
    edge = np.abs(x) == s5; Hf[edge] = (-3 / (10 * np.pi)) * x[edge]
    Hft = np.mean(Hf / H, axis=1)
    if p <= n:
        c = p / n; d = lz / ((np.pi * c * lz * ft) ** 2 + (1 - c - np.pi * c * lz * Hft) ** 2)
    else:
        Hf0 = (1 / np.pi) * (3 / (10 * h ** 2) + 3 / (4 * s5 * h) * (1 - 1 / (5 * h ** 2)) * np.log((1 + s5 * h) / (1 - s5 * h))) * np.mean(1 / lz)
        d0 = 1 / (np.pi * (p - n) / n * Hf0); d = np.r_[np.full(p - n, d0), lz / (np.pi ** 2 * lz ** 2 * (ft ** 2 + Hft ** 2))]
    return (U * d) @ U.T

def nested_target(G, a: float, b: float):
    """T(a, b) = a 11' + b G + (1 - a - b) I with G's diagonal set to 1 (SPEC §8). With G PSD (a Gram matrix of unit
    vectors, or a block matrix of industry indicators), a, b >= 0 and a + b < 1, T is positive definite with unit
    diagonal; b = 0 is the constant-correlation target. Card: docs/STATS_GUIDE.md#fn-text_target"""
    G = np.array(G, dtype=np.float64); np.fill_diagonal(G, 1.0); N = len(G)
    return a * np.ones((N, N)) + b * G + (1 - a - b) * np.eye(N)

def fit_target_ab(r, g=None, cap: float = 0.999):
    """Constrained least squares of pair correlations r_ij on [1, g_ij]: minimise sum (r - a - b g)^2 subject to
    a >= 0, b >= 0, a + b <= cap (D20(b)). The objective is a convex quadratic, so the minimiser over the triangle is the
    unconstrained OLS solution if feasible, else the best point on one of the three edges (each a one-dimensional
    least squares, clipped to the edge); all candidates are evaluated and the lowest sum of squares wins. g=None fits
    the constant-correlation target (b = 0). Returns (a, b). Card: docs/STATS_GUIDE.md#fn-text_target"""
    r = np.asarray(r, dtype=np.float64)
    if g is None: return float(np.clip(r.mean(), 0, cap)), 0.0
    g = np.asarray(g, dtype=np.float64)
    sse = lambda a, b: float(np.sum((r - a - b * g) ** 2))
    cands = [(np.clip(r.mean(), 0, cap), 0.0)]                                             # edge b = 0
    gg = g @ g; cands.append((0.0, np.clip((r @ g) / gg, 0, cap) if gg > 0 else 0.0))     # edge a = 0
    w = 1 - g; ww = w @ w                                                                  # edge a + b = cap: r - cap g = a (1 - g)
    a_e = np.clip(((r - cap * g) @ w) / ww, 0, cap) if ww > 0 else 0.0; cands.append((a_e, cap - a_e))
    gc = g - g.mean(); vg = gc @ gc
    if vg > 0:
        b_u = (gc @ (r - r.mean())) / vg; a_u = r.mean() - b_u * g.mean()
        if a_u >= 0 and b_u >= 0 and a_u + b_u <= cap: cands.append((a_u, b_u))
    a, b = min(cands, key=lambda ab: sse(*ab)); return float(a), float(b)

def ss_intensity(X, Tgt):
    """Schaefer & Strimmer (2005) eq. 8 intensity for shrinking the sample correlation of the n x N returns X towards
    the fixed target Tgt (SPEC §8; D20(c)). With x the standardised data (ddof = 1), w_kij = x_ki x_kj,
    r_ij = n/(n-1) mean_k w_kij (the sample correlation) and Var^(r_ij) = n/(n-1)^3 sum_k (w_kij - wbar_ij)^2:
        delta = sum_{i != j} Var^(r_ij) / sum_{i != j} (r_ij - t_ij)^2, clipped to [0, 1].
    sum_k w_kij^2 = ((X o X)'(X o X))_ij, so no n x N x N array is built. The same formula serves every target
    (constant correlation, industry, text, placebo), so two targets differ only in the target itself. Not LW 2004's
    own constant-correlation intensity. Returns (delta, R). Card: docs/STATS_GUIDE.md#fn-text_target"""
    Z = standardise(X); n = Z.shape[0]
    wbar = Z.T @ Z / n; R = n / (n - 1) * wbar; Q = Z * Z
    var = n / (n - 1) ** 3 * (Q.T @ Q - n * wbar ** 2)
    off = ~np.eye(len(R), dtype=bool); den = np.sum((R - Tgt)[off] ** 2)
    return float(np.clip(np.sum(var[off]) / den, 0, 1)) if den > 0 else 1.0, R

def shrink(R, Tgt, delta: float):
    """Linear shrinkage delta T + (1 - delta) R (unit diagonal kept when both have one)."""
    return delta * np.asarray(Tgt, dtype=np.float64) + (1 - delta) * np.asarray(R, dtype=np.float64)

def precondition_nl(X, Tgt):
    """Text-preconditioned nonlinear shrinkage (Ledoit & Wolf 2017, RFS, eq. 16): with T = V diag(mu) V' positive
    definite (np.linalg.eigh), transform the standardised returns Y = Z T^{-1/2}, shrink their covariance with
    lw_nonlinear, and transform back: R^ = T^{1/2} NL(Y) T^{1/2}, renormalised to unit diagonal. Nonlinear shrinkage
    keeps the eigenvectors of whatever it is given; after preconditioning those are the eigenvectors of the data
    relative to the target, so the target's information about eigenvectors is used. T = I gives lw_nonlinear itself.
    Card: docs/STATS_GUIDE.md#fn-precondition"""
    mu, V = np.linalg.eigh(np.asarray(Tgt, dtype=np.float64))
    if mu.min() <= 0: raise ValueError('the target must be positive definite')
    Th, Tmh = (V * np.sqrt(mu)) @ V.T, (V / np.sqrt(mu)) @ V.T
    return to_corr(Th @ lw_nonlinear(standardise(X) @ Tmh) @ Th)

def factor_fit(X, F):
    """OLS of every column of X (n x N) on [1, F] (tfs_stats.regression.ols_qr): returns (B [N x K] slopes,
    E [n x N] residuals, Cov(F) [K x K] with ddof = 1)."""
    X = np.asarray(X, dtype=np.float64); F = np.asarray(F, dtype=np.float64)
    b, E = ols_qr(np.column_stack([np.ones(len(F)), F]), X)
    return b[1:].T, E, np.atleast_2d(np.cov(F, rowvar=False))

def factor_corr(X, F=None, k: int | None = None, resid_corr=None):
    """Factor model in correlation form (D20(a) estimators 12-14; D20(d)).
      F given (FF6): Sigma = B Cov(F) B' + D_e^{1/2} R_e D_e^{1/2}, residual variances with ddof = K + 1, R_e = I
        (diagonal residuals) or resid_corr (e.g. the residual correlation shrunk to a text target); returned as a
        correlation matrix.
      k given (PCA): first k principal components of the standardised returns (tfs_stats.rmt.pca_factors):
        R^ = V_k Lambda_k V_k' with the diagonal reset to 1 (diagonal residuals on the correlation scale).
    Card: docs/STATS_GUIDE.md#fn-factor_corr"""
    X = np.asarray(X, dtype=np.float64)
    if F is not None:
        B, E, SF = factor_fit(X, F); n, K = len(X), B.shape[1]; ve = (E ** 2).sum(0) / (n - K - 1)
        Re = np.eye(X.shape[1]) if resid_corr is None else np.asarray(resid_corr, dtype=np.float64)
        return to_corr(B @ SF @ B.T + np.sqrt(ve)[:, None] * Re * np.sqrt(ve)[None, :])
    Z = standardise(X); V, f, _ = pca_factors(Z, k); lamk = f.var(0, ddof=1)
    R = (V * lamk) @ V.T; np.fill_diagonal(R, 1.0); return R
