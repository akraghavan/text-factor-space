"""tfs_stats.varcompare: size under a GARCH null with highly correlated portfolios, recovery of a known Delta."""
import numpy as np
from tfs_stats.varcompare import log_var_diff, log_var_diff_boot

def _garch_pair(T, rng, rho=0.95, scale_b=1.0):
    """Two returns with a common GARCH(1,1) variance (omega 0.05, alpha 0.1, beta 0.85) and correlation rho."""
    z = rng.multivariate_normal([0, 0], [[1, rho], [rho, 1]], T + 200); h = np.empty(T + 200); h[0] = 1.0; e = np.empty(T + 200)
    for t in range(T + 200):
        if t: h[t] = 0.05 + 0.1 * e[t - 1] ** 2 + 0.85 * h[t - 1]
        e[t] = np.sqrt(h[t]) * z[t, 0]
    r = np.sqrt(h)[:, None] * z; return r[200:, 0], scale_b * r[200:, 1]

def test_size_under_equal_variances():
    rng = np.random.default_rng(0)
    rej = [log_var_diff(*_garch_pair(1800, rng))['p_one_sided'] < 0.05 for _ in range(500)]
    assert 0.03 <= np.mean(rej) <= 0.08

def test_recovers_a_known_difference():
    rng = np.random.default_rng(1); T = 20_000; z = rng.multivariate_normal([0, 0], [[1, 0.9], [0.9, 1]], T)
    r = log_var_diff(0.9 * z[:, 0], z[:, 1]); se_iid = np.sqrt(4 * (1 - 0.9 ** 2) / T)
    assert abs(r['delta'] - np.log(0.81)) < 3 * r['se'] and abs(r['se'] / se_iid - 1) < 0.15 and r['p_one_sided'] < 1e-6

def test_bootstrap_agrees_on_a_clear_case():
    rng = np.random.default_rng(2); a, b = _garch_pair(1500, rng, scale_b=1.1)
    assert log_var_diff_boot(a, b, B=199)['p_one_sided'] < 0.05 and log_var_diff_boot(b, a, B=199)['p_one_sided'] > 0.5
