"""Random-matrix tools for the correlation spectrum (B) and covariance estimators for D: the project's estimator layer
(D13). numpy for the closed forms, scikit-learn for Ledoit-Wolf. Tests: tests/test_rmt.py. Cards: docs/STATS_GUIDE.md#stats-rmt"""
import numpy as np
from sklearn.covariance import LedoitWolf

__all__ = ['mp_edges', 'mp_sigma2_iterated', 'circular_shift_edge', 'ipr', 'clip_correlation', 'ledoit_wolf', 'min_var_weights', 'pca_factors']

def mp_edges(q: float, sigma2: float = 1.0):
    """Marchenko-Pastur support of the eigenvalues of a sample correlation matrix of N iid series over T observations,
    q = N/T:  lambda_pm = sigma2 (1 +/- sqrt(q))^2.  Returns (lambda_minus, lambda_plus). Closed form, numpy.
    Raises ValueError for q > 1 (N > T: N - T eigenvalues are exactly 0 and lambda_minus no longer bounds the smallest
    one). Callers adjust the inputs: sigma2 = 1 - lambda_max/N (iterated) once the market mode is removed, and
    q_eff = N/(T - K - 1) for residuals of a K-factor regression. Card: docs/STATS_GUIDE.md#fn-mp_edges"""
    if q <= 0: raise ValueError('q must be positive')
    if q > 1: raise ValueError(f'q = {q:.3f} > 1: more series than observations; the MP edges do not apply as stated')
    r = np.sqrt(q)
    return sigma2 * (1 - r) ** 2, sigma2 * (1 + r) ** 2

def mp_sigma2_iterated(eigs: np.ndarray, q: float, tol: float = 1e-10, max_iter: int = 100):
    """Noise variance for the Marchenko-Pastur edge once structure is removed (SPEC §6.4; Laloux et al. 1999):
    iterate sigma2 = 1 - sum_{lambda_k > lambda_plus(sigma2)} lambda_k / N from sigma2 = 1 until it stops changing.
    The trace of a correlation matrix is N; eigenvalues above the edge (the market mode, sectors) carry their share of
    it, so the noise bulk has less than unit variance.
    The map is monotone (lower sigma2 -> lower edge -> more eigenvalues above -> lower sigma2), so it either converges or
    runs away when the bulk is wider than MP allows (heavy tails, heteroskedasticity): the edge then walks into the
    bulk. On a runaway (sigma2 <= 0 or more than half the eigenvalues above the edge) the function returns Laloux's
    one-step value sigma2 = 1 - sum_{lambda_k > lambda_plus(1)} lambda_k / N with converged=False; that case is itself
    evidence the iid MP edge is too narrow, which is why the circular-shift edge is primary in B.
    Returns (sigma2, lambda_plus, n_above, converged). numpy only. Card: docs/STATS_GUIDE.md#fn-mp_edges"""
    eigs = np.asarray(eigs, dtype=np.float64); N = len(eigs)
    one = 1 - eigs[eigs > mp_edges(q, 1.0)[1]].sum() / N
    s2 = 1.0
    for _ in range(max_iter):
        hi = mp_edges(q, s2)[1]; above = eigs > hi; new = 1 - eigs[above].sum() / N
        if new <= 0 or above.sum() > N / 2:
            hi = mp_edges(q, one)[1]; return one, hi, int((eigs > hi).sum()), False
        if abs(new - s2) < tol: s2 = new; break
        s2 = new
    hi = mp_edges(q, s2)[1]
    return s2, hi, int((eigs > hi).sum()), True

def circular_shift_edge(Z: np.ndarray, draws: int = 200, quantile: float = 0.95, seed: int = 0):
    """Empirical noise edge for the top eigenvalue of the correlation matrix of Z (T x N, columns standardised):
    shift each column circularly by an independent random offset, recompute the correlation matrix's largest
    eigenvalue, repeat `draws` times, return (quantile of the null top eigenvalues, the draws). Shifting keeps every
    series' own distribution and autocorrelation but destroys the synchrony between series, so it widens the edge for
    heavy tails and serial dependence that Marchenko-Pastur's iid assumption ignores (SPEC §6.4). No library has it;
    numpy (a circular index shift per column, np.linalg.eigvalsh). Card: docs/STATS_GUIDE.md#fn-mp_edges"""
    Z = np.asarray(Z, dtype=np.float64); T, N = Z.shape; rng = np.random.default_rng(seed)
    Z = (Z - Z.mean(0)) / Z.std(0); rows = np.arange(T)[:, None]; top = np.empty(draws)
    for d in range(draws):
        off = rng.integers(0, T, N); Zs = Z[(rows - off[None, :]) % T, np.arange(N)[None, :]]
        top[d] = np.linalg.eigvalsh(Zs.T @ Zs / T)[-1]
    return float(np.quantile(top, quantile)), top

