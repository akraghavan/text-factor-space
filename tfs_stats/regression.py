"""Regression + inference, written by hand. Each function has a test in tests/test_regression.py
that checks it against statsmodels. Numpy only (np.linalg.qr is allowed; np.linalg.lstsq/inv are not)."""
import numpy as np

def ols_qr(X: np.ndarray, y: np.ndarray):
    """OLS via thin QR: X = QR, beta = R^{-1} Q'y (solve the triangular system by back-substitution).
    Returns (beta [k], resid [n]). Why QR and not (X'X)^{-1}X'y: cond(X'X) = cond(X)^2."""
    raise NotImplementedError

def vcov(X: np.ndarray, resid: np.ndarray, kind: str = "classical", groups=None, lags: int | None = None):
    """Covariance matrix of beta_hat.
    kind='classical' : s^2 (X'X)^{-1},            s^2 = e'e/(n-k)
    kind='HC1'       : n/(n-k) * (X'X)^{-1} (sum e_i^2 x_i x_i') (X'X)^{-1}
    kind='cluster'   : G/(G-1) * (n-1)/(n-k) * (X'X)^{-1} (sum_g u_g u_g') (X'X)^{-1},  u_g = sum_{i in g} x_i e_i
    kind='NW'        : Newey-West with Bartlett weights w_l = 1 - l/(L+1):
                       S = G_0 + sum_{l=1}^{L} w_l (G_l + G_l'),  G_l = sum_t e_t e_{t-l} x_t x_{t-l}'
                       V = (X'X)^{-1} S (X'X)^{-1}   (no small-sample factor; matches statsmodels 'HAC' with use_correction=False)"""
    raise NotImplementedError

def fama_macbeth(y: np.ndarray, X: np.ndarray, t: np.ndarray, nw_lags: int = 0):
    """Cross-sectional OLS of y on [1, X] each period t, then time-series mean of the slopes.
    SE = NW (lags=nw_lags) standard error of the mean of the slope series.
    Returns dict(coef=[k+1], se=[k+1], tstat=[k+1], lambdas=[T x (k+1)])."""
    raise NotImplementedError
