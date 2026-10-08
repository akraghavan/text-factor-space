"""Element E exploratory specs, tier 2 (each through src/runner.py, counted for BH). Same construction as the
confirmatory run (analysis/e_h3.py, src/e_signals.py, both unchanged), delisting imputation at the primary delta.

portfolios      E_x_portfolios      Test period. Each month t, sort on PEERMOM at NYSE breakpoints (NYSE firms of that
                                    month's sample) into quintiles and deciles; long the top group, short the bottom one,
                                    held for month t; equal- and value-weighted (ME at t-1); price at t-1 >= $1 and >= $5.
                                    Sample: E firms with a PEERMOM and a month-t return (no complete-case drop: a sort
                                    needs only the signal). Alphas on FF3, FF3+UMD, FF5+UMD and FF5+UMD+STR (Ken French
                                    ST_Rev, src/ff_extra.py), NW(3) t. Headline for BH, fixed before the run: quintile,
                                    equal-weighted, price >= $1, FF5+UMD alpha, one-sided p.
idiosyncratic   E_x_idiosyncratic   Test period. PEERMOM built from peers' idiosyncratic returns
                                    e_jm = (r_jm - rf_m) - beta_jm' f_m, beta_jm = the FF6 betas on the 252 trading days
                                    before month m (src/c_panel.py, no alpha), compounded over t-12..t-1 (>= 8 months);
                                    same peers, controls and FM as H3. Statistic: test-period slope, NW(3), one-sided p.
hp_replication  E_x_hp_replication  Full period Jul 2012 - Jun 2026 on the common sample (E's complete cases, so every
                                    firm-month has both a text and a TNIC-3 peer): FM of the excess return on TNIC-3 peer
                                    momentum with HP-style controls (log ME, log B/M, r_1, R(t-12,t-2), FF-48 industry
                                    momentum, SIC-3 momentum), z-scored (our convention, NW(4) at T = 168) and raw
                                    (winsorised 1/99, not z-scored: the units of HP Table 3A's 0.008); then our BoW-null
                                    PEERMOM in place of TNIC momentum on the same rows. Quintile EW long-short alphas
                                    (FF3, as HP Table 11B, and FF3+UMD) for both signals. Headline for BH: the z-scored
                                    TNIC-3 slope, one-sided p.
perm_matched    E_x_perm_matched    Test period. 999 draws; in each, every true peer j of firm i is replaced by a random
                                    universe firm from j's own decile of R(t-12, t-1) that month (never i itself);
                                    PEERMOM is recomputed from the random peers, winsorised and z-scored as before, and
                                    the FM t recorded. p = (1 + #{t_b >= t_obs}) / 1000. The null keeps the coarse level
                                    of the peers' past returns and asks whether the identity of the linked firms matters
                                    beyond it (Moskowitz-Grinblatt / HP matched random peers).
Writes analysis/output/e_explore2/. Aggregates only."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import formation as F, networks as N, e_signals as ES, e_h3, e_explore as EX, c_panel as C, series_out
from paths import PROCESSED
from ff_extra import st_reversal_monthly
from tfs_stats.regression import ols_qr, vcov, fama_macbeth, nw_lags_rule, one_sided_p

OUT = ROOT / 'analysis' / 'output' / 'e_explore2'
MODELS = {'FF3': ['Mkt_RF', 'SMB', 'HML'], 'FF3+UMD': ['Mkt_RF', 'SMB', 'HML', 'Mom'],
          'FF5+UMD': ['Mkt_RF', 'SMB', 'HML', 'RMW', 'CMA', 'Mom'], 'FF5+UMD+STR': ['Mkt_RF', 'SMB', 'HML', 'RMW', 'CMA', 'Mom', 'ST_Rev']}

def _save(name, res):
    OUT.mkdir(parents=True, exist_ok=True); (OUT / f'{name}.json').write_text(json.dumps(res, indent=1, default=float)); print(name, res)
    return res

def _factors():
    ff = pd.read_parquet(PROCESSED / 'ff_monthly.parquet').set_index('ym'); ff['ST_Rev'] = st_reversal_monthly().reindex(ff.index)
    return ff

def long_short(P, signal, groups, weight, min_price):
    """Monthly top-minus-bottom return; groups at NYSE breakpoints of `signal` within each month's sample."""
    out = {}
    for t, g in P[(P.prc >= min_price) & P[signal].notna() & P.exret.notna()].groupby('t'):
        bp = g.loc[g.primaryexch == 'N', signal].quantile(np.arange(1, groups) / groups).to_numpy()
        k = np.searchsorted(bp, g[signal].to_numpy(), side='right'); hi, lo = g[k == groups - 1], g[k == 0]
        avg = (lambda x: x.exret.mean()) if weight == 'EW' else (lambda x: np.average(x.exret, weights=x.me))
        out[t] = avg(hi) - avg(lo)
    return pd.Series(out).sort_index()

