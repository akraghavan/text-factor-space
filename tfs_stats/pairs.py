"""Inference for pair (dyadic) regressions, Element C's two checks beside Fama-MacBeth (SPEC §7, "Robustness 1 and 2";
PREREG Element C "reported beside"). Pair observations are dependent through shared firms: two pairs that share a firm
share that firm's shocks. Neither estimator exists in statsmodels / linearmodels, so both are written here on numpy:
  mrqap_dsp      MRQAP with double semi-partialling (Dekker, Krackhardt & Snijders 2007): a permutation test that
                 relabels firms, so it keeps every dependence a network has and breaks only the link between y and s
  DyadicMeat     the dyadic-robust ("two-way firm") sandwich meat (Aronow, Samii & Assenova 2015; Cameron & Miller 2014),
                 accumulated month by month because C's pooled panel (~73M pair-months) does not fit in memory at once
Tests: tests/test_pairs.py (statsmodels for the observed t, a null simulation for MRQAP's size, a brute-force double
sum for the dyadic meat). Card: docs/STATS_GUIDE.md#fn-pairs"""
import numpy as np

__all__ = ['mrqap_dsp', 'DyadicMeat']

def mrqap_dsp(y, s, C, i, j, n, n_perm: int = 999, seed: int = 0):
    """MRQAP-DSP test of the coefficient on s in the pair regression y = C gamma + b s + u.
    Inputs are pair vectors (one entry per pair i < j over firms 0..n-1, i and j the firm positions); C holds the
    controls including the constant. Steps:
      1. Residualise s on C (QR: numpy.linalg.qr, Q'Q = I): e_s = s - Q Q's; put it in an n x n symmetric matrix E
         (zero for pairs outside the sample, e.g. a pair with a missing control).
      2. Observed: regress y on [C, e_s]. By Frisch-Waugh-Lovell the coefficient on e_s is the OLS b on s in the full
         regression, and its classical OLS t is the same too.
      3. Each draw: relabel firms by a random permutation P (rows and columns together) and take v = E[P i, P j];
         regress y on [C, v] and record the classical OLS t. Only the part of s orthogonal to the controls moves, so
         collinearity between s and the controls (e.g. SIC) does not break the test (the point of DSP).
      Fast form, with r_y = y - Q Q'y and m = v'v - |Q'v|^2 = |M_C v|^2:
         b = v'r_y / m,  SSR = r_y'r_y - b^2 m,  t = b / sqrt(SSR / (N - k - 1) / m).
    The t (not b) is recorded because it is pivotal (Dekker et al.). p-values: one-sided (1 + #{t_b >= t}) / (B + 1)
    and two-sided (1 + #{|t_b| >= |t|}) / (B + 1) (SPEC §7). Returns dict(b, t, t_perm, p_one_sided, p_two_sided)."""
    y = np.asarray(y, dtype=np.float64); s = np.asarray(s, dtype=np.float64); C = np.asarray(C, dtype=np.float64)
    i = np.asarray(i); j = np.asarray(j); N, k = C.shape; df = N - k - 1
    Q, _ = np.linalg.qr(C)
    e_s = s - Q @ (Q.T @ s); r_y = y - Q @ (Q.T @ y); ryy = r_y @ r_y
    E = np.zeros((n, n)); E[i, j] = e_s; E[j, i] = e_s
    def t_of(v):
        m = v @ v - np.sum((Q.T @ v) ** 2); b = (v @ r_y) / m
        return b, b / np.sqrt((ryy - b * b * m) / df / m)
    b, t = t_of(e_s); rng = np.random.default_rng(seed); tp = np.empty(n_perm)
    for d in range(n_perm):
        p = rng.permutation(n); tp[d] = t_of(E[p[i], p[j]])[1]
    return {'b': float(b), 't': float(t), 't_perm': tp,
            'p_one_sided': (1 + np.sum(tp >= t)) / (n_perm + 1), 'p_two_sided': (1 + np.sum(np.abs(tp) >= abs(t))) / (n_perm + 1)}

class DyadicMeat:
    """Dyadic-robust meat for OLS on pair observations, accumulated in chunks (e.g. one month at a time).
    Two observations are treated as dependent when their pairs share at least one firm (any month: the firm is the
    cluster, so persistence over time is covered too). With score s_p = x_p e_p, inclusion-exclusion gives
        meat = sum_i g_i g_i' - sum_d h_d h_d',   g_i = sum of s_p over observations involving firm i,
                                                  h_d = sum of s_p over observations of dyad d (all months),
    because a pair of observations of the same dyad is counted twice in the first sum (once through each firm),
    and so is each observation with itself. vcov = c (X'X)^-1 meat (X'X)^-1 with c = G/(G-1) * n/(n-k) (SPEC §7;
    G = firms observed, n = observations, k = estimated coefficients); inference uses t with G - 1 degrees of freedom.
    Memory: the dyad sums are an (n_firms choose 2) x k float64 array (about 0.6 GB at 2,800 firms and k = 20)."""
    def __init__(self, n_firms: int, k: int):
        self.G0, self.k = int(n_firms), int(k)
        self.g = np.zeros((self.G0, self.k)); self.h = np.zeros((self.G0 * (self.G0 - 1) // 2, self.k))
        self.seen = np.zeros(self.G0, bool); self.n = 0
    def add(self, S, a, b):
        """S: scores x_p e_p (n_obs x k); a, b: firm indices of each observation's two firms (a != b)."""
        S = np.asarray(S, dtype=np.float64); a = np.asarray(a, dtype=np.int64); b = np.asarray(b, dtype=np.int64)
        lo, hi = np.minimum(a, b), np.maximum(a, b); G = self.G0
        d = lo * G - lo * (lo + 1) // 2 + (hi - lo - 1)                         # row of dyad (lo, hi) in the triangle
        u, inv = np.unique(d, return_inverse=True)
        for c in range(self.k):
            self.g[:, c] += np.bincount(a, S[:, c], G) + np.bincount(b, S[:, c], G)
            self.h[u, c] += np.bincount(inv, S[:, c], len(u))
        self.seen[a] = True; self.seen[b] = True; self.n += len(S)
    def meat(self):
        return self.g.T @ self.g - self.h.T @ self.h
    def vcov(self, XtX, k_total=None):
        """Sandwich with the bread (X'X)^-1; k_total = coefficients estimated (incl. absorbed fixed effects) for n/(n-k)."""
        G = int(self.seen.sum()); k = self.k if k_total is None else int(k_total)
        A = np.linalg.inv(np.asarray(XtX, dtype=np.float64))
        return G / (G - 1) * self.n / (self.n - k) * A @ self.meat() @ A, G
