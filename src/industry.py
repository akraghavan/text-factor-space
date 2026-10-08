"""Compustat historical SIC (`sich`) as the robustness industry code (PREREG "Industry codes", D14; SPEC D22, D23).
Point in time like book equity (formation.book_to_market): at formation month t, y = t.year if t.month >= 7 else
t.year - 1, and a firm's code is `sich` of its fiscal year ending in calendar year y - 1 (latest datadate in that year),
from data/raw/ccm_funda.parquet (already pulled from WRDS; no new query), primary links (linkprim P or C), keyed by
lpermno. Where `sich` is missing the CRSP `siccd` of month t-1 (the primary code) is kept, and the source is recorded.
with_sich(u, t) returns a copy of a universe frame with `sic` replaced and a `sic_source` column ('sich' / 'siccd')."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW
import numpy as np, pandas as pd

_cache = {}

def _sich_table():
    if 'sich' not in _cache:
        a = pd.read_parquet(RAW / 'ccm_funda.parquet', columns=['lpermno', 'linkprim', 'datadate', 'sich'])
        a = a[a.linkprim.isin(['P', 'C']) & a.sich.notna()].copy(); a['fy_cal'] = a.datadate.dt.year
        _cache['sich'] = a.sort_values('datadate').drop_duplicates(['lpermno', 'fy_cal'], keep='last')[['lpermno', 'fy_cal', 'sich']]
    return _cache['sich']

def sich_at(t) -> pd.Series:
    """`sich` usable at formation month t, indexed by permno."""
    t = pd.Period(t, 'M'); y = t.year if t.month >= 7 else t.year - 1
    a = _sich_table(); a = a[a.fy_cal == y - 1]
    return a.set_index('lpermno').sich.astype(float)

def with_sich(u, t):
    s = sich_at(t).reindex(u.permno.to_numpy()).to_numpy(); u = u.copy()
    u['sic_source'] = np.where(np.isfinite(s), 'sich', 'siccd'); u['sic'] = np.where(np.isfinite(s), s, u.sic.to_numpy(dtype=float))
    return u