def alpha(ls, ff, model, lags):
    """OLS of the long-short series on [1, factors] (tfs_stats.regression.ols_qr), NW(lags) SE via vcov."""
    f = ff.reindex(ls.index)[MODELS[model]]; X = np.column_stack([np.ones(len(ls)), f.to_numpy()])
    b, e = ols_qr(X, ls.to_numpy()); se = np.sqrt(np.diag(vcov(X, e, kind='NW', lags=lags)))
    return {'alpha': float(b[0]), 't': float(b[0] / se[0]), 'umd_loading': float(b[1 + MODELS[model].index('Mom')]) if 'Mom' in MODELS[model] else None}

def _test_panel():
    EX._base_panel('primary'); return e_h3.panel(*e_h3.TEST)

def portfolios(spec=None):
    t0 = time.time(); P, d = _test_panel(); ff = _factors(); L = nw_lags_rule(P.t.nunique()); rows = []
    for groups in (5, 10):
        for weight in ('EW', 'VW'):
            for pmin in (1, 5):
                ls = long_short(P, 'peermom', groups, weight, pmin)
                r = {'groups': groups, 'weight': weight, 'min_price': pmin, 'months': len(ls), 'mean_ls': float(ls.mean())}
                for m in MODELS: a = alpha(ls, ff, m, L); r[f'alpha_{m}'] = a['alpha']; r[f't_{m}'] = a['t']
                r['umd_loading_FF5+UMD'] = alpha(ls, ff, 'FF5+UMD', L)['umd_loading']; rows.append(r)
    R = pd.DataFrame(rows); OUT.mkdir(parents=True, exist_ok=True); R.to_json(OUT / 'portfolios_table.json', orient='records', indent=1)
    h = R[(R.groups == 5) & (R.weight == 'EW') & (R.min_price == 1)].iloc[0]
    return _save('portfolios', {'alpha': float(h['alpha_FF5+UMD']), 't': float(h['t_FF5+UMD']), 'nw_lags': L,
                                'p_one_sided': float(one_sided_p(h['t_FF5+UMD'])), 'headline': 'quintile EW price>=1 FF5+UMD',
                                'mean_ls': float(h.mean_ls), 'umd_loading': float(h['umd_loading_FF5+UMD']), 'months': int(h.months),
                                'seconds': round(time.time() - t0)})

def _capture_peers():
    """Wrap networks.peers so the next signals_at call leaves its peer matrix (rows = universe_at(t) order) in stash."""
    stash, orig = {}, N.peers
    def cap(S, pi): A = orig(S, pi); stash['A'] = A; return A
    N.peers = cap
    return stash, lambda: setattr(N, 'peers', orig)

def _idio_monthly():
    m = F.monthly()[['permno', 'ym', 'ret']]; B = pd.read_parquet(C.BET)
    x = m.merge(B, on=['permno', 'ym'], how='inner'); ff = pd.read_parquet(PROCESSED / 'ff_monthly.parquet').set_index('ym').reindex(x.ym)
    e = x.ret.to_numpy() - ff.RF.to_numpy() - sum(x[f'b_{f}'].to_numpy() * ff[f].to_numpy() for f in F.FACTORS)
    return pd.DataFrame({'permno': x.permno.to_numpy(), 'ym': x.ym.to_numpy(), 'ret': e})

