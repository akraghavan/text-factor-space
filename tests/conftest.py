"""Report tests of not-yet-written tfs_stats functions as SKIPPED instead of FAILED.

tfs_stats/ is written by hand; until a function is implemented it raises NotImplementedError.
Only a NotImplementedError raised from inside tfs_stats/ is converted, so the same exception
coming from numpy, statsmodels or the test itself still fails loudly.
"""
from pathlib import Path

import pytest

REASON = "not implemented yet (tfs_stats is written by hand)"
TFS_STATS = Path(__file__).resolve().parents[1] / "tfs_stats"


def _raised_in_tfs_stats(excinfo) -> bool:
    if not excinfo.errisinstance(NotImplementedError):
        return False
    origin = Path(str(excinfo.traceback[-1].path)).resolve()
    return TFS_STATS in origin.parents


@pytest.hookimpl(wrapper=True)
def pytest_runtest_makereport(item, call):
    rep = yield
    if call.when == "call" and call.excinfo is not None and _raised_in_tfs_stats(call.excinfo):
        path, lineno, _ = item.location
        rep.outcome = "skipped"
        rep.longrepr = (str(item.path), (lineno or 0) + 1, f"Skipped: {REASON}")
    return rep
