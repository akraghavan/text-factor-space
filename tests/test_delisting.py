"""SPEC §3 delisting imputation (src/delisting.py) on a synthetic fixture: only performance-related delistings with a
missing DelRet are imputed, by compounding delta onto MthRet; a present DelRet is never added again."""
import os, sys
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import delisting as D

def fixture():
    ym = pd.Period('2020-03', 'M')
    m = pd.DataFrame({'permno': [1, 2, 3, 4, 5, 6, 1], 'ym': [ym] * 6 + [ym - 1],
                      'ret': [-0.10, 0.05, -0.20, 0.02, np.nan, -0.05, 0.01], 'primaryexch': ['N', 'Q', 'N', 'N', 'A', 'R', 'N']})
    d = pd.DataFrame({'permno': [1, 2, 3, 4, 5, 6], 'delistingdt': pd.to_datetime(['2020-03-10'] * 6),
                      'delactiontype': ['GDR', 'GDR', 'GDR', 'GLI', 'GDR', 'GDR'], 'primaryexch': ['N', 'Q', 'N', 'N', 'A', 'R'],
                      'delret': [np.nan, np.nan, -0.40, np.nan, np.nan, np.nan], 'delretmisstype': ['DM', 'DP', None, 'DG', 'DM', 'DG']})
    d['ym'] = d.delistingdt.dt.to_period('M'); d['delret_missing'] = d.delret.isna() | d.delretmisstype.isin(D.MISSING_TYPES)
    d['performance'] = d.delactiontype.isin(D.PERFORMANCE)
    return m, d

def test_primary_rule():
    m, d = fixture()
    # permno 6 has exchange R in the delisting file and in the panel: no N/A/Q -> must raise, so give it a panel exchange
    m.loc[m.permno == 6, 'primaryexch'] = 'Q'
    out, st = D.adjust(m, d)
    r = out.set_index(['permno', 'ym']).ret; ym = pd.Period('2020-03', 'M')
    assert np.isclose(r[(1, ym)], 0.9 * 0.7 - 1)          # NYSE, missing, GDR: -30% compounded
    assert np.isclose(r[(2, ym)], 1.05 * 0.45 - 1)        # Nasdaq: -55%
    assert np.isclose(r[(3, ym)], -0.20)                  # DelRet present: already in MthRet, untouched
    assert np.isclose(r[(4, ym)], 0.02)                   # GLI (not performance-related): untouched
    assert np.isclose(r[(5, ym)], -0.30)                  # MthRet missing: taken as 0, then -30%
    assert np.isclose(r[(6, ym)], 0.95 * 0.45 - 1)        # exchange R in the file -> panel exchange Q -> -55%
    assert np.isclose(r[(1, ym - 1)], 0.01)               # other months untouched
    assert st['imputed_rows'] == 4 and st['missing_nonperformance_left'] == 1
    assert st['by_exchange_used'] == {'N': 1, 'Q': 2, 'A': 1}   # permno 1 N; 2 and 6 Q (6 via the R -> panel-exchange fallback); 5 A

def test_sensitivity_uniform_delta():
    m, d = fixture(); m.loc[m.permno == 6, 'primaryexch'] = 'Q'
    for delta in (0.0, -0.30, -1.0):
        out, _ = D.adjust(m, d, delta=delta); r = out.set_index(['permno', 'ym']).ret
        assert np.isclose(r[(2, pd.Period('2020-03', 'M'))], 1.05 * (1 + delta) - 1)
    out, _ = D.adjust(m, d, delta=0.0); assert np.allclose(out.ret.fillna(0), out.ret_raw.fillna(0))

def test_exit_month_rows_kept():
    """universe.add_exit_months: the month after the last universe month is kept (flagged), later months are not."""
    import universe as U
    ym = pd.period_range('2020-01', '2020-05', freq='M')
    raw = pd.DataFrame({'permno': [7] * 5 + [8] * 5, 'ym': list(ym) * 2, 'mthret': np.arange(10) / 100})
    members = raw[(raw.permno == 7) & (raw.ym <= ym[2]) | (raw.permno == 8)]      # 7 leaves after Mar 2020; 8 never leaves
    ex = U.add_exit_months(raw, members)
    assert list(zip(ex.permno, ex.ym)) == [(7, ym[3])] and not ex.in_universe.any()
