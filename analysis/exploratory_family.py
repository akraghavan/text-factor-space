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
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(ROOT / 'src'))
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
