"""Multiple-testing corrections (SPEC §10.2-10.3; PREREG "Confirmatory family"): the project's estimator layer (D13).
Library call: statsmodels.stats.multitest.multipletests. Card: docs/STATS_GUIDE.md#fn-multitest"""
import numpy as np
from statsmodels.stats.multitest import multipletests

__all__ = ['holm', 'bh', 'by', 'fisher_combine', 'romano_wolf', 'romano_wolf_size']

def holm(pvals, alpha: float = 0.05):
    """Holm (1979) step-down for the confirmatory family. Sort the m p-values; the k-th smallest is compared with
    alpha / (m - k + 1) (with m = 2: 0.025 for the smaller, 0.05 for the larger), stopping at the first failure.
    Library call: multipletests(p, alpha, method='holm'). Returns dict(reject, p_adjusted, thresholds) in input order,
    thresholds being alpha / (m - rank + 1) for each p's rank. Strong FWER control under any dependence."""
    p = np.asarray(pvals, dtype=float); m = len(p)
    reject, padj, _, _ = multipletests(p, alpha=alpha, method='holm')
    rank = np.empty(m, int); rank[np.argsort(p, kind='stable')] = np.arange(m)
    return {'reject': reject, 'p_adjusted': padj, 'thresholds': alpha / (m - rank)}

def bh(pvals, q: float = 0.10):
    """Benjamini-Hochberg (1995) FDR at level q for the exploratory family: multipletests(method='fdr_bh').
    m is the number of distinct exploratory specs run (python src/runner.py count). Returns dict(reject, p_adjusted)."""
    reject, padj, _, _ = multipletests(np.asarray(pvals, dtype=float), alpha=q, method='fdr_bh')
    return {'reject': reject, 'p_adjusted': padj}

def by(pvals, q: float = 0.10):
    """Benjamini-Yekutieli (2001): FDR under arbitrary dependence (the check next to BH): multipletests(method='fdr_by')."""
    reject, padj, _, _ = multipletests(np.asarray(pvals, dtype=float), alpha=q, method='fdr_by')
    return {'reject': reject, 'p_adjusted': padj}

def fisher_combine(pvals):
    """Fisher's method for one overall p from independent tests: X = -2 sum log p ~ chi^2(2k) under the joint null
    (scipy.stats.combine_pvalues(method='fisher')). Used to pool B's per-formation subspace-overlap p-values; the annual
    windows overlap, so the combined p is optimistic in the same way as B's binomial share test."""
    from scipy import stats
    return float(stats.combine_pvalues(np.asarray(pvals, dtype=float), method='fisher').pvalue)

def romano_wolf(series, size: float = 0.05, block: int = 4, reps: int = 10_000, seed: int = 2026, se=None):
    """Romano-Wolf stepdown across slope series (PREREG multiple testing; D25, D28): which mean slopes are significantly
    positive, controlling the family-wise error rate under any dependence between the series. Library call:
    arch.bootstrap.StepM (Romano & Wolf 2005 stepdown built on Hansen's SPA bootstrap): benchmark loss 0, model losses
    -x_t (so "superior" = mean > 0), stationary bootstrap of the common months with mean block length `block`, `reps`
    replications, seed fixed, Hansen's "consistent" re-centring.
    Studentisation (D28). In arch 8.0.0 StepM's studentize flag only labels the output: the max statistic and its
    bootstrap critical values use the raw means. So the series are studentised before they reach StepM: with
    se = {name: full-sample Newey-West SE of the mean slope, from each spec's own lags}, x_t = b_t / (sqrt(T) se), whose
    mean is t / sqrt(T). The SE is held fixed across bootstrap draws (Romano & Wolf 2005, studentisation with the full-
    sample standard error), so the max is taken over t-statistics and a series with a large scale cannot set the
    critical value for the rest. se=None keeps the raw means (D25 as first run).
    Every series must cover the same months. series: {name: 1-d array}.
    Returns dict(superior: names in input order, size, block, reps, studentised)."""
    import pandas as pd
    from arch.bootstrap import StepM
    M = pd.DataFrame({k: np.asarray(v, dtype=float) for k, v in series.items()})
    if se is not None: M = M / (np.sqrt(len(M)) * pd.Series({k: float(se[k]) for k in M.columns}))
    sm = StepM(np.zeros(len(M)), -M, size=size, block_size=block, reps=reps, bootstrap='stationary', studentize=True, seed=seed)
    sm.compute(); sup = set(sm.superior_models)
    return {'superior': [k for k in M.columns if k in sup], 'size': size, 'block': block, 'reps': reps, 'studentised': se is not None}

def romano_wolf_size(T: int, k: int, rho: float, block: int, nw_lags: int, nsim: int = 600, reps: int = 1000, seed: int = 0,
                     size: float = 0.05):
    """Simulated family-wise error rate of the studentised romano_wolf (D28: how the block length is chosen). Each draw:
    k independent AR(1) series of length T with autocorrelation rho and mean 0 (every null true), each studentised by
    its own full-sample Newey-West SE with nw_lags (tfs_stats.regression.fm_inference), then the stepdown at `size` with
    mean block `block` and `reps` replications. Returns the share of draws with at least one rejection. Independent
    series are the hardest case for FWER control (positively dependent series behave like fewer tests)."""
    from .regression import fm_inference
    rng = np.random.default_rng(seed); hits = 0
    for d in range(nsim):
        e = rng.normal(size=(T + 50, k)); x = np.empty_like(e); x[0] = e[0]
        for t in range(1, T + 50): x[t] = rho * x[t - 1] + e[t]
        x = x[50:]; se = fm_inference(x, nw_lags)['se']
        r = romano_wolf({f's{j}': x[:, j] for j in range(k)}, size=size, block=block, reps=reps, seed=seed * 100_000 + d,
                        se={f's{j}': se[j] for j in range(k)})
        hits += bool(r['superior'])
    return hits / nsim
