"""Tests for Abhi's OLS-by-hand practice (practice/ols_by_hand.py). Not collected by CI (pyproject testpaths = tests);
run with:  python -m pytest -q practice/   Each test says what it checks; none says how to implement it."""
import os, sys
import numpy as np
import pytest
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ols_by_hand import ols_1d_no_intercept, back_substitute, ols_qr_by_hand, StreamingOLS, RLS

rng = np.random.default_rng(0)
n, k = 500, 4
X = np.column_stack([np.ones(n), rng.normal(size=(n, k - 1))])
y = X @ np.array([0.5, 1.0, -2.0, 0.0]) + rng.normal(size=n)
REF = np.linalg.lstsq(X, y, rcond=None)[0]


def test_1d():
    x = rng.normal(size=200); yy = 1.7 * x + rng.normal(size=200)
    assert np.isclose(ols_1d_no_intercept(x, yy), np.linalg.lstsq(x[:, None], yy, rcond=None)[0][0])


def test_1d_not_identified():
    with pytest.raises(ValueError):
        ols_1d_no_intercept(np.zeros(5), np.ones(5))


def test_back_substitute():
    R = np.triu(rng.normal(size=(6, 6))) + 5 * np.eye(6); c = rng.normal(size=6)
    assert np.allclose(R @ back_substitute(R, c), c)


def test_batch_qr():
    b, e = ols_qr_by_hand(X, y)
    assert np.allclose(b, REF) and np.allclose(e, y - X @ REF)


def test_batch_qr_ill_conditioned():
    # cond(X) ~ 1e7: QR must stay within rtol 1e-6 of lstsq (the normal equations typically do not)
    t = np.linspace(0, 1, n); Z = np.column_stack([np.ones(n), t, t + 1e-7 * rng.normal(size=n)])
    yy = Z @ np.array([1., 2., 3.]) + 1e-9 * rng.normal(size=n)
    b, _ = ols_qr_by_hand(Z, yy)
    assert np.allclose(b, np.linalg.lstsq(Z, yy, rcond=None)[0], rtol=1e-6)


def test_streaming_row_by_row_equals_blocks_equals_batch():
    s1, s2 = StreamingOLS(k), StreamingOLS(k)
    for i in range(n): s1.update(X[i], y[i])
    for a in range(0, n, 37): s2.update(X[a:a + 37], y[a:a + 37])
    assert np.allclose(s1.coef(), REF) and np.allclose(s2.coef(), REF)


def test_streaming_sigma2():
    s = StreamingOLS(k); s.update(X, y)
    e = y - X @ REF
    assert np.isclose(s.sigma2(), e @ e / (n - k))


def test_rls_matches_batch():
    r = RLS(k, lam=1.0, delta=1e6)
    for i in range(n): r.update(X[i], y[i])
    assert np.allclose(r.beta, REF, atol=1e-6)
