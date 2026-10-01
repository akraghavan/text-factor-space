"""Multiple-testing corrections (SPEC §10.2-10.3; PREREG "Confirmatory family"): the project's estimator layer (D13).
Library call: statsmodels.stats.multitest.multipletests. Card: docs/STATS_GUIDE.md#fn-multitest"""
import numpy as np
from statsmodels.stats.multitest import multipletests

__all__ = ['holm', 'bh', 'by']

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
