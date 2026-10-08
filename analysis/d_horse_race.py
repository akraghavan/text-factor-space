"""Element D, the covariance horse race (SPEC §8; PREREG Element D; D20, D21). Out of sample, every 21 trading days
from July 2012 (src/d_panel.py), each estimator gives a correlation matrix R^ on the T-day estimation window;
Sigma^ = D^{1/2} R^ D^{1/2} with D the window's sample variances; unconstrained GMV weights
(tfs_stats.rmt.min_var_weights) held for 21 days; the portfolio's daily returns are recorded.
Estimators (D20(a); tfs_stats.covariance unless stated):
  ew           1/N (no estimator)
  sample       sample correlation (only when N < T)
  lw_identity  sklearn LedoitWolf on standardised returns, rescaled to unit diagonal
  constcorr    T(a, 0), a fitted on the pre-window, Schaefer-Strimmer intensity (the "b = 0" target)
  clip         RMT eigenvalue clipping (tfs_stats.rmt.clip_correlation; q > 1 path when N > T)
  lwnl         LW (2020) analytical nonlinear shrinkage of the standardised returns, unit diagonal: the BENCHMARK
  industry     T_ind(a, b), B = same SIC-3 blocks
  text         T(a, b) with G = dense similarity: the PRIMARY text estimator
  bow_raw      T(a, b) with G = raw BoW cosine Gram
  text_val     the dense target with the 63-day validated intensity: delta on a 0.05 grid minimising the GMV variance
               over the window's last 63 days, R and D from its first T - 63 days, then applied to the full window
  precond      text-preconditioned nonlinear shrinkage with the fitted dense target (LW 2017 eq. 16)
  ff6          FF6 factor model, diagonal residuals
  ff6_text     FF6 factor model + residual correlation shrunk to a dense target fitted on pre-window FF6 residuals
  pca5         5-factor PCA model, diagonal residuals
  placebo      T(a, b) with G replaced by P G P' (P a random permutation, seed = rebalance index), (a, b) refitted
(a, b): constrained LS of the pre-window pair correlations (>= 200 common days) on g_ij (D20(b)); delta:
Schaefer-Strimmer eq. 8 (D20(c)).
Configurations: primary N = 500, T = 252; robustness N = 1,000, T = 252 and N = 500, T = 504 (D20(h)). Each is computed
once and cached in data/processed/d_oos_<config>_<code hash>.parquet (daily returns) and d_reb_<...>.parquet
(per-rebalance predicted variance, weights summaries, fitted a, b, delta), gitignored; the hash covers the code that
produces them, so a code change forces a rebuild.
Entries: text_vs_lwnl (D_x_text_vs_lwnl, pre-listed), text_vs_constcorr and text_vs_placebo (D21, post-freeze), each a
test-period Delta log variance with the LW (2011) HAC t (tfs_stats.varcompare), one-sided p for Delta < 0, and the
studentised circular block bootstrap p beside it; table (D_horse_race_table, diagnostic): every estimator against LW-NL
in development, test and full periods for each configuration, Holm across estimators, and the metrics of D20(i).
Writes analysis/output/d_horse_race/. Aggregates only."""
import sys, time, json, hashlib
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import d_panel as DP
from paths import PROCESSED
from tfs_stats.covariance import (lw_nonlinear, nested_target, fit_target_ab, ss_intensity, shrink, precondition_nl, factor_fit,
                                  factor_corr, to_corr, standardise)
from tfs_stats.rmt import clip_correlation, min_var_weights, ledoit_wolf
from tfs_stats.varcompare import log_var_diff, log_var_diff_boot
from tfs_stats.multitest import holm

OUT = ROOT / 'analysis' / 'output' / 'd_horse_race'
CONFIGS = {'primary': (500, 252), 'n1000': (1000, 252), 't504': (500, 504)}
ESTIMATORS = ['ew', 'sample', 'lw_identity', 'constcorr', 'clip', 'lwnl', 'industry', 'text', 'bow_raw', 'text_val', 'precond',
              'ff6', 'ff6_text', 'pca5', 'placebo']
GRID = np.round(np.arange(0, 1.0001, 0.05), 2); VAL = 63

def _code_hash():
    """Hash of the code that produces the cached returns (the panel, the estimator layer, and this module's computing
    functions and constants), so a change to any of them forces a rebuild while README formatting does not."""
    import inspect
    h = hashlib.sha256()
    for f in ['src/d_panel.py', 'tfs_stats/covariance.py', 'tfs_stats/rmt.py', 'src/networks.py', 'src/formation.py', 'src/bow.py']: h.update((ROOT / f).read_bytes())
    for fn in (_pairs, _target, _validated_delta, estimate_all, _fit_resid, build): h.update(inspect.getsource(fn).encode())
    h.update(repr((CONFIGS, ESTIMATORS, GRID.tolist(), VAL)).encode())
    return h.hexdigest()[:12]

