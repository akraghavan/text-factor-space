"""tfs_stats.covariance: known spectra, brute force and an optional check against the published algorithm."""
import numpy as np, pytest
from scipy import optimize
from sklearn.covariance import LedoitWolf
from tfs_stats.covariance import (lw_nonlinear, nested_target, fit_target_ab, ss_intensity, shrink, precondition_nl,
                                  factor_corr, to_corr, standardise)

def _sigma(p, rng):
    """Ledoit-Wolf's heterogeneous spectrum (20% at 1, 40% at 3, 40% at 10) with random eigenvectors."""
    ev = np.r_[np.ones(p // 5), np.full(2 * p // 5, 3.0), np.full(p - p // 5 - 2 * p // 5, 10.0)]
    Q, _ = np.linalg.qr(rng.normal(size=(p, p))); return (Q * ev) @ Q.T

def _mv_loss(S_hat, S):
    O = np.linalg.inv(S_hat); p = len(S)
    return np.trace(O @ S @ O) / p / (np.trace(O) / p) ** 2 - 1 / (np.trace(np.linalg.inv(S)) / p)

@pytest.mark.parametrize('p,n', [(100, 300), (200, 100)])
def test_lw_nonlinear_beats_sample_and_linear(p, n):
    rng = np.random.default_rng(0); S = _sigma(p, rng); L = np.linalg.cholesky(S); fro, mv = [], []
    for _ in range(4):
        X = rng.normal(size=(n, p)) @ L.T
        nl, lin, smp = lw_nonlinear(X), LedoitWolf().fit(X).covariance_, np.cov(X, rowvar=False)
        fro.append([np.linalg.norm(e - S) for e in (nl, lin, smp)]); mv.append([_mv_loss(nl, S), _mv_loss(lin, S)])
    fro, mv = np.mean(fro, 0), np.mean(mv, 0)
    assert fro[0] < fro[1] and fro[0] < fro[2] and mv[0] < mv[1]
    if p < n: assert _mv_loss(lw_nonlinear(X), S) < _mv_loss(np.cov(X, rowvar=False), S)

def test_lw_nonlinear_keeps_eigenvectors_and_is_positive_definite():
    rng = np.random.default_rng(1); X = rng.normal(size=(80, 120)) @ np.linalg.cholesky(_sigma(120, rng)).T
    E = lw_nonlinear(X); Xc = X - X.mean(0); _, U = np.linalg.eigh(Xc.T @ Xc / 79)
    D = U.T @ E @ U; assert np.abs(D - np.diag(np.diag(D))).max() < 1e-8 * np.abs(D).max()
    assert np.linalg.eigvalsh(E).min() > 0

def test_lw_nonlinear_converges_to_sample_as_n_over_p_grows():
    rng = np.random.default_rng(2); p = 5; S = _sigma(p, rng); X = rng.normal(size=(200_000, p)) @ np.linalg.cholesky(S).T
    a, b = np.linalg.eigvalsh(lw_nonlinear(X)), np.linalg.eigvalsh(np.cov(X, rowvar=False))
    assert np.max(np.abs(a / b - 1)) < 0.01

@pytest.mark.parametrize('p,n', [(60, 150), (150, 60)])
def test_lw_nonlinear_matches_published_algorithm(p, n):
    ref = pytest.importorskip('nonlinshrink')                     # port of the authors' code; installed locally, not in CI
    rng = np.random.default_rng(3); X = rng.normal(size=(n, p)) @ np.linalg.cholesky(_sigma(p, rng)).T
    assert np.allclose(lw_nonlinear(X), ref.shrink_cov(X), rtol=0, atol=1e-8)

def test_nested_target_is_a_pd_correlation_matrix():
    rng = np.random.default_rng(4); V = rng.normal(size=(30, 5)); V /= np.linalg.norm(V, axis=1, keepdims=True)
    T = nested_target(V @ V.T, 0.2, 0.5)
    assert np.allclose(np.diag(T), 1) and np.linalg.eigvalsh(T).min() > 0
    assert np.allclose(nested_target(V @ V.T, 0.3, 0.0)[~np.eye(30, dtype=bool)], 0.3)

@pytest.mark.parametrize('a,b', [(0.2, 0.3), (0.0, 0.6), (0.4, 0.0), (0.5, 0.7), (-0.2, 0.4)])
def test_fit_target_ab_matches_a_numerical_solver(a, b):
    rng = np.random.default_rng(5); g = rng.uniform(-0.2, 0.9, 2000); r = a + b * g + 0.05 * rng.normal(size=2000)
    ah, bh = fit_target_ab(r, g); sse = lambda v: np.sum((r - v[0] - v[1] * g) ** 2)
    num = optimize.minimize(sse, [0.1, 0.1], method='SLSQP', bounds=[(0, None), (0, None)],
                            constraints=[{'type': 'ineq', 'fun': lambda v: 0.999 - v[0] - v[1]}], options={'ftol': 1e-14})
    assert ah >= 0 and bh >= 0 and ah + bh <= 0.999 + 1e-12 and sse([ah, bh]) <= num.fun + 1e-9

def test_ss_intensity_matches_brute_force():
    rng = np.random.default_rng(6); X = rng.normal(size=(40, 7)) @ rng.normal(size=(7, 7)); T = nested_target(np.eye(7), 0.3, 0.0)
    d, R = ss_intensity(X, T); Z = standardise(X); n = len(Z)
    W = np.einsum('ki,kj->kij', Z, Z); wb = W.mean(0); var = n / (n - 1) ** 3 * ((W - wb) ** 2).sum(0)
    off = ~np.eye(7, dtype=bool); ref = np.clip(var[off].sum() / ((R - T)[off] ** 2).sum(), 0, 1)
    assert np.isclose(d, ref) and np.allclose(R, np.corrcoef(X, rowvar=False)) and 0 <= d <= 1
    assert np.allclose(shrink(R, T, d), d * T + (1 - d) * R)

def test_precondition_nl():
    rng = np.random.default_rng(7); X = rng.normal(size=(100, 40))
    assert np.allclose(precondition_nl(X, np.eye(40)), to_corr(lw_nonlinear(standardise(X))))
    V = rng.normal(size=(60, 4)); V /= np.linalg.norm(V, axis=1, keepdims=True); T = nested_target(V @ V.T, 0.2, 0.6)
    L = np.linalg.cholesky(T); lp, ln = [], []
    for _ in range(4):
        Y = rng.normal(size=(50, 60)) @ L.T
        lp.append(np.linalg.norm(precondition_nl(Y, T) - T)); ln.append(np.linalg.norm(to_corr(lw_nonlinear(standardise(Y))) - T))
    assert np.mean(lp) < np.mean(ln)                              # a correct target helps

def test_factor_corr():
    rng = np.random.default_rng(8); n, N, K = 20_000, 12, 3; F = rng.normal(size=(n, K)); B = rng.normal(size=(N, K))
    X = F @ B.T + rng.normal(size=(n, N)); true = to_corr(B @ B.T + np.eye(N))
    assert np.abs(factor_corr(X, F) - true).max() < 0.02
    R = factor_corr(X, k=3); lam, V = np.linalg.eigh(np.corrcoef(X, rowvar=False)); Rk = (V[:, -3:] * lam[-3:]) @ V[:, -3:].T
    off = ~np.eye(N, dtype=bool)                                   # the definition: top-3 eigen-reconstruction, unit diagonal
    assert np.allclose(R[off], Rk[off]) and np.allclose(np.diag(R), 1) and np.linalg.eigvalsh(R).min() > 0
