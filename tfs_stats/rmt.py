"""Random-matrix tools for the correlation spectrum (B) and covariance estimators for D: the project's estimator layer
(D13). numpy for the closed forms, scikit-learn for Ledoit-Wolf. Tests: tests/test_rmt.py. Cards: docs/STATS_GUIDE.md#stats-rmt"""
import numpy as np
from sklearn.covariance import LedoitWolf

__all__ = ['mp_edges', 'ipr', 'clip_correlation', 'ledoit_wolf', 'min_var_weights']

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