def _pairs(R, G):
    i, j = np.triu_indices(len(R), 1); r = R[i, j]; ok = np.isfinite(r)
    return r[ok], (None if G is None else G[i, j][ok])

def _target(Rfit, G):
    """Fitted nested target and its (a, b). G None = constant correlation."""
    r, g = _pairs(Rfit, G); a, b = fit_target_ab(r, g)
    return nested_target(np.zeros((len(Rfit), len(Rfit))) if G is None else G, a, b), a, b

def _validated_delta(X, Tgt):
    """delta on GRID minimising the variance of the GMV portfolio over the window's last 63 days (R, D from the rest)."""
    A, V = X[:-VAL], X[-VAL:]; Ra = np.corrcoef(A, rowvar=False); sd = A.std(0, ddof=1); best = (np.inf, 0.0)
    for d in GRID:
        w = min_var_weights(sd[:, None] * shrink(Ra, Tgt, d) * sd[None, :]); v = float(np.var(V @ w))
        if v < best[0]: best = (v, float(d))
    return best[1]

def estimate_all(inp, T):
    """{estimator: (R^ or None for 1/N, info dict)} for one rebalance."""
    X, Xfit, F, Ffit = inp['X'], inp['Xfit'], inp['F'], inp['Ffit']; n, Nn = X.shape; Z = standardise(X)
    Rs = Z.T @ Z / (n - 1); Rfit = DP.pair_corr(Xfit); out = {'ew': (None, {})}
    if Nn < n: out['sample'] = (Rs, {})
    out['lw_identity'] = (to_corr(ledoit_wolf(Z)), {})                       # sklearn LedoitWolf via tfs_stats
    Tc, a, b = _target(Rfit, None); d, _ = ss_intensity(X, Tc); out['constcorr'] = (shrink(Rs, Tc, d), {'a': a, 'b': b, 'delta': d})
    out['clip'] = (clip_correlation(Rs, n, allow_q_gt_1=True), {})
    out['lwnl'] = (to_corr(lw_nonlinear(Z)), {})
    for name, G in (('industry', inp['B_ind']), ('text', inp['G_dense']), ('bow_raw', inp['G_bow'])):
        Tg, a, b = _target(Rfit, G); d, _ = ss_intensity(X, Tg); out[name] = (shrink(Rs, Tg, d), {'a': a, 'b': b, 'delta': d})
        if name == 'text': Ttext = Tg
    dv = _validated_delta(X, Ttext); out['text_val'] = (shrink(Rs, Ttext, dv), {'delta': dv})
    out['precond'] = (precondition_nl(X, Ttext), {})
    out['ff6'] = (factor_corr(X, F), {})
    _, Efit, _ = _fit_resid(Xfit, Ffit); Te, a, b = _target(DP.pair_corr(Efit), inp['G_dense'])
    _, E, _ = factor_fit(X, F); d, Re = ss_intensity(E, Te)
    out['ff6_text'] = (factor_corr(X, F, resid_corr=shrink(Re, Te, d)), {'a': a, 'b': b, 'delta': d})
    out['pca5'] = (factor_corr(X, k=5), {})
    P = np.random.default_rng(inp['m']).permutation(Nn); Tp, a, b = _target(Rfit, inp['G_dense'][np.ix_(P, P)])   # seed = rebalance index
    d, _ = ss_intensity(X, Tp); out['placebo'] = (shrink(Rs, Tp, d), {'a': a, 'b': b, 'delta': d})
    return out

def _fit_resid(Xfit, Ffit):
    """FF6 residuals of the pre-window, firm by firm on the days it has (formation.residuals: >= 200 returns)."""
    import formation as Fm
    B, E, nobs = Fm.residuals(Xfit, Ffit, min_obs=DP.MIN_FIT_OBS); return B, E, nobs