def idiosyncratic(spec=None):
    t0 = time.time(); EX._base_panel('primary'); idm = _idio_monthly(); orig_sig = ES.signals_at; stash, restore = _capture_peers()
    def sig(t, monthly=None):
        u = orig_sig(t); univ = F.universe_at(pd.Period(t, 'M')).reset_index(drop=True)
        R = ES.cum_return(t, 12, 1, monthly=idm).reindex(univ.permno).to_numpy(); pm, _ = ES._peer_mean(stash['A'], R)
        u['peermom_total'] = u.peermom; u['peermom'] = pd.Series(pm, index=univ.permno.to_numpy()).reindex(u.permno).to_numpy()
        return u
    ES.signals_at = sig
    try: P, d = e_h3.panel(*e_h3.TEST)
    finally: ES.signals_at = orig_sig; restore()
    T = d.t.nunique(); L = nw_lags_rule(T); r = e_h3.fm(d, L); series_out.save(OUT, spec, 'idiosyncratic', r['periods'], r['lambdas'][:, 1])
    return _save('idiosyncratic', {'slope': float(r['coef'][1]), 't_nw': float(r['tstat'][1]), 'nw_lags': L, 'p_one_sided': float(one_sided_p(r['tstat'][1])),
                                   'months': int(T), 'firm_months': int(len(d)), 'firm_months_before_drop': int(len(P)),
                                   'corr_with_total_peermom': float(P[['peermom', 'peermom_total']].corr().iloc[0, 1]), 'seconds': round(time.time() - t0)})

HP_CTRL = ['log_me', 'log_bm', 'r_1', 'r12_2', 'indmom', 'sic3mom']

def hp_replication(spec=None):
    t0 = time.time(); EX._base_panel('primary'); P, d = e_h3.panel(e_h3.DEV[0], e_h3.TEST[1]); T = d.t.nunique(); L = nw_lags_rule(T)
    raw = P.loc[d.index, ['t', 'exret', 'peermom', 'tnicmom'] + HP_CTRL].copy()
    for c in ['peermom', 'tnicmom'] + HP_CTRL:
        raw[c] = raw.groupby('t')[c].transform(lambda s: s.clip(*s.quantile([0.01, 0.99])))
    fm = lambda D, sigcol: fama_macbeth(D.exret.to_numpy(), D[[sigcol] + HP_CTRL].to_numpy(), D.t.astype(str).to_numpy(), nw_lags=L)
    out = {}
    for sigcol in ('tnicmom', 'peermom'):
        z, r = fm(d, sigcol), fm(raw, sigcol)
        out[sigcol] = {'slope_z': float(z['coef'][1]), 't_z': float(z['tstat'][1]), 'slope_raw': float(r['coef'][1]), 't_raw': float(r['tstat'][1])}
    ff = _factors(); C5 = P.loc[d.index].copy()
    for sigcol in ('tnicmom', 'peermom'):
        ls = long_short(C5, sigcol, 5, 'EW', 1)
        for m in ('FF3', 'FF3+UMD'):
            a = alpha(ls, ff, m, L); out[sigcol][f'q5_alpha_{m}'] = a['alpha']; out[sigcol][f'q5_t_{m}'] = a['t']
            if m == 'FF3+UMD': out[sigcol]['q5_umd_loading'] = a['umd_loading']
    res = {'slope': out['tnicmom']['slope_z'], 't_nw': out['tnicmom']['t_z'], 'nw_lags': L, 'p_one_sided': float(one_sided_p(out['tnicmom']['t_z'])),
           'months': int(T), 'firm_months': int(len(d)), 'tnic3': out['tnicmom'], 'bow_null_peermom': out['peermom'],
           'hp_reference': {'table3a_slope': 0.008, 'table3a_t': 4.36, 'table11b_q5_ew_ff3_alpha': 0.017, 'table11b_t': 3.30},
           'seconds': round(time.time() - t0)}
    return _save('hp_replication', res)

