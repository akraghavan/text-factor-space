"""Benjamini-Hochberg (q = 0.10) and Benjamini-Yekutieli over the exploratory family (PREREG "Confirmatory family and
multiple testing"; SPEC §10.3). Reads the latest status-'ok' runner record of every exploratory spec from runs.log
(nothing is re-estimated); m = the number of distinct exploratory specs run, which is what `python src/runner.py count`
reports (checked here). Each spec contributes the p-value of its registered statistic (a Fama-MacBeth NW t for C and E,
the binomial share test or Fisher-pooled permutation p for B, a permutation p for the permutation nulls, the LW (2011)
test for D): `p_one_sided` in the registered direction for specs with predicted_sign '+' or '-', and `p_two_sided` for
specs with predicted_sign 'none', which have no direction to test (PREREG change log, 8 Oct; family_p below; the table
names which p each spec used). tfs_stats.multitest.bh and .by (statsmodels multipletests) give the adjusted p-values
(q-values) and decisions. Writes analysis/output/exploratory/README.md and table.json.
Run: python src/runner.py run Exploratory_family_bh"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT, ROOT / 'src', ROOT / 'analysis'): sys.path.insert(0, str(_p))
import numpy as np
from tfs_stats.multitest import bh, by
import runner

Q = 0.10
HEADLINE = [('b_bar', 'b̄'), ('slope', 'slope'), ('alpha', 'alpha'), ('b_pooled', 'pooled b'), ('mean_b', 'mean annual b'),
            ('share', 'aligned share'), ('mean_ratio', 'overlap / random'), ('delta', 'Δ log var'), ('t_obs', 't (observed)')]
T_KEYS = ('t_nw', 't', 't_dyadic', 'pooled_T')                              # the t each entry reports, in this order

def family_p(res, sign):
    """The p a spec contributes to BH/BY: one-sided in the registered direction for '+' / '-' (the entry computes it
    as `p_one_sided`), two-sided for 'none' (`p_two_sided`). Returns (p, label)."""
    sign = str(sign)
    if sign == 'none':
        if 'p_two_sided' not in res: raise KeyError('a spec with predicted_sign none must return p_two_sided')
        return float(res['p_two_sided']), 'two-sided'
    if sign not in ('+', '-'): raise ValueError(f'predicted_sign {sign!r}')
    return float(res['p_one_sided']), f'one-sided ({sign})'

def _headline(res):
    for k, lab in HEADLINE:
        if k in res: return lab, res[k]
    return '', float('nan')

def run(spec=None):
    recs = [json.loads(l) for l in (ROOT / 'runs.log').read_text().splitlines() if l.strip()]
    latest = {}
    for r in recs:
        if r.get('status') == 'ok' and r.get('family') == 'exploratory': latest[r['spec']] = r
    m, counted = runner.count(); ids = sorted(latest, key=lambda s: (latest[s]['element'], s))
    if sorted(counted) != sorted(ids): raise RuntimeError(f'runner count {m} disagrees with the {len(ids)} exploratory specs found')
    _, specs, _ = runner.load_registry(ROOT / 'specs.yaml')
    fp = [family_p(latest[s]['result'], specs[s]['predicted_sign']) for s in ids]
    p = np.array([v for v, _ in fp], dtype=float)
    b, y = bh(p, Q), by(p, Q)
    rows = []
    for k, s in enumerate(ids):
        res = latest[s]['result']; lab, est = _headline(res)
        rows.append({'spec': s, 'element': latest[s]['element'], 'estimate_label': lab, 'estimate': est,
                     't': next((res[k] for k in T_KEYS if k in res), None), 'p': float(p[k]), 'p_used': fp[k][1], 'q_bh': float(b['p_adjusted'][k]),
                     'reject_bh': bool(b['reject'][k]), 'q_by': float(y['p_adjusted'][k]), 'reject_by': bool(y['reject'][k]),
                     'run_time': latest[s]['time'], 'commit': latest[s]['commit'][:7]})
    f = lambda v: '' if v is None else (f'{v:.3g}' if isinstance(v, float) else str(v))
    lines = [f'# Exploratory family: Benjamini–Hochberg and Benjamini–Yekutieli at q = {Q}', '',
             f'm = {m} exploratory specs run (`python src/runner.py count`). p-values from the latest `ok` runner record of each '
             '(`runs.log`; nothing re-estimated): one-sided in the registered direction, two-sided for the one spec with no predicted sign; '
             'q-values from `tfs_stats.multitest.bh` / `.by`. BY is valid under any dependence; BH '
             'assumes independence or positive dependence, which overlapping variants of the same test roughly satisfy.', '',
             '| Spec | Element | Estimate | t | p | p used | BH q | BH reject | BY q | BY reject | commit |', '|---|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| `{r['spec']}` | {r['element']} | {r['estimate_label']} {f(r['estimate'])} | {f(r['t'])} | {r['p']:.2g} | {r['p_used']} | "
                     f"{r['q_bh']:.2g} | {'yes' if r['reject_bh'] else 'no'} | {r['q_by']:.2g} | {'yes' if r['reject_by'] else 'no'} | {r['commit']} |")
    out = {'m': m, 'q': Q, 'rejected_bh': int(sum(r['reject_bh'] for r in rows)), 'rejected_by': int(sum(r['reject_by'] for r in rows))}
    lines += ['', f"Rejected at q = {Q}: BH {out['rejected_bh']} of {m}, BY {out['rejected_by']} of {m}."]
    o = ROOT / 'analysis' / 'output' / 'exploratory'; o.mkdir(parents=True, exist_ok=True)
    (o / 'README.md').write_text('\n'.join(lines) + '\n'); (o / 'table.json').write_text(json.dumps(rows, indent=1))
    print('\n'.join(lines))
    return out

if __name__ == '__main__':
    run()

RW_FAMILIES = {
    'C (full period, 165 months)': ['C_x_bow_null', 'C_x_bow_raw', 'C_x_binary_network', 'C_x_missing_bm_indicator', 'C_x_pc5', 'C_x_pc10',
                                    'C_x_dimson', 'C_x_sich'],
    'E (test period, 91 months)': ['E_x_nearest5', 'E_x_delist_0', 'E_x_delist_m100', 'E_x_sim_weighted', 'E_x_h_6_1', 'E_x_h_12_7',
                                   'E_x_grundy_martin', 'E_x_idiosyncratic', 'E_x_text_only', 'E_x_sic_only', 'E_x_both', 'E_x_dense_only',
                                   'E_x_stale_y3', 'E_x_sich', 'E_x_nyse20']}

BLOCKS, FWER_TARGET, SIM_DRAWS, SIM_REPS = (4, 8, 12), 0.06, 2000, 1000

def romano_wolf(spec=None):
    """Exploratory_family_romano_wolf (diagnostic; D25 with the D28 implementation correction): Romano-Wolf stepdown
    (tfs_stats.multitest.romano_wolf: arch StepM, stationary bootstrap, 10,000 reps, seed 2026, FWER 5%) on two families
    of monthly Fama-MacBeth slope series saved by the entries (analysis/output/<dir>/series/<spec>.json; the headline
    regressor's b_t): C's full-period variants and E's test-period variants. Excluded (D25): subperiods, 12-month
    windows, permutation nulls, portfolios, the HP replication, MRQAP/dyadic, B, D and the two-sided placebo.
    D28: (1) each series is studentised by its full-sample Newey-West SE with its spec's own lags (nw_lags_rule(T): 4 at
    T = 165, 3 at T = 91), recomputed from the saved series and checked against the logged se_nw; (2) the block length
    is the smallest of (4, 8, 12) whose simulated FWER (tfs_stats.multitest.romano_wolf_size: independent AR(1) series at
    the family's mean observed lag-1 autocorrelation and shape, 2,000 draws, 1,000 reps each) is <= 6%; if none is, 12,
    and RW is reported as mildly liberal at that rate. Writes analysis/output/exploratory/romano_wolf.md/.json."""
    from tfs_stats.multitest import romano_wolf as rw, romano_wolf_size
    from tfs_stats.regression import fm_inference, nw_lags_rule
    import series_out
    recs = [json.loads(l) for l in (ROOT / 'runs.log').read_text().splitlines() if l.strip()]
    logged = {}
    for r in recs:
        if r.get('status') == 'ok' and r.get('family') == 'exploratory': logged[r['spec']] = r['result']
    out, lines = {}, ['# Romano–Wolf stepdown across Fama–MacBeth slope series (D25; studentised, D28)', '',
                      'arch `StepM` on studentised series x_t = b_t / (√T · SE_NW), SE from each spec\'s own Newey–West lags on the full sample and '
                      'held fixed across draws (arch 8.0.0 does not studentise itself); superior = mean > 0; stationary bootstrap; 10,000 replications; '
                      'seed 2026; FWER 5%. Block length: the smallest of 4, 8, 12 with simulated FWER ≤ 6% (independent AR(1) series at the family\'s '
                      'mean lag-1 autocorrelation and shape; 2,000 draws).', '']
    for fi, (fam, ids) in enumerate(RW_FAMILIES.items()):
        S, se, ac = {}, {}, []
        for sid in ids:
            f = list((ROOT / 'analysis' / 'output').glob(f'*/series/{sid}.json'))
            if len(f) != 1: raise FileNotFoundError(f'{sid}: {len(f)} series files')
            S[sid] = series_out.load(f[0]); x = np.array(list(S[sid].values())); L = nw_lags_rule(len(x))
            se[sid] = float(fm_inference(x[:, None], L)['se'][0]); ac.append(float(np.corrcoef(x[1:], x[:-1])[0, 1]))
            if 'se_nw' in logged.get(sid, {}) and not np.isclose(se[sid], logged[sid]['se_nw'], rtol=1e-9):
                raise ValueError(f'{sid}: recomputed NW SE {se[sid]} != logged {logged[sid]["se_nw"]}')
        months = list(S[ids[0]])
        if any(list(v) != months for v in S.values()): raise ValueError(f'{fam}: series cover different months')
        T, k, rho, L = len(months), len(ids), float(np.mean(ac)), nw_lags_rule(len(months))
        sims = {b: romano_wolf_size(T, k, rho, b, L, nsim=SIM_DRAWS, reps=SIM_REPS, seed=1000 * (fi + 1) + b) for b in BLOCKS}
        ok = [b for b in BLOCKS if sims[b] <= FWER_TARGET]; block = ok[0] if ok else BLOCKS[-1]
        r = rw({kk: np.array(list(v.values())) for kk, v in S.items()}, block=block, se=se)
        tstat = {kk: float(np.mean(list(v.values())) / se[kk]) for kk, v in S.items()}
        out[fam] = {'series': k, 'months': T, 'nw_lags': L, 'mean_lag1_autocorr': rho, 'simulated_fwer': {str(b): v for b, v in sims.items()},
                    'block': block, 'fwer_at_block': sims[block], 'meets_6pct': bool(ok), 'superior': r['superior'],
                    'not_rejected': [kk for kk in ids if kk not in r['superior']], 't': tstat}
        lines += [f'## {fam}', '', f"Mean lag-1 autocorrelation {rho:.3f}; NW lags {L}. Simulated FWER at blocks 4 / 8 / 12: "
                  + ' / '.join(f'{sims[b]:.3f}' for b in BLOCKS) + f". Block used: {block} (simulated FWER {sims[block]:.3f}"
                  + ('' if ok else '; no block reaches 6%, so RW is mildly liberal at this rate') + ').', '',
                  f"{len(r['superior'])} of {k} mean slopes significantly positive at FWER 5%.", '',
                  '| spec | t (NW) | superior |', '|---|---|---|'] + \
                 [f"| `{kk}` | {tstat[kk]:.2f} | {'yes' if kk in r['superior'] else 'no'} |" for kk in ids] + ['']
        print(fam, {k_: v for k_, v in out[fam].items() if k_ != 't'}, flush=True)
    o = ROOT / 'analysis' / 'output' / 'exploratory'; o.mkdir(parents=True, exist_ok=True)
    (o / 'romano_wolf.json').write_text(json.dumps(out, indent=1)); (o / 'romano_wolf.md').write_text('\n'.join(lines) + '\n'); print('\n'.join(lines))
    return {fam: {'block': v['block'], 'fwer_at_block': v['fwer_at_block'], 'superior': v['superior'], 'not_rejected': v['not_rejected']}
            for fam, v in out.items()}
