"""Testing whether one portfolio's out-of-sample variance is lower than another's (Element D; SPEC §8; PREREG
Element D; D20(g)). Ledoit & Wolf (2011, Wilmott), "Robust performance hypothesis testing with the variance".
  log_var_diff       Delta = log var(r_A) - log var(r_B) with the delta-method standard error from a prewhitened
                     Quadratic-Spectral HAC estimate (arch.covariance.kernel.QuadraticSpectral) of the long-run
                     covariance of y_t = (r_A, r_B, r_A^2, r_B^2)
  log_var_diff_boot  the studentised circular block bootstrap beside it (arch.bootstrap.CircularBlockBootstrap)
Tests: tests/test_varcompare.py (size under a GARCH null, recovery of a known Delta). Card: docs/STATS_GUIDE.md#fn-var_test"""
import numpy as np
from scipy import stats
from arch.covariance.kernel import QuadraticSpectral
from arch.bootstrap import CircularBlockBootstrap

__all__ = ['log_var_diff', 'log_var_diff_boot', 'hac_prewhitened', 'andrews_bandwidth']

def andrews_bandwidth(e):
    """Andrews (1991) AR(1) plug-in bandwidth for the QS kernel: fit an AR(1) to each column of e (standardised, so
    every moment counts equally), alpha(2) = sum 4 rho^2 s^4 / (1 - rho)^8 / sum s^4 / (1 - rho)^4 with s^2 the AR(1)
    innovation variance, bandwidth = 1.3221 (alpha(2) T)^{1/5}. arch's own automatic choice is the Newey-West (1994)
    nonparametric plug-in, so the bandwidth is computed here and passed to arch."""
    e = np.asarray(e, dtype=np.float64); e = (e - e.mean(0)) / e.std(0); T = len(e); num = den = 0.0
    for a in range(e.shape[1]):
        x0, x1 = e[:-1, a], e[1:, a]; rho = float(x0 @ x1 / (x0 @ x0)); rho = np.clip(rho, -0.97, 0.97)
        s2 = float(np.mean((x1 - rho * x0) ** 2))
        num += 4 * rho ** 2 * s2 ** 2 / (1 - rho) ** 8; den += s2 ** 2 / (1 - rho) ** 4
    return float(1.3221 * (num / den * T) ** 0.2)

def hac_prewhitened(y):
    """Long-run covariance of the rows of y (T x k) by VAR(1) prewhitening + QS kernel + recolouring (Andrews &
    Monahan 1992): A = OLS of y_t on y_{t-1} (demeaned, no intercept); e_t = y_t - A y_{t-1}; Psi* = QS kernel HAC of e
    (arch, Andrews bandwidth, divided by T); Psi = (I - A)^{-1} Psi* (I - A)^{-T}. Returns (Psi, bandwidth)."""
    y = np.asarray(y, dtype=np.float64); yc = y - y.mean(0)
    A = np.linalg.lstsq(yc[:-1], yc[1:], rcond=None)[0].T; e = yc[1:] - yc[:-1] @ A.T
    bw = andrews_bandwidth(e); P = QuadraticSpectral(e, bandwidth=bw, center=True).cov.long_run
    M = np.linalg.inv(np.eye(len(A)) - A); return M @ P @ M.T, bw

def log_var_diff(rA, rB):
    """Delta = log s_A^2 - log s_B^2 (plug-in variances) and its LW (2011) standard error. With means (a, b, c, d) of
    y_t = (r_A, r_B, r_A^2, r_B^2), Delta = f = log(c - a^2) - log(d - b^2), gradient
    (-2a/(c - a^2), 2b/(d - b^2), 1/(c - a^2), -1/(d - b^2)); SE = sqrt(grad' Psi grad / T) with Psi = hac_prewhitened(y).
    One-sided p for Delta < 0 (A has the lower variance) from the normal: Phi(Delta / SE). Returns dict(delta, se, t,
    p_one_sided, p_two_sided, ci95, ratio_sd = exp(Delta / 2), bandwidth, T)."""
    rA, rB = np.asarray(rA, dtype=np.float64), np.asarray(rB, dtype=np.float64)
    y = np.column_stack([rA, rB, rA ** 2, rB ** 2]); T = len(y); a, b, c, d = y.mean(0); vA, vB = c - a * a, d - b * b
    delta = float(np.log(vA) - np.log(vB)); g = np.array([-2 * a / vA, 2 * b / vB, 1 / vA, -1 / vB])
    Psi, bw = hac_prewhitened(y); se = float(np.sqrt(g @ Psi @ g / T)); t = delta / se
    return {'delta': delta, 'se': se, 't': t, 'p_one_sided': float(stats.norm.cdf(t)), 'p_two_sided': float(2 * stats.norm.sf(abs(t))),
            'ci95': [delta - 1.96 * se, delta + 1.96 * se], 'ratio_sd': float(np.exp(delta / 2)), 'bandwidth': bw, 'T': T}

def log_var_diff_boot(rA, rB, block: int = 21, B: int = 2000, seed: int = 2026):
    """Studentised circular block bootstrap of Delta (LW 2011 section 3.2 logic; arch.bootstrap.CircularBlockBootstrap,
    block length 21 days). Each resample keeps the pairs (r_At, r_Bt) together, recomputes Delta* and its HAC SE*, and
    t*_b = (Delta*_b - Delta) / SE*_b. One-sided p for Delta < 0: (1 + #{t*_b <= t}) / (B + 1), t = Delta / SE.
    Returns dict(p_one_sided, t, B, block)."""
    base = log_var_diff(rA, rB); bs = CircularBlockBootstrap(block, np.asarray(rA, float), np.asarray(rB, float), seed=seed); ts = []
    for (a, b), _ in bs.bootstrap(B):
        r = log_var_diff(a, b); ts.append((r['delta'] - base['delta']) / r['se'])
    ts = np.array(ts)
    return {'p_one_sided': float((1 + np.sum(ts <= base['t'])) / (B + 1)), 't': base['t'], 'B': B, 'block': block}
