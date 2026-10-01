"""Network inference for Element B (SPEC §6.6; PREREG Element B): residualising a similarity matrix on industry blocks,
the alignment of residual eigenmodes with it under a firm-relabelling null, and the binomial test of the share of
aligned modes. No library implements these; numpy, tfs_stats.regression.ols_qr and scipy.stats.binomtest.
Tests: tests/test_network.py (simulations with known answers). Card: docs/STATS_GUIDE.md#fn-mode_alignment"""
import numpy as np
from scipy import stats
from .regression import ols_qr

__all__ = ['residualize_on_blocks', 'residualize_on_dummies', 'mode_alignment', 'share_test', 'subspace_overlap']

def residualize_on_blocks(G: np.ndarray, labels) -> np.ndarray:
    """'Beyond industry' similarity: regress the off-diagonal entries g_ij (i < j) on [1, 1(same block)] by OLS
    (tfs_stats.regression.ols_qr) and return the residuals as a symmetric matrix with a zero diagonal. A firm with a
    missing label (NaN / None) matches no one. What is left is similarity that this one block structure does not
    predict; with SIC-3 labels that is 'beyond SIC-3 co-membership' (similarity shared within an SIC-2 or SIC-1 sector
    stays in; use residualize_on_dummies with nested SIC-1..4 for 'beyond industry')."""
    G = np.asarray(G, dtype=np.float64); n = len(G); i, j = np.triu_indices(n, 1)
    lab = np.asarray(labels, dtype=object)
    miss = np.array([l is None or (isinstance(l, float) and np.isnan(l)) for l in lab])
    same = ((lab[i] == lab[j]) & ~miss[i] & ~miss[j]).astype(float)
    _, e = ols_qr(np.column_stack([np.ones(len(i)), same]), G[i, j])
    R = np.zeros_like(G); R[i, j] = e; R[j, i] = e
    return R

def residualize_on_dummies(G: np.ndarray, label_sets) -> np.ndarray:
    """Like residualize_on_blocks with several co-membership dummies at once: regress g_ij (i < j) on
    [1, 1(same label_1), ..., 1(same label_L)] by OLS (tfs_stats.regression.ols_qr) and return the symmetric residual
    matrix with a zero diagonal. With nested SIC-1..4 labels this removes every level of the SIC hierarchy (the same
    industry controls Element C uses), which is what 'beyond industry' should mean; missing labels never match."""
    G = np.asarray(G, dtype=np.float64); n = len(G); i, j = np.triu_indices(n, 1); cols = [np.ones(len(i))]
    for labels in label_sets:
        lab = np.asarray(labels, dtype=object)
        miss = np.array([l is None or (isinstance(l, float) and np.isnan(l)) for l in lab])
        cols.append(((lab[i] == lab[j]) & ~miss[i] & ~miss[j]).astype(float))
    X = np.column_stack(cols); X = X[:, np.r_[True, X[:, 1:].std(0) > 0]]                     # drop dummies that are all 0
    _, e = ols_qr(X, G[i, j])
    R = np.zeros_like(G); R[i, j] = e; R[j, i] = e
    return R

def subspace_overlap(U: np.ndarray, W: np.ndarray, n_perm: int = 1000, seed: int = 0):
    """Squared principal-angle overlap between span(U) (K residual modes, orthonormal columns) and span(W) (the top-K
    eigenvectors of a text Gram matrix): ov = ||U'W||_F^2 / K = mean cos^2 of the principal angles (scipy-free: singular
    values of U'W are the cosines). A random K-dimensional subspace gives E[ov] = K/N. One-sided p from relabelling
    firms (permuting the rows of W): p = (1 + #{ov(P) >= ov}) / (n_perm + 1). Returns (ov, K/N, p)."""
    U = np.asarray(U, dtype=np.float64); W = np.asarray(W, dtype=np.float64); K = U.shape[1]; N = U.shape[0]
    ov = float(np.sum((U.T @ W) ** 2) / K); rng = np.random.default_rng(seed); ge = 0
    for _ in range(n_perm): ge += np.sum((U.T @ W[rng.permutation(N)]) ** 2) / K >= ov
    return ov, K / N, (1 + ge) / (n_perm + 1)

def mode_alignment(U: np.ndarray, G: np.ndarray, n_perm: int = 1000, seed: int = 0):
    """Alignment A_k = u_k' G u_k of each column u_k of U (unit eigenvectors) with a symmetric zero-diagonal matrix G,
    and its one-sided permutation p-value under joint row/column relabelling of the firms:
      relabel firms by a random permutation P (rows and columns together): A_k(P) = u_k' P G P' u_k = (P'u_k)' G (P'u_k),
      i.e. the same as permuting the entries of u_k; p_k = (1 + #{A_k(P) >= A_k}) / (n_perm + 1).
    The null keeps G's whole structure (degrees, blocks, spectrum) and only breaks which firm sits where, which is the
    QAP logic (Krackhardt 1988). One draw serves all modes. Returns (A [K], p [K])."""
    U = np.asarray(U, dtype=np.float64); G = np.asarray(G, dtype=np.float64)
    if U.ndim == 1: U = U[:, None]
    A = np.einsum('ik,ik->k', U, G @ U)
    rng = np.random.default_rng(seed); ge = np.zeros(U.shape[1])
    for _ in range(n_perm):
        Up = U[rng.permutation(len(U))]
        ge += np.einsum('ik,ik->k', Up, G @ Up) >= A
    return A, (1 + ge) / (n_perm + 1)

def share_test(n_hit: int, n_total: int, p0: float = 0.05):
    """One-sided binomial test that the share of 'hits' exceeds p0 (scipy.stats.binomtest, alternative='greater').
    Under the null each mode's permutation p-value is ~uniform, so P(p < 0.05) = 0.05. Treats modes as independent,
    which pooled modes across overlapping annual windows are not exactly; the PREREG states this rule as is.
    Returns dict(share, pvalue)."""
    r = stats.binomtest(int(n_hit), int(n_total), p0, alternative='greater')
    return {'share': n_hit / n_total, 'pvalue': float(r.pvalue)}
