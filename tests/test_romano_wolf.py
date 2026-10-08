"""tfs_stats.multitest.romano_wolf: FWER under a simulated null, and power against a real effect."""
import numpy as np
from tfs_stats.multitest import romano_wolf

def _ar(T, k, rng, mu):
    e = rng.normal(size=(T, k)); x = np.empty_like(e); x[0] = e[0]
    for t in range(1, T): x[t] = 0.2 * x[t - 1] + e[t]
    return x + mu

def test_fwer_under_the_null():
    # iid null in the shape of the C family (T = 165, 8 series), where the bootstrap is valid: nominal 5%, about 6.5% in a
    # 600-draw simulation at these sizes; under AR(1) persistence 0.2 with blocks of 4 it rises to 8.5% (documented, card)
    rng = np.random.default_rng(7); hits = 0
    for s in range(300):
        X = rng.normal(size=(165, 8)); hits += bool(romano_wolf({f'm{j}': X[:, j] for j in range(8)}, reps=500, seed=1000 + s)['superior'])
    assert hits / 300 <= 0.10

def test_finds_a_real_effect():
    rng = np.random.default_rng(1); X = _ar(165, 4, rng, np.array([0.6, 0, 0, 0]))
    assert romano_wolf({f'm{j}': X[:, j] for j in range(4)}, reps=1000)['superior'] == ['m0']

def test_studentised_finds_a_small_scale_effect_next_to_a_noisy_null():
    # a noisy series with mean 0 (scale 20) and a quiet one with a real positive mean (scale 1): with raw means the noisy
    # series sets the critical value; with each series divided by its own SE the quiet effect is found
    from tfs_stats.regression import fm_inference
    rng = np.random.default_rng(3); T = 165; X = np.column_stack([20 * rng.normal(size=T), 0.35 + rng.normal(size=T)])
    se = fm_inference(X, 4)['se']; S = {'noisy': X[:, 0], 'quiet': X[:, 1]}
    assert romano_wolf(S, reps=2000, se={'noisy': se[0], 'quiet': se[1]})['superior'] == ['quiet']
    assert romano_wolf(S, reps=2000)['superior'] == []

def test_studentised_size_simulation_runs_and_is_reproducible():
    from tfs_stats.multitest import romano_wolf_size
    a = romano_wolf_size(91, 4, 0.0, 4, 3, nsim=40, reps=200, seed=5); b = romano_wolf_size(91, 4, 0.0, 4, 3, nsim=40, reps=200, seed=5)
    assert a == b and 0 <= a <= 0.2
