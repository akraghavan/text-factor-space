"""OLS by hand: Abhi's practice exercise (CLAUDE.md rule 2, practice exception). Stubs only; Abhi writes the bodies.
Claude tutors here and never fills these in (hints on request: H1 the idea, H2 the next step, H3 the line with the bug).
Nothing in src/, analysis/ or tfs_stats/ imports this module. Cards: docs/STATS_GUIDE.md#stats-practice
Run the tests with:  python -m pytest -q practice/"""
import numpy as np


def ols_1d_no_intercept(x: np.ndarray, y: np.ndarray) -> float:
    """Step 1 (#fn-practice-1d): beta minimising sum_i (y_i - beta x_i)^2, one regressor, no intercept.
    Raise ValueError if beta is not identified."""
    raise NotImplementedError


def back_substitute(R: np.ndarray, c: np.ndarray) -> np.ndarray:
    """Step 2 (#fn-practice-qr): solve R b = c for upper-triangular R (k x k) with a loop, last row first.
    No np.linalg.solve / inv / lstsq / scipy here."""
    raise NotImplementedError


def ols_qr_by_hand(X: np.ndarray, y: np.ndarray):
    """Step 2 (#fn-practice-qr): OLS via np.linalg.qr and your back_substitute. Returns (beta [k], resid [n])."""
    raise NotImplementedError


class StreamingOLS:
    """Step 3 (#fn-practice-stream): OLS from rows that arrive one at a time or in blocks and are not stored.
    Memory O(k^2), each update O(k^2) per row, independent of n."""

    def __init__(self, k: int):
        raise NotImplementedError

    def update(self, X: np.ndarray, y: np.ndarray) -> None:
        """Absorb one row (X shape (k,), y scalar) or a block (X (m, k), y (m,))."""
        raise NotImplementedError

    def coef(self) -> np.ndarray:
        """Current OLS coefficients [k]."""
        raise NotImplementedError

    def sigma2(self) -> float:
        """Current residual variance e'e / (n - k), without storing residuals."""
        raise NotImplementedError


class RLS:
    """Step 4 (#fn-practice-rls): recursive least squares with forgetting factor lam (1.0 = no forgetting) and prior
    P0 = delta * I. Attribute `beta` holds the current coefficients after each update."""

    def __init__(self, k: int, lam: float = 1.0, delta: float = 1e6):
        raise NotImplementedError

    def update(self, x: np.ndarray, y: float) -> None:
        """Absorb one row x (k,) with response y."""
        raise NotImplementedError