def build(config):
    """Run every rebalance of a configuration and cache the out-of-sample returns. Returns (daily, per_rebalance)."""
    Nn, T = CONFIGS[config]; h = _code_hash(); fd, fr = PROCESSED / f'd_oos_{config}_{h}.parquet', PROCESSED / f'd_reb_{config}_{h}.parquet'
    if fd.exists() and fr.exists(): return pd.read_parquet(fd), pd.read_parquet(fr)
    t0 = time.time(); days, rebs = [], []; prev = {}
    for m, k in enumerate(DP.schedule(T)):
        inp = DP.inputs(k, Nn, T); inp['m'] = m; X = inp['X']; sd = X.std(0, ddof=1); perm = inp['firms'].permno.to_numpy()
        for name, (Rh, info) in estimate_all(inp, T).items():
            if Rh is None: w = np.full(len(perm), 1 / len(perm)); pv = np.nan
            else:
                S = sd[:, None] * Rh * sd[None, :]; w = min_var_weights(S); pv = float(w @ S @ w)
            r = inp['hold'] @ w; ws = pd.Series(w, index=perm)
            to = float(ws.sub(prev[name], fill_value=0).abs().sum()) if name in prev else np.nan; prev[name] = ws
            days.append(pd.DataFrame({'date': inp['hold_dates'], 'estimator': name, 'ret': r, 'reb': m}))
            rebs.append({'reb': m, 'date': inp['date'], 'estimator': name, 'N': len(perm), 'pred_var': pv, 'real_ms': float(np.mean(r ** 2)),
                         'turnover': to, 'gross': float(np.abs(w).sum()), 'maxw': float(np.abs(w).max()), 'missing_hold': inp['missing_hold'], **info})
        if m % 12 == 0: print(config, inp['date'].date(), f'{time.time() - t0:.0f}s', flush=True)
    D, Rb = pd.concat(days, ignore_index=True), pd.DataFrame(rebs)
    D.to_parquet(fd); Rb.to_parquet(fr); print(config, 'built', f'{time.time() - t0:.0f}s')
    return D, Rb

def _period(D, period):
    if period == 'dev': return D[D.date < DP.DEV_END]
    if period == 'test': return D[D.date >= DP.DEV_END]
    return D

def _series(D, name, period):
    s = _period(D, period); s = s[s.estimator == name].set_index('date').ret.sort_index(); return s

def ann_sd(D, name, period): return float(_series(D, name, period).std(ddof=1) * np.sqrt(252))

def dev_sanity(config='primary'):
    """Development-period annualised SDs of LW-NL, the dense text target and 1/N (a construction check, no test)."""
    D, _ = build(config)
    return {n: ann_sd(D, n, 'dev') for n in ('lwnl', 'text', 'ew', 'constcorr', 'ff6', 'pca5')}

def _test(name_a, name_b, spec, out_name):
    t0 = time.time(); D, Rb = build('primary'); a, b = _series(D, name_a, 'test'), _series(D, name_b, 'test')
    if not a.index.equals(b.index): raise ValueError('the two portfolios cover different days')
    r = log_var_diff(a.to_numpy(), b.to_numpy()); bt = log_var_diff_boot(a.to_numpy(), b.to_numpy(), block=21, B=2000, seed=2026)
    res = {'delta': r['delta'], 'se': r['se'], 't': r['t'], 'p_one_sided': r['p_one_sided'], 'p_two_sided': r['p_two_sided'],
           'ci95': r['ci95'], 'ratio_sd': r['ratio_sd'], 'p_boot_one_sided': bt['p_one_sided'], 'bandwidth': r['bandwidth'],
           'test_days': r['T'], 'first_day': str(a.index[0].date()), 'last_day': str(a.index[-1].date()),
           f'ann_sd_{name_a}': ann_sd(D, name_a, 'test'), f'ann_sd_{name_b}': ann_sd(D, name_b, 'test'), 'code_hash': _code_hash(),
           'seconds': round(time.time() - t0)}
    OUT.mkdir(parents=True, exist_ok=True); (OUT / f'{out_name}.json').write_text(json.dumps(res, indent=1)); print(out_name, res)
    return res

def text_vs_lwnl(spec=None): return _test('text', 'lwnl', spec, 'text_vs_lwnl')
def text_vs_constcorr(spec=None): return _test('text', 'constcorr', spec, 'text_vs_constcorr')
def text_vs_placebo(spec=None): return _test('text', 'placebo', spec, 'text_vs_placebo')

