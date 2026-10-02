"""Ken French short-term reversal factor, monthly: the "+STR" alpha in E's portfolio sorts (SPEC §9; PREREG Element E
pre-listed exploratory). File data/raw/F-F_ST_Reversal_Factor_CSV.zip, downloaded 2 Oct 2026 from the French data
library (docs/DATA.md §2). Same parsing convention as src/build_panel.py: percent -> decimal, monthly block only."""
import sys, os, zipfile; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW
import numpy as np, pandas as pd

def st_reversal_monthly() -> pd.Series:
    """ST_Rev in decimals, indexed by Period[M]; -99.99 / -999 (missing) become NaN."""
    z = zipfile.ZipFile(RAW / 'F-F_ST_Reversal_Factor_CSV.zip'); txt = z.read(z.namelist()[0]).decode('latin1').splitlines()
    rows, started = [], False
    for line in txt:
        p = [x.strip() for x in line.split(',')]
        if not started: started = len(p) > 1 and p[0] == '' and p[1] == 'ST_Rev'; continue
        if len(p) == 2 and p[0].isdigit() and len(p[0]) == 6: rows.append((pd.Period(f'{p[0][:4]}-{p[0][4:]}', 'M'), float(p[1])))
        elif rows: break                                                          # the annual block follows
    s = pd.Series([v for _, v in rows], index=pd.PeriodIndex([d for d, _ in rows]), name='ST_Rev')
    return (s.where(s > -99) / 100)