def _zwin_blocks(v, starts):
    """e_h3.zwin (winsorise 1/99, z-score with ddof=1) applied to each month's block of v (rows sorted by month)."""
    out = np.empty_like(v)
    for a, b in zip(starts[:-1], starts[1:]):
        x = v[a:b]; lo, hi = np.quantile(x, [0.01, 0.99]); x = np.clip(x, lo, hi); out[a:b] = (x - x.mean()) / x.std(ddof=1)
    return out

def perm_matched(spec=None, n_perm=999, seed=2026):
    t0 = time.time(); EX._base_panel('primary'); stash, restore = _capture_peers(); orig_sig = ES.signals_at; months = {}
    def sig(t, monthly=None):
        u = orig_sig(t); univ = F.universe_at(pd.Period(t, 'M')).reset_index(drop=True)
        months[pd.Period(t, 'M')] = (stash['A'], univ.permno.to_numpy(), ES.cum_return(t, 12, 1).reindex(univ.permno).to_numpy())
        return u
    ES.signals_at = sig
    try: P, d = e_h3.panel(*e_h3.TEST)
    finally: ES.signals_at = orig_sig; restore()
    d = d.sort_values('t', kind='stable').reset_index(drop=True); L = nw_lags_rule(d.t.nunique()); t_obs = float(e_h3.fm(d, L)['tstat'][1])
    blocks, starts, n0, true_pm = [], [0], 0, []
    for t, g in d.groupby('t', sort=True):
        A, pu, R = months[t]; ok = np.isfinite(R); pos = pd.Index(pu).get_indexer(g.permno.to_numpy())
        rr, cc = np.nonzero(A[pos] & ok[None, :])
        dec = np.full(len(R), -1); dec[ok] = pd.qcut(pd.Series(R[ok]).rank(method='first'), 10, labels=False).to_numpy()
        order = np.argsort(dec, kind='stable'); first = np.searchsorted(dec[order], np.arange(10)); size = np.bincount(dec[ok], minlength=10)
        cnt = np.bincount(rr, minlength=len(pos))
        obs = np.bincount(rr, R[cc], minlength=len(pos)) / cnt
        assert np.allclose(obs, P.set_index(['t', 'permno']).loc[[(t, p) for p in g.permno], 'peermom'].to_numpy())   # same PEERMOM as e_signals
        true_pm.append(obs)
        blocks.append((rr, dec[cc], pos[rr], order, first, size, cnt, R)); n0 += len(pos); starts.append(n0)
    rng = np.random.default_rng(seed); tb = np.empty(n_perm); starts = np.array(starts); corr = []; true_pm = np.concatenate(true_pm)
    X = d[e_h3.RHS].to_numpy().copy(); y = d.exret.to_numpy(); tt = d.t.astype(str).to_numpy()
    for b in range(n_perm):
        pm = np.empty(n0)
        for (rr, q, own, order, first, size, cnt, R), a in zip(blocks, starts[:-1]):
            u = rng.integers(0, size[q]); k = order[first[q] + u]
            clash = k == own; k[clash] = order[first[q[clash]] + (u[clash] + 1) % size[q[clash]]]      # never i itself
            pm[a:a + len(cnt)] = np.bincount(rr, R[k], minlength=len(cnt)) / cnt
        if b < 20: corr.append(np.corrcoef(pm, true_pm)[0, 1])
        X[:, 0] = _zwin_blocks(pm, starts); tb[b] = fama_macbeth(y, X, tt, nw_lags=L)['tstat'][1]
        if b % 100 == 0: print('draw', b, f'{time.time() - t0:.0f}s', flush=True)
    res = {'t_obs': t_obs, 'p_one_sided': float((1 + np.sum(tb >= t_obs)) / (n_perm + 1)), 'mean_t_perm': float(tb.mean()),
           'sd_t_perm': float(tb.std()), 'p95_t_perm': float(np.quantile(tb, 0.95)), 'n_perm': n_perm, 'nw_lags': L,
           'mean_corr_random_vs_true_peermom': float(np.mean(corr)), 'firm_months': int(len(d)), 'seconds': round(time.time() - t0)}
    return _save('perm_matched', res)
