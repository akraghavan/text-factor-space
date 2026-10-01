"""tfs_stats.network and tfs_stats.multitest: simulations with known answers and a statsmodels reference."""
import numpy as np
from statsmodels.stats.multitest import multipletests
from tfs_stats.network import residualize_on_blocks, mode_alignment, share_test
from tfs_stats.multitest import holm, bh
from tfs_stats.regression import one_sided_p
rng = np.random.default_rng(3)

def test_residualize_removes_block_mean():
    n = 60; lab = np.repeat(np.arange(6), 10); same = lab[:, None] == lab[None, :]
    G = 0.3 * same + rng.normal(0, 0.05, (n, n)); G = (G + G.T) / 2; np.fill_diagonal(G, 0)
    R = residualize_on_blocks(G, lab); i, j = np.triu_indices(n, 1)
    assert np.allclose(R, R.T) and np.allclose(np.diag(R), 0)
    assert abs(R[i, j][same[i, j]].mean()) < 1e-10 and abs(R[i, j][~same[i, j]].mean()) < 1e-10

def test_alignment_detects_a_planted_mode_and_is_uniform_otherwise():
    n = 200; v = np.zeros(n); v[:20] = 1 / np.sqrt(20)                                   # a mode localised on 20 firms
    G = np.outer(v, v) * 5 + rng.normal(0, 0.01, (n, n)); G = (G + G.T) / 2; np.fill_diagonal(G, 0)
    Q, _ = np.linalg.qr(rng.normal(size=(n, 40)))                                        # 40 random unit modes
    A, p = mode_alignment(np.column_stack([v, Q]), G, n_perm=500, seed=1)
    assert p[0] < 0.01 and 0.3 < p[1:].mean() < 0.7

def test_share_test():
    assert share_test(5, 100)['pvalue'] > 0.3 and share_test(20, 100)['pvalue'] < 1e-5

def test_holm_and_bh_match_statsmodels():
    p = np.array([0.012, 0.04]); h = holm(p)
    assert list(h['reject']) == [True, True] and np.allclose(h['thresholds'], [0.025, 0.05])
    assert list(holm([0.03, 0.04])['reject']) == [False, False]
    q = rng.uniform(size=30) ** 2
    assert np.array_equal(bh(q)['reject'], multipletests(q, 0.1, 'fdr_bh')[0])

def test_one_sided_p():
    assert np.isclose(one_sided_p(1.6448536), 0.05) and np.isclose(one_sided_p(-1.6448536, direction='-'), 0.05)
