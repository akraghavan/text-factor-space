"""Benjamini-Hochberg (q = 0.10) and Benjamini-Yekutieli over the exploratory family (PREREG "Confirmatory family and
multiple testing"; SPEC §10.3). Reads the latest status-'ok' runner record of every exploratory spec from runs.log
(nothing is re-estimated); m = the number of distinct exploratory specs run, which is what `python src/runner.py count`
reports (checked here). Each spec contributes the one-sided p-value its entry returns as `p_one_sided` (its registered
statistic: a Fama-MacBeth NW t for C and E, the binomial share test or Fisher-pooled permutation p for B, a permutation
p for the permutation nulls). tfs_stats.multitest.bh and .by (statsmodels multipletests) give the adjusted p-values
(q-values) and decisions. Writes analysis/output/exploratory/README.md and table.json.
Run: python src/runner.py run Exploratory_family_bh"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'src'))
import numpy as np
from tfs_stats.multitest import bh, by
import runner

Q = 0.10
HEADLINE = [('b_bar', 'b̄'), ('slope', 'slope'), ('alpha', 'alpha'), ('share', 'aligned share'), ('mean_ratio', 'overlap / random'),
            ('t_obs', 't (observed)')]

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
    p = np.array([latest[s]['result']['p_one_sided'] for s in ids], dtype=float)
    b, y = bh(p, Q), by(p, Q)
    rows = []
    for k, s in enumerate(ids):
        res = latest[s]['result']; lab, est = _headline(res)
        rows.append({'spec': s, 'element': latest[s]['element'], 'estimate_label': lab, 'estimate': est,
                     't': res.get('t_nw', res.get('t', None)), 'p_one_sided': float(p[k]), 'q_bh': float(b['p_adjusted'][k]),
                     'reject_bh': bool(b['reject'][k]), 'q_by': float(y['p_adjusted'][k]), 'reject_by': bool(y['reject'][k]),
                     'run_time': latest[s]['time'], 'commit': latest[s]['commit'][:7]})
    f = lambda v: '' if v is None else (f'{v:.3g}' if isinstance(v, float) else str(v))
    lines = [f'# Exploratory family: Benjamini–Hochberg and Benjamini–Yekutieli at q = {Q}', '',
             f'm = {m} exploratory specs run (`python src/runner.py count`). One-sided p-values from the latest `ok` runner record of each '
             '(`runs.log`; nothing re-estimated); q-values from `tfs_stats.multitest.bh` / `.by`. BY is valid under any dependence; BH '
             'assumes independence or positive dependence, which overlapping variants of the same test roughly satisfy.', '',
             '| Spec | Element | Estimate | t | one-sided p | BH q | BH reject | BY q | BY reject | commit |', '|---|---|---|---|---|---|---|---|---|---|']
    for r in rows:
        lines.append(f"| `{r['spec']}` | {r['element']} | {r['estimate_label']} {f(r['estimate'])} | {f(r['t'])} | {r['p_one_sided']:.2g} | "
                     f"{r['q_bh']:.2g} | {'yes' if r['reject_bh'] else 'no'} | {r['q_by']:.2g} | {'yes' if r['reject_by'] else 'no'} | {r['commit']} |")
    out = {'m': m, 'q': Q, 'rejected_bh': int(sum(r['reject_bh'] for r in rows)), 'rejected_by': int(sum(r['reject_by'] for r in rows))}
    lines += ['', f"Rejected at q = {Q}: BH {out['rejected_bh']} of {m}, BY {out['rejected_by']} of {m}."]
    o = ROOT / 'analysis' / 'output' / 'exploratory'; o.mkdir(parents=True, exist_ok=True)
    (o / 'README.md').write_text('\n'.join(lines) + '\n'); (o / 'table.json').write_text(json.dumps(rows, indent=1))
    print('\n'.join(lines))
    return out

if __name__ == '__main__':
    run()
