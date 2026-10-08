"""H3 (confirmatory; specs.yaml E_H3_bow_peermom_test; PREREG Element E, frozen at 01cb5cc). Run only via
    python src/runner.py run E_H3_bow_peermom_test
Monthly formation t; src/e_signals.signals_at(t) (peers: BoW nouns, null-corrected, SIC-3 density; price >= $1; >= 1
peer); monthly returns with the SPEC §3 delisting imputation (src/delisting.adjust, exchange-specific delta) and
exit-month returns kept. Dependent: month-t return minus the FF risk-free rate. Right-hand side, winsorised at 1/99
and z-scored each month: PEERMOM, log ME, log B/M, r_{t-1}, R(t-12, t-2), VW FF-48 industry momentum, SIC-3 peer
momentum, TNIC-3 peer momentum (FY2023 carried forward for Jul 2025 - Jun 2026, flagged).
Primary statistic: the test-period (Dec 2018 - Jun 2026, T = 91) Fama-MacBeth mean slope on PEERMOM, Newey-West t
with L = nw_lags_rule(91) = 3 (x T/(T-1)), one-sided p (normal). Reported beside it: NW(2), EWC(8) with t_8, the
Harvey-Liu-Zhu t > 3 hurdle, the full-sample slope (Jul 2012 - Jun 2026) and the test-minus-development difference
(independent periods: SE = sqrt(SE_test^2 + SE_dev^2)). Writes analysis/output/e_h3/README.md; returns the summary."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
import formation as F, delisting
from paths import PROCESSED
from tfs_stats.regression import fama_macbeth, fm_inference, ewc, nw_lags_rule, ewc_nu_rule, one_sided_p

OUT = ROOT / 'analysis' / 'output' / 'e_h3'
DEV = (pd.Period('2012-07', 'M'), pd.Period('2018-11', 'M')); TEST = (pd.Period('2018-12', 'M'), pd.Period('2026-06', 'M'))
RHS = ['peermom', 'log_me', 'log_bm', 'r_1', 'r12_2', 'indmom', 'sic3mom', 'tnicmom']

def zwin(s):
    lo, hi = s.quantile([0.01, 0.99]); s = s.clip(lo, hi); return (s - s.mean()) / s.std()

def panel(first, last):
    import e_signals as E
    ffm = pd.read_parquet(PROCESSED / 'ff_monthly.parquet').set_index('ym'); rows = []
    for t in pd.period_range(first, last, freq='M'):
        u = E.signals_at(t)
        u['exret'] = F.monthly()[F.monthly().ym == t].set_index('permno').ret.reindex(u.permno).to_numpy() - ffm.RF.loc[t]
        rows.append(u)
    P = pd.concat(rows, ignore_index=True); d = P.dropna(subset=['exret'] + RHS).copy()
    for c in RHS: d[c] = d.groupby('t')[c].transform(zwin)
    return P, d

def fm(d, lags):
    return fama_macbeth(d.exret.to_numpy(), d[RHS].to_numpy(), d.t.astype(str).to_numpy(), nw_lags=lags)

def run(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    F._cache['m'], dstats = delisting.adjust(F.monthly())
    P, d = panel(DEV[0], TEST[1])
    dt, dd = d[d.t >= TEST[0]], d[d.t <= DEV[1]]
    Tt = dt.t.nunique(); L = nw_lags_rule(Tt); nu = ewc_nu_rule(Tt)
    rt = fm(dt, L); rd = fm(dd, nw_lags_rule(dd.t.nunique())); rf = fm(d, nw_lags_rule(d.t.nunique()))
    b = rt['lambdas'][:, 1]; nw2 = fm_inference(rt['lambdas'], 2); ew = ewc(b, nu)
    diff = rt['coef'][1] - rd['coef'][1]; se_diff = np.hypot(rt['se'][1], rd['se'][1])
    res = {'slope_test': float(rt['coef'][1]), 'se_nw': float(rt['se'][1]), 't_nw': float(rt['tstat'][1]), 'nw_lags': L,
           'p_one_sided': float(one_sided_p(rt['tstat'][1])), 't_nw2': float(nw2['tstat'][1]), 't_ewc': float(ew['tstat']), 'ewc_nu': nu,
           'p_ewc_one_sided': float(one_sided_p(ew['tstat'], df=nu)), 'hlz_t_gt_3': bool(rt['tstat'][1] > 3),
           'slope_dev': float(rd['coef'][1]), 't_dev': float(rd['tstat'][1]), 'slope_full': float(rf['coef'][1]), 't_full': float(rf['tstat'][1]),
           'test_minus_dev': float(diff), 't_test_minus_dev': float(diff / se_diff), 'months_test': int(Tt), 'months_skipped': int(rt['n_skipped']),
           'firm_months_test': int(len(dt)), 'carried_tnic_months': int(dt[dt.tnic_carried.astype(bool)].t.nunique()),
           'delisting_imputed_rows_panel': dstats['imputed_rows']}
    names = ['const'] + RHS
    tab = pd.DataFrame({'coef (%/month per SD)': np.round(rt['coef'] * 100, 3), f'NW({L}) t': np.round(rt['tstat'], 2),
                        'NW(2) t': np.round(nw2['tstat'], 2), f'EWC({nu}) t': np.round(ewc(rt['lambdas'], nu)['tstat'], 2)}, index=names)
    md = lambda df: '\n'.join(['| | ' + ' | '.join(df.columns) + ' |', '|---|' + '---|' * df.shape[1]] +
                              [f'| {i} | ' + ' | '.join(str(v) for v in row) + ' |' for i, row in zip(df.index, df.itertuples(index=False))])
    txt = ['# H3 (Element E): text-peer momentum out of sample — confirmatory', '',
           'Spec `E_H3_bow_peermom_test`, PREREG frozen at 01cb5cc, run through `src/runner.py`.', '',
           f"**Test period (Dec 2018 – Jun 2026, T = {Tt}): PEERMOM slope = {res['slope_test'] * 100:.3f}%/month per SD, NW({L}) t = {res['t_nw']:.2f}, "
           f"one-sided p = {res['p_one_sided']:.3g}.** Beside it: NW(2) t = {res['t_nw2']:.2f}; EWC({nu}) t = {res['t_ewc']:.2f} "
           f"(one-sided p from t_{nu} = {res['p_ewc_one_sided']:.3g}); Harvey–Liu–Zhu t > 3: {'yes' if res['hlz_t_gt_3'] else 'no'}.", '',
           f"Development (Jul 2012 – Nov 2018): {res['slope_dev'] * 100:.3f}%/month (t = {res['t_dev']:.2f}). Full sample: {res['slope_full'] * 100:.3f}%/month "
           f"(t = {res['t_full']:.2f}). Test − development: {res['test_minus_dev'] * 100:.3f}%/month (t = {res['t_test_minus_dev']:.2f}).", '',
           f"{res['firm_months_test']:,} test firm-months with every variable; {res['carried_tnic_months']} months use the carried-forward FY2023 TNIC network; "
           f"delisting imputation applied to {res['delisting_imputed_rows_panel']} panel rows (13 E firm-months, PREREG).", '',
           '## Test-period mean slopes', '', md(tab), '', f'Runtime {time.time() - t0:.0f} s.']
    (OUT / 'README.md').write_text('\n'.join(txt) + '\n'); print('\n'.join(txt))
    return res

if __name__ == '__main__':
    run()