def ipr(V: np.ndarray):
    """Inverse participation ratio of each column v of V (unit eigenvectors from eigh, V[:, k]): sum_i v_i^4.
    numpy: (V**4).sum(axis=0). 1 for a vector on one stock, 1/m for one spread evenly over m, and E = 3/(N+2) ~ 3/N for
    a random unit vector (the noise baseline B uses). Card: docs/STATS_GUIDE.md#fn-ipr"""
    V = np.asarray(V, dtype=np.float64)
    if V.ndim == 1: V = V[:, None]
    return (V ** 4).sum(axis=0)

def clip_correlation(C: np.ndarray, T: int):
    """Eigenvalue clipping (Laloux, Cizeau, Bouchaud & Potters 1999): np.linalg.eigh(C); keep eigenvalues above
    lambda_plus = mp_edges(N/T)[1]; replace every bulk eigenvalue (<= lambda_plus) by the bulk mean, which keeps the
    trace = N; rebuild V diag V'; rescale to unit diagonal D^{-1/2} C D^{-1/2}; symmetrise. No library implements it.
    Positive definite because every rebuilt eigenvalue is > 0 (the bulk mean of a PSD spectrum with positive trace).
    For residual correlations pass the effective sample size T - K - 1. Card: docs/STATS_GUIDE.md#fn-clip_correlation"""
    C = np.asarray(C, dtype=np.float64); N = C.shape[0]
    lam, V = np.linalg.eigh(C)
    _, hi = mp_edges(N / T)
    bulk = lam <= hi
    lam2 = lam.copy()
    if bulk.any(): lam2[bulk] = lam[bulk].mean()
    Cc = (V * lam2) @ V.T
    d = np.sqrt(np.diag(Cc)); Cc = Cc / np.outer(d, d)
    Cc = (Cc + Cc.T) / 2; np.fill_diagonal(Cc, 1.0)
    return Cc

def ledoit_wolf(X: np.ndarray):
    """Ledoit-Wolf (2004, JMVA) shrinkage of the sample covariance towards mu I, mu = tr(S)/N.
    Library call: sklearn.covariance.LedoitWolf().fit(X).covariance_ (assume_centered=False: columns demeaned;
    S = X'X/T, dividing by T; delta = b^2/d^2 with b^2 capped at d^2). The fitted delta is sklearn's shrinkage_.
    Identity target, not the constant-correlation target of LW (2004, JPM), which is D's estimator 4.
    Card: docs/STATS_GUIDE.md#fn-ledoit_wolf"""
    return LedoitWolf().fit(np.asarray(X, dtype=np.float64)).covariance_

def min_var_weights(S: np.ndarray):
    """Global minimum-variance weights w = S^{-1} 1 / (1' S^{-1} 1), from one linear solve S z = 1 (np.linalg.solve),
    then w = z / sum(z); never an explicit inverse. Unconstrained (short positions allowed). The minimum variance is
    1 / (1' S^{-1} 1). Card: docs/STATS_GUIDE.md#fn-min_var_weights"""
    S = np.asarray(S, dtype=np.float64)
    z = np.linalg.solve(S, np.ones(S.shape[0]))
    return z / z.sum()

def pca_factors(Z: np.ndarray, k: int):
    """First k principal components of a T x N panel Z (columns standardised by the caller): thin SVD Z = U S V'
    (np.linalg.svd). Returns (loadings V_k [N x k], factor series Z V_k [T x k], share of variance of each component).
    Used for C's statistical-factor robustness (SPEC §7.7: FF6 plus 5 or 10 PCs of the FF6 residuals): a month's
    factor returns are that month's standardised residuals times the window's loadings, so no future data enter.
    Card: docs/STATS_GUIDE.md#fn-pca_factors"""
    Z = np.asarray(Z, dtype=np.float64); U, S, Vt = np.linalg.svd(Z, full_matrices=False)
    V = Vt[:k].T; return V, Z @ V, (S[:k] ** 2) / np.sum(S ** 2)
