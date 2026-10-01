"""H1 (confirmatory; specs.yaml C_H1_dense_bbar; PREREG Element C, frozen at d1df5c7). Run only via
    python src/runner.py run C_H1_dense_bbar
Each formation month t = Jul 2012 .. Mar 2026: the 1,000 largest universe firms at t-1 and their 499,500 pairs
(src/c_panel.c_month). Monthly cross-sectional OLS of z_ij,t (Fisher z of the within-month FF6 residual correlation)
on [1, s~, z_lag, same SIC-1..4, d_size, d_bm, d_mom, |dbeta_k| x 6, d_illiq (daily Amihud), same FYE month,
len_sum, len_diff, same exchange]; s~ = the dense similarity standardised within the month over that month's
regression sample (pairs with every variable present; the rest are dropped, PREREG D14). The month's X'X and X'y are
accumulated and the slopes come from tfs_stats.regression.fm_from_moments (the stacked panel is ~80M rows).
Primary statistic: b-bar on s~ with its Newey-West t (L = 4, x T/(T-1)), one-sided p (normal). Reported beside it:
EWC(12) t with t_12, the lag-1 autocorrelation of b_t, per-month coverage and condition numbers.
Writes analysis/output/c_h1/README.md (aggregates only) and returns the summary the runner logs."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
import formation as F, c_panel as C
from tfs_stats.regression import fm_from_moments, ewc, nw_lags_rule, ewc_nu_rule, one_sided_p

OUT = ROOT / 'analysis' / 'output' / 'c_h1'
FIRST, LAST = '2012-07', '2026-03'
X_COLS = ['s_tilde', 'z_lag', 'same_sic1', 'same_sic2', 'same_sic3', 'same_sic4', 'd_me', 'd_bm', 'd_mom'] + \
         [f'db_{f}' for f in F.FACTORS] + ['d_illiq', 'same_fye', 'len_sum', 'len_diff', 'same_exch']

def month_moments(t):
    f, P = C.c_month(t)
    D = P[['z', 's_dense'] + [c for c in X_COLS if c != 's_tilde']].astype(np.float64)
    D = D[np.isfinite(D.to_numpy()).all(1)]
    s = D.s_dense; D['s_tilde'] = (s - s.mean()) / s.std()
    X = np.column_stack([np.ones(len(D)), D[X_COLS].to_numpy()]); y = D.z.to_numpy()
    return X.T @ X, X.T @ y, len(D), len(P)

def run(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    months = pd.period_range(FIRST, LAST, freq='M'); XtX, Xty, n, npairs = [], [], [], []
    for t in months:
        a, b, k, m = month_moments(t); XtX.append(a); Xty.append(b); n.append(k); npairs.append(m)
        if t.month == 1: print(t, k, f'{time.time() - t0:.0f}s', flush=True)
    T = len(months); L = nw_lags_rule(T); nu = ewc_nu_rule(T)
    r = fm_from_moments(np.stack(XtX), np.stack(Xty), np.array(n), nw_lags=L)
    b = r['lambdas'][:, 1]; ew = ewc(b, nu)
    names = ['const'] + X_COLS
    res = {'b_bar': float(r['coef'][1]), 'se_nw': float(r['se'][1]), 't_nw': float(r['tstat'][1]), 'nw_lags': L,
           'p_one_sided': float(one_sided_p(r['tstat'][1])), 't_ewc': float(ew['tstat']), 'ewc_nu': nu,
           'p_ewc_one_sided': float(one_sided_p(ew['tstat'], df=nu)), 'b_autocorr_lag1': float(np.corrcoef(b[1:], b[:-1])[0, 1]),
           'months': int(r['T']), 'months_skipped': int(r['n_skipped']), 'median_pairs_used': int(np.median(n)),
           'share_pairs_used': float(np.sum(n) / np.sum(npairs)), 'max_cond_XtX': float(np.max(r['cond']))}
    tab = pd.DataFrame({'mean slope': r['coef'], f'NW({L}) t': r['tstat']}, index=names).round(4)
    md = lambda df: '\n'.join(['| | ' + ' | '.join(df.columns) + ' |', '|---|' + '---|' * df.shape[1]] +
                              [f'| {i} | ' + ' | '.join(str(v) for v in row) + ' |' for i, row in zip(df.index, df.itertuples(index=False))])
    txt = ['# H1 (Element C): text similarity and residual comovement — confirmatory', '',
           'Spec `C_H1_dense_bbar`, PREREG frozen at d1df5c7, run through `src/runner.py`.', '',
           f"**b̄ (dense s̃) = {res['b_bar']:.4f}** per SD of similarity, NW({L}) SE {res['se_nw']:.4f}, **t = {res['t_nw']:.2f}**, "
           f"one-sided p = {res['p_one_sided']:.2e}. Beside it: EWC({nu}) t = {res['t_ewc']:.2f} (one-sided p from t_{nu} = {res['p_ewc_one_sided']:.2e}); "
           f"lag-1 autocorrelation of b_t = {res['b_autocorr_lag1']:.2f}.", '',
           f"{res['months']} months (skipped {res['months_skipped']}); median {res['median_pairs_used']:,} pairs a month in the regression "
           f"({res['share_pairs_used']:.1%} of all pairs); max condition number of X'X {res['max_cond_XtX']:.1e}.", '',
           '## All mean slopes (Fama–MacBeth)', '', md(tab), '', f'Runtime {time.time() - t0:.0f} s.']
    (OUT / 'README.md').write_text('\n'.join(txt) + '\n'); print('\n'.join(txt))
    pd.DataFrame(r['lambdas'], columns=names, index=months.astype(str)).to_csv(OUT / 'lambdas.csv')   # gitignored (*.csv)
    return res

if __name__ == '__main__':
    run()
