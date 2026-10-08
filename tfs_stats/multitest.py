"""Multiple-testing corrections (SPEC §10.2-10.3; PREREG "Confirmatory family"): the project's estimator layer (D13).
Library call: statsmodels.stats.multitest.multipletests. Card: docs/STATS_GUIDE.md#fn-multitest"""
import numpy as np
from statsmodels.stats.multitest import multipletests

__all__ = ['holm', 'bh', 'by', 'fisher_combine', 'romano_wolf']

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

def romano_wolf(series, size: float = 0.05, block: int = 4, reps: int = 10_000, seed: int = 2026):
    """Romano-Wolf stepdown across slope series (PREREG multiple testing; D25): which mean slopes are significantly
    positive, controlling the family-wise error rate under any dependence between the series. Library call:
    arch.bootstrap.StepM (Romano & Wolf 2005 stepdown built on Hansen's SPA bootstrap): benchmark loss 0, model losses
    -b_t (so "superior" = mean slope > 0), stationary bootstrap of the common months with mean block length `block`,
    `reps` replications, seed fixed, Hansen's "consistent" re-centring. studentize=True is passed as D25 specifies, but in
    arch 8.0.0 the flag only labels the output: the max statistic and its bootstrap critical values use the raw mean
    slopes (the variances serve only the re-centring screen), so this is the non-studentised stepdown. Simulated FWER at
    size 0.05 (tests/test_romano_wolf.py and the card): about 6.5% with iid series at our shapes (T = 165, 8 series;
    T = 91, 15 series); 8.5% and 11% when every series is AR(1) with rho = 0.2, because a mean block of 4 understates
    that persistence. Every series must cover the same months. series: {name: 1-d array}.
    Returns dict(superior: names in input order, size, block, reps)."""
    import pandas as pd
    from arch.bootstrap import StepM
    M = pd.DataFrame({k: np.asarray(v, dtype=float) for k, v in series.items()})
    sm = StepM(np.zeros(len(M)), -M, size=size, block_size=block, reps=reps, bootstrap='stationary', studentize=True, seed=seed)
    sm.compute(); sup = set(sm.superior_models)
    return {'superior': [k for k in M.columns if k in sup], 'size': size, 'block': block, 'reps': reps}