def table(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); rows, metr = [], []
    for config in CONFIGS:
        D, Rb = build(config); names = [e for e in ESTIMATORS if e in set(D.estimator)]
        for period in ('dev', 'test', 'full'):
            base = _series(D, 'lwnl', period); res = []
            for e in names:
                s = _series(D, e, period); row = {'config': config, 'period': period, 'estimator': e, 'ann_sd': float(s.std(ddof=1) * np.sqrt(252)), 'days': len(s)}
                if e != 'lwnl':
                    r = log_var_diff(s.to_numpy(), base.to_numpy()); row.update({'delta_vs_lwnl': r['delta'], 't_vs_lwnl': r['t'], 'p_two_sided': r['p_two_sided']})
                res.append(row)
            cmp = [x for x in res if 'p_two_sided' in x]; hm = holm([x['p_two_sided'] for x in cmp], alpha=0.05)
            for x, rej in zip(cmp, hm['reject']): x['holm_reject_5pct'] = bool(rej)
            rows += res
        sub = Rb.copy(); sub['period'] = np.where(sub.date < DP.DEV_END, 'dev', 'test')
        for (e, period), g in sub.groupby(['estimator', 'period']):
            m = {'config': config, 'estimator': e, 'period': period, 'rebalances': len(g), 'mean_turnover': float(g.turnover.mean()),
                 'mean_gross': float(g.gross.mean()), 'mean_maxw': float(g.maxw.mean()),
                 'mean_bias_ratio': float((g.real_ms / g.pred_var).mean()) if g.pred_var.notna().any() else np.nan}
            if 'b' in g and g.b.notna().any():
                m.update({'median_a': float(g.a.median()), 'median_b': float(g.b.median()), 'share_b_zero': float((g.b <= 1e-12).mean())})
            if 'delta' in g and g.delta.notna().any(): m['median_delta'] = float(g.delta.median())
            metr.append(m)
        print(config, 'table done', f'{time.time() - t0:.0f}s', flush=True)
    T_, M_ = pd.DataFrame(rows), pd.DataFrame(metr)
    T_.to_json(OUT / 'table.json', orient='records', indent=1); M_.to_json(OUT / 'metrics.json', orient='records', indent=1)
    _readme(T_, M_)
    p = T_[(T_.config == 'primary') & (T_.period == 'test')]
    return {'primary_test_ann_sd': {r.estimator: round(r.ann_sd, 4) for r in p.itertuples()},
            'primary_test_holm_rejections': int(p.get('holm_reject_5pct', pd.Series(dtype=bool)).fillna(False).sum()),
            'configs': list(CONFIGS), 'code_hash': _code_hash(), 'seconds': round(time.time() - t0)}

def _readme(T_, M_):
    lines = ['# D_horse_race_table (diagnostic): every estimator against LW nonlinear shrinkage', '',
             'Annualised out-of-sample SD of the unconstrained GMV portfolio (21-day rebalancing), and Δ = log variance minus that of '
             'LW-NL with the LW (2011) prewhitened-HAC t; Holm at 5% (two-sided) across the estimators of each configuration and period. '
             'Development = before 2018-12-01, test = after.', '']
    for config in CONFIGS:
        for period in ('test', 'dev', 'full'):
            s = T_[(T_.config == config) & (T_.period == period)]
            if s.empty: continue
            lines += [f'## {config}, {period} ({int(s.days.iloc[0])} days)', '', '| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |', '|---|---|---|---|---|']
            for r in s.itertuples():
                dl = '' if pd.isna(getattr(r, 'delta_vs_lwnl', np.nan)) else f'{r.delta_vs_lwnl:+.4f}'
                tt = '' if pd.isna(getattr(r, 't_vs_lwnl', np.nan)) else f'{r.t_vs_lwnl:.2f}'
                hr = getattr(r, 'holm_reject_5pct', np.nan); hr = '' if not isinstance(hr, (bool, np.bool_)) else ('reject' if hr else '')
                lines.append(f'| {r.estimator} | {r.ann_sd:.2%} | {dl} | {tt} | {hr} |')
            lines.append('')
    lines += ['## Weights and fit (per rebalance means; test period, primary)', '', '| estimator | turnover | gross leverage | max |w| | bias ratio | median a | median b | share b = 0 | median δ |', '|---|---|---|---|---|---|---|---|---|']
    s = M_[(M_.config == 'primary') & (M_.period == 'test')]
    f = lambda v, fmt: '' if v is None or (isinstance(v, float) and np.isnan(v)) else format(v, fmt)
    for r in s.itertuples():
        lines.append(f"| {r.estimator} | {f(r.mean_turnover, '.2f')} | {f(r.mean_gross, '.2f')} | {f(r.mean_maxw, '.3f')} | {f(r.mean_bias_ratio, '.2f')} | "
                     f"{f(getattr(r, 'median_a', np.nan), '.3f')} | {f(getattr(r, 'median_b', np.nan), '.3f')} | {f(getattr(r, 'share_b_zero', np.nan), '.2f')} | {f(getattr(r, 'median_delta', np.nan), '.2f')} |")
    (OUT / 'README.md').write_text('\n'.join(lines) + '\n')
