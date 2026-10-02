"""Element C, the two checks registered beside H1 (PREREG Element C "reported beside"; SPEC §7 Robustness 1 and 2).
Exploratory specs, each through src/runner.py and counted for BH. Same firms, outcome construction and controls as H1
(analysis/c_h1.py, src/c_panel.py, both unchanged); only the inference changes.

mrqap   C_x_mrqap   MRQAP-DSP (tfs_stats.pairs.mrqap_dsp) on annual July-June cross-sections, formations July 2012 ..
                    July 2024 (13 full years; Jul 2025 - Mar 2026 is not a full year and is left out). Firms: the top
                    1,000 at the July formation (c_month), restricted to firms with every firm-level control present
                    (B/M, momentum, daily Amihud, betas), so a relabelled firm always carries a complete row; a pair
                    still missing a pair-level value (z_lag, or the annual z) is left out of the regression and its
                    residual cell is 0. Outcome: Fisher z of the pair's daily FF6 residual correlation over the 12
                    months July..June (>= 126 common days, as z_lag); regressors: the H1 set with the dense similarity
                    (standardised over the year's sample), controls measured at the July formation. 999 relabellings
                    per year (seed = year). Pooled over years with the same draw index: T = sum_y t_y / sqrt(Y) for the
                    observed data and for each draw; p = (1 + #{T_b >= T}) / 1000 (one-sided, for BH; two-sided with
                    |T| beside it, SPEC §7).
dyadic  C_x_dyadic  pooled OLS over the 165 H1 months with month fixed effects (each month's y and X demeaned within the
                    month, which is OLS with month dummies by Frisch-Waugh-Lovell), dyadic-robust standard errors
                    (tfs_stats.pairs.DyadicMeat; firms are clusters across all months), t with G - 1 degrees of freedom.
                    Two passes over the months: slopes from the summed X'X and X'y, then the scores into the meat.
Writes analysis/output/c_pairs/. Aggregates only."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import c_panel as C, c_h1 as H
from tfs_stats.pairs import mrqap_dsp, DyadicMeat
from tfs_stats.regression import one_sided_p

OUT = ROOT / 'analysis' / 'output' / 'c_pairs'
CTRL = [c for c in H.X_COLS if c != 's_tilde']
YEARS = range(2012, 2025)

def _annual(y0):
    t = pd.Period(f'{y0}-07', 'M'); f, P = C.c_month(t)
    keep = (f.bm.notna() & f.mom.notna() & f.illiq.notna() & f.has_beta).to_numpy(); pos = np.full(len(f), -1); pos[keep] = np.arange(keep.sum())
    Z = C._fisher_z(C._resid(f.permno.to_numpy()[keep], t, t + 11), C.MIN_LAG_DAYS)
    i, j = pos[P.i.to_numpy()], pos[P.j.to_numpy()]; inn = (i >= 0) & (j >= 0)
    P = P[inn]; i, j = i[inn], j[inn]; P['z'] = Z[i, j]
    D = P[['z', 's_dense'] + CTRL].astype(np.float64).to_numpy(); ok = np.isfinite(D).all(1)
    D, i, j = D[ok], i[ok], j[ok]; s = (D[:, 1] - D[:, 1].mean()) / D[:, 1].std()
    return D[:, 0], s, np.column_stack([np.ones(len(D)), D[:, 2:]]), i, j, int(keep.sum()), int(len(f))

def mrqap(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); rows, tp = [], []
    for y0 in YEARS:
        y, s, X, i, j, n, n_all = _annual(y0); r = mrqap_dsp(y, s, X, i, j, n, n_perm=999, seed=y0); tp.append(r['t_perm'])
        rows.append({'year': f'{y0}/{(y0 + 1) % 100:02d}', 'firms': n, 'firms_top1000': n_all, 'pairs': len(y), 'b': r['b'], 't': r['t'],
                     'p_one_sided': r['p_one_sided'], 'max_t_perm': float(r['t_perm'].max())})
        print(rows[-1], f'{time.time() - t0:.0f}s', flush=True)
    R = pd.DataFrame(rows); Yn = len(R); T = R.t.sum() / np.sqrt(Yn); Tb = np.stack(tp).sum(0) / np.sqrt(Yn); B = len(Tb)
    res = {'pooled_T': float(T), 'p_one_sided': float((1 + np.sum(Tb >= T)) / (B + 1)), 'p_two_sided': float((1 + np.sum(np.abs(Tb) >= abs(T))) / (B + 1)),
           'mean_b': float(R.b.mean()), 'min_t_year': float(R.t.min()), 'max_t_perm_any_year': float(R.max_t_perm.max()),
           'years': Yn, 'years_p_le_001': int((R.p_one_sided <= 0.001).sum()), 'n_perm': B, 'seconds': round(time.time() - t0)}
    R.to_json(OUT / 'mrqap_years.json', orient='records', indent=1); (OUT / 'mrqap.json').write_text(json.dumps(res, indent=1)); print('mrqap', res)
    return res

def _month(t):
    f, P = C.c_month(t); D = P[['z', 's_dense'] + CTRL].astype(np.float64); ok = np.isfinite(D.to_numpy()).all(1)
    D = D[ok]; D['s_tilde'] = (D.s_dense - D.s_dense.mean()) / D.s_dense.std()
    X = D[H.X_COLS].to_numpy(); y = D.z.to_numpy(); perm = f.permno.to_numpy()
    return X - X.mean(0), y - y.mean(), perm[P.i.to_numpy()[ok]], perm[P.j.to_numpy()[ok]]

def dyadic(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); months = pd.period_range(H.FIRST, H.LAST, freq='M')
    k = len(H.X_COLS); XtX = np.zeros((k, k)); Xty = np.zeros(k); firms = set(); n = 0
    for t in months:                                                         # pass 1: pooled slopes (month FE)
        X, y, a, b = _month(t); XtX += X.T @ X; Xty += X.T @ y; firms.update(a); firms.update(b); n += len(y)
        if t.month == 1: print('pass 1', t, f'{time.time() - t0:.0f}s', flush=True)
    beta = np.linalg.solve(XtX, Xty); idx = pd.Index(sorted(firms)); M = DyadicMeat(len(idx), k)
    for t in months:                                                         # pass 2: scores into the dyadic meat
        X, y, a, b = _month(t); e = y - X @ beta
        M.add(X * e[:, None], idx.get_indexer(a), idx.get_indexer(b))
        if t.month == 1: print('pass 2', t, f'{time.time() - t0:.0f}s', flush=True)
    V, G = M.vcov(XtX, k_total=k + len(months)); se = np.sqrt(np.diag(V)); tt = beta / se
    res = {'b_pooled': float(beta[0]), 'se_dyadic': float(se[0]), 't_dyadic': float(tt[0]), 'df': G - 1,
           'p_one_sided': float(one_sided_p(tt[0], df=G - 1)), 'firms_G': G, 'pair_months': int(n), 'months': len(months),
           'coef': dict(zip(H.X_COLS, map(float, beta))), 't_all': dict(zip(H.X_COLS, map(float, tt))), 'seconds': round(time.time() - t0)}
    (OUT / 'dyadic.json').write_text(json.dumps(res, indent=1)); print('dyadic', {k_: v for k_, v in res.items() if k_ not in ('coef', 't_all')})
    return res
