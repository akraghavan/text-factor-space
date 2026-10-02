"""tfs_stats.pairs: MRQAP-DSP against statsmodels and a null simulation; the dyadic meat against a brute-force double sum."""
import numpy as np, statsmodels.api as sm
from tfs_stats.pairs import mrqap_dsp, DyadicMeat

def _net(n, rng, signal=0.0):
    i, j = np.triu_indices(n, 1); grp = rng.integers(0, 4, n); same = (grp[i] == grp[j]).astype(float)
    a = rng.normal(size=n); s = a[i] + a[j] + 0.5 * same + rng.normal(size=len(i))       # s depends on firms and groups
    f = rng.normal(size=n); y = 0.3 * same + f[i] + f[j] + signal * s + rng.normal(size=len(i))   # firm effects in y
    return y, s, np.column_stack([np.ones(len(i)), same]), i, j

def test_mrqap_observed_t_matches_statsmodels():
    rng = np.random.default_rng(1); y, s, C, i, j = _net(30, rng, 0.2)
    r = mrqap_dsp(y, s, C, i, j, 30, n_perm=9, seed=0); fit = sm.OLS(y, np.column_stack([C, s])).fit()
    assert np.isclose(r['b'], fit.params[-1]) and np.isclose(r['t'], fit.tvalues[-1])

def test_mrqap_size_under_null_and_power():
    rng = np.random.default_rng(2); rej = [mrqap_dsp(*_net(25, rng), 25, n_perm=99, seed=k)['p_one_sided'] <= 0.05 for k in range(200)]
    assert 0.01 <= np.mean(rej) <= 0.10                                       # nominal 5%; the naive OLS t over-rejects here
    y, s, C, i, j = _net(25, rng, 0.5); assert mrqap_dsp(y, s, C, i, j, 25, n_perm=99)['p_one_sided'] == 0.01

def test_dyadic_meat_matches_brute_force():
    rng = np.random.default_rng(3); n, k = 8, 3; i, j = np.triu_indices(n, 1)
    a = np.tile(i, 3); b = np.tile(j, 3); S = rng.normal(size=(len(a), k))       # 3 periods of all pairs
    D = DyadicMeat(n, k)
    for t in range(3): sl = slice(t * len(i), (t + 1) * len(i)); D.add(S[sl], a[sl], b[sl])
    share = (a[:, None] == a[None, :]) | (a[:, None] == b[None, :]) | (b[:, None] == a[None, :]) | (b[:, None] == b[None, :])
    assert np.allclose(D.meat(), S.T @ share @ S)
    V, G = D.vcov(np.eye(k)); assert G == n and np.allclose(V, n / (n - 1) * len(a) / (len(a) - k) * D.meat())
