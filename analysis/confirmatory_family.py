"""Holm decision for the confirmatory family {H1, H3} (PREREG "Confirmatory family", frozen at d1df5c7). Reads the latest
status-'ok' runner record of each confirmatory spec from runs.log (nothing is re-estimated) and applies
tfs_stats.multitest.holm at alpha = 0.05 (thresholds 0.025 for the smaller p, 0.05 for the larger).
Writes analysis/output/confirmatory/README.md; returns the decisions. Run: python src/runner.py run Confirmatory_family_holm"""
import sys, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT))
from tfs_stats.multitest import holm

FAMILY = [('H1', 'C_H1_dense_bbar', 'b_bar', 't_nw'), ('H3', 'E_H3_bow_peermom_test', 'slope_test', 't_nw')]

def run(spec=None):
    recs = [json.loads(l) for l in (ROOT / 'runs.log').read_text().splitlines()]
    latest = {}
    for r in recs:
        if r.get('status') == 'ok' and r.get('family') == 'confirmatory': latest[r['spec']] = r
    rows = [(h, sid, latest[sid]) for h, sid, _, _ in FAMILY]
    p = [r['result']['p_one_sided'] for _, _, r in rows]
    h = holm(p, alpha=0.05)
    out = {h_: {'spec': sid, 'estimate': r['result'][est], 't_nw': r['result'][tk], 'p_one_sided': r['result']['p_one_sided'],
                'holm_threshold': float(th), 'reject_null': bool(rej), 'run_time': r['time'], 'commit': r['commit']}
           for (h_, sid, r), (_, _, est, tk), th, rej in zip(rows, FAMILY, h['thresholds'], h['reject'])}
    lines = ['# Confirmatory family {H1, H3}: Holm at 5%', '', 'From the runner records in `runs.log` (no re-estimation); `tfs_stats.multitest.holm`.', '',
             '| Hypothesis | Spec | Estimate | NW t | one-sided p | Holm threshold | Null rejected |', '|---|---|---|---|---|---|---|']
    for k, v in out.items():
        lines.append(f"| {k} | `{v['spec']}` | {v['estimate']:.4g} | {v['t_nw']:.2f} | {v['p_one_sided']:.3g} | {v['holm_threshold']:.3f} | {'yes' if v['reject_null'] else 'no'} |")
    lines += ['', 'Estimates: H1 b̄ per SD of dense similarity (Fisher-z units); H3 test-period slope per SD of PEERMOM (monthly return).']
    o = ROOT / 'analysis' / 'output' / 'confirmatory'; o.mkdir(parents=True, exist_ok=True); (o / 'README.md').write_text('\n'.join(lines) + '\n')
    print('\n'.join(lines))
    return out

if __name__ == '__main__':
    run()
