"""E_event_time (diagnostic, SPEC §9 portfolio items that need no extra data; D24). Not a test.
Test-period formations Dec 2018 - Jun 2026, the E_x_portfolios headline portfolio: quintiles of PEERMOM at NYSE
breakpoints, equal-weighted, price at t-1 >= $1, firms with a month-t return (analysis/e_explore2.long_short's
sample, so month +1 equals that spec's long-short series).
  1. Event time: the same top-minus-bottom portfolio formed at t, held in month t+h-1 for h = 1..24 (a member with no
     return that month drops out of that month's average); mean and NW(3) t over the formations that have month
     t+h-1 in the data (to Jun 2026), via tfs_stats.regression.fm_inference on the series (the NW t of a mean).
  2. Turnover: for each leg, 1/2 sum_i |w_i,t - w_i,t-1| with equal weights (a name not held counts as 0), i.e. the
     share of the leg replaced each month; the long-short turnover adds the two legs. Break-even round-trip cost =
     the FF5+UMD alpha of the month +1 series / that turnover (no spread data, so no net-of-cost alpha; D27).
  3. Risk: the 3 worst months of the month +1 series and its maximum drawdown (peak-to-trough of the cumulative
     product of 1 + r).
Writes analysis/output/e_event_time/ (README.md, event_time.json, fig_event_time.png). Aggregates only."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import formation as F, e_h3, e_explore2 as E2
from tfs_stats.regression import fm_inference, nw_lags_rule

OUT = ROOT / 'analysis' / 'output' / 'e_event_time'
H = 24

def _legs(P):
    """{t: (long permnos, short permnos)} for the headline sort, exactly as e_explore2.long_short builds it."""
    out = {}
    for t, g in P[(P.prc >= 1) & P.peermom.notna() & P.exret.notna()].groupby('t'):
        bp = g.loc[g.primaryexch == 'N', 'peermom'].quantile(np.arange(1, 5) / 5).to_numpy()
        k = np.searchsorted(bp, g.peermom.to_numpy(), side='right'); out[t] = (g.permno[k == 4].to_numpy(), g.permno[k == 0].to_numpy())
    return out

def run(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); P, d = E2._test_panel(); legs = _legs(P)
    m = F.monthly(); ret = m.set_index(['permno', 'ym']).ret; last = m.ym.max()
    L = nw_lags_rule(len(legs)); ev = {}
    for h in range(1, H + 1):
        s = {}
        for t, (lo_hi) in legs.items():
            u = t + h - 1
            if u > last: continue
            lg, sh = (ret.reindex(pd.MultiIndex.from_arrays([x, np.full(len(x), u)])).to_numpy() for x in lo_hi)
            if np.isfinite(lg).any() and np.isfinite(sh).any(): s[t] = np.nanmean(lg) - np.nanmean(sh)
        v = np.array(list(s.values()))[:, None]; r = fm_inference(v, L)
        ev[h] = {'mean': float(r['coef'][0]), 't_nw': float(r['tstat'][0]), 'formations': len(s)}
        if h == 1: ls1 = pd.Series(s).sort_index()
    ref = E2.long_short(P, 'peermom', 5, 'EW', 1); assert np.allclose(ls1.to_numpy(), ref.reindex(ls1.index).to_numpy())   # = E_x_portfolios
    turn = []
    ts = sorted(legs)
    for a, b in zip(ts[:-1], ts[1:]):
        tv = 0.0
        for k in (0, 1):
            old, new = pd.Series(1 / len(legs[a][k]), index=legs[a][k]), pd.Series(1 / len(legs[b][k]), index=legs[b][k])
            tv += 0.5 * old.sub(new, fill_value=0).abs().sum()
        turn.append(tv)
    ff = E2._factors(); al = E2.alpha(ls1, ff, 'FF5+UMD', L)
    cum = (1 + ls1).cumprod(); mdd = float((cum / cum.cummax() - 1).min()); worst = ls1.nsmallest(3)
    res = {'alpha_ff5umd_month1': al['alpha'], 't_alpha': al['t'], 'mean_turnover_long_short': float(np.mean(turn)),
           'breakeven_round_trip_cost': float(al['alpha'] / np.mean(turn)), 'max_drawdown': mdd,
           'worst_months': {str(k): float(v) for k, v in worst.items()}, 'event_time': {str(h): v for h, v in ev.items()},
           'cumulative_mean_months_1_12': float(sum(ev[h]['mean'] for h in range(1, 13))),
           'cumulative_mean_months_13_24': float(sum(ev[h]['mean'] for h in range(13, 25))), 'formations': len(legs), 'seconds': round(time.time() - t0)}
    (OUT / 'event_time.json').write_text(json.dumps(res, indent=1)); _figure(ev)
    txt = ['# E_event_time (diagnostic): the headline E portfolio in event time', '',
           'Quintile EW long-short on PEERMOM (NYSE breakpoints, price ≥ $1), test-period formations Dec 2018 – Jun 2026.', '',
           '| h (months after formation) | mean long-short return | NW(3) t | formations |', '|---|---|---|---|']
    txt += [f"| {h} | {v['mean']:.4f} | {v['t_nw']:.2f} | {v['formations']} |" for h, v in ev.items()]
    txt += ['', f"Sum of the mean returns over months 1–12: {res['cumulative_mean_months_1_12']:.4f}; months 13–24: {res['cumulative_mean_months_13_24']:.4f}.",
            f"Turnover (both legs, share of each leg replaced, summed): {res['mean_turnover_long_short']:.2f} a month. FF5+UMD alpha of month +1: "
            f"{res['alpha_ff5umd_month1']:.4f} (t {res['t_alpha']:.2f}), so the break-even round-trip cost is {res['breakeven_round_trip_cost']:.2%} of the value traded.",
            f"Maximum drawdown {mdd:.1%}; worst months: " + ', '.join(f'{k} {v:.1%}' for k, v in res['worst_months'].items()) + '.', '',
            f"Runtime {res['seconds']} s."]
    (OUT / 'README.md').write_text('\n'.join(txt) + '\n'); print('\n'.join(txt))
    return {k: v for k, v in res.items() if k != 'event_time'}

def _figure(ev):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    h = np.array(list(ev)); m = np.array([ev[k]['mean'] for k in ev]) * 100
    fig, ax = plt.subplots(figsize=(7, 3.6)); ax.bar(h, m, color='#1f4e79'); ax.plot(h, np.cumsum(m), color='#c55a11', lw=1.6, label='cumulative')
    ax.axhline(0, color='k', lw=0.6); ax.set_xlabel('months after formation'); ax.set_ylabel('% per month'); ax.legend(frameon=False)
    ax.set_title('PEERMOM quintile EW long-short in event time (test-period formations)', fontsize=10, loc='left')
    fig.tight_layout(); fig.savefig(OUT / 'fig_event_time.png', dpi=150); plt.close(fig)
