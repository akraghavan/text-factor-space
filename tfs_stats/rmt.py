"""Random-matrix tools for the correlation spectrum, written by hand. Tests in tests/test_rmt.py."""
import numpy as np

def mp_edges(q: float, sigma2: float = 1.0):
    """Marchenko-Pastur support of the eigenvalues of a sample correlation matrix of N iid series over T obs,
    q = N/T < 1:  lambda_pm = sigma2 * (1 +/- sqrt(q))^2.  Returns (lambda_minus, lambda_plus)."""
    raise NotImplementedError

def ipr(V: np.ndarray):
    """Inverse participation ratio of each column (unit eigenvector) v: sum_i v_i^4.
    ~1/N for a delocalised vector, ~1/k for a vector spread evenly over k components."""
    raise NotImplementedError

def clip_correlation(C: np.ndarray, T: int):
    """Eigenvalue clipping (Laloux-Cizeau-Bouchaud-Potters 1999): keep eigenvalues above lambda_plus,
    replace the bulk by their average so the trace is preserved, rebuild, then rescale to unit diagonal."""
    raise NotImplementedError

def ledoit_wolf(X: np.ndarray):
    """Ledoit-Wolf (2004) shrinkage of the sample covariance of demeaned X [T x N] towards mu*I.
    Must match sklearn.covariance.LedoitWolf(assume_centered=False).fit(X).covariance_."""
    raise NotImplementedError

def min_var_weights(S: np.ndarray):
    """Global minimum-variance weights w = S^{-1} 1 / (1' S^{-1} 1). Use a linear solve, not an inverse."""
    raise NotImplementedError
