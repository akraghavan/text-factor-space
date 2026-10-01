"""B primary statistic (specs.yaml B_primary_alignment_share; PREREG Element B, frozen at d1df5c7). Run only via
    python src/runner.py run B_primary_alignment_share
Per annual formation 1 July 2014..2025: the B sample of analysis/b_spectra.sample_at (500 largest universe firms with
complete returns and rolling-beta FF6 residuals over T = 756 days; pairs with return correlation > 0.95 thinned by
Amihud), standardised residual correlation C = Z'Z/T, eigenvectors u_k, and the empirical noise edge
(tfs_stats.rmt.circular_shift_edge, 200 shifts, seed = year, as in the diagnostic run). For each mode above the edge:
A_k = u_k' G~ u_k, G~ = the dense similarity of the 500 firms (src/networks.dense) residualised on SIC-3
co-membership with a zero diagonal (tfs_stats.network.residualize_on_blocks), and its one-sided p from 1,000 joint
row/column relabellings (tfs_stats.network.mode_alignment, seed = year).
Primary statistic: the share of above-edge modes, pooled over the 12 formations, with p < 0.05; decision: share > 5%
with a one-sided binomial p < 0.05 (tfs_stats.network.share_test). IPR x N of each above-edge mode is reported beside it.
Writes analysis/output/b_primary/README.md; returns the summary."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import networks as N, b_spectra as BS
from tfs_stats.rmt import circular_shift_edge, ipr
from tfs_stats.network import residualize_on_blocks, mode_alignment, share_test

OUT = ROOT / 'analysis' / 'output' / 'b_primary'
YEARS = range(2014, 2026)

def run(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); rows, per = [], []
    for y in YEARS:
        u, Rb, Eb, ndrop, d0, d1 = BS.sample_at(y); T, Nn = Eb.shape
        Ze = (Eb - Eb.mean(0)) / Eb.std(0); lam, V = np.linalg.eigh(Ze.T @ Ze / T)
        edge, _ = circular_shift_edge(Ze, draws=BS.DRAWS, seed=y)
        above = lam > edge; U = V[:, above]
        G = N.dense(u.accession.to_numpy()).astype(np.float64); np.fill_diagonal(G, 0)
        Gt = residualize_on_blocks(G, np.floor(u.sic.to_numpy(dtype=float) / 10))
        A, p = mode_alignment(U, Gt, n_perm=1000, seed=y); ip = ipr(U) * Nn
        per.append({'formation': f'{y}-07-01', 'modes above edge': int(above.sum()), 'p < 0.05': int((p < 0.05).sum()),
                    'median IPR x N': round(float(np.median(ip)), 2)})
        rows += [{'year': y, 'lambda': float(l), 'A': float(a), 'p': float(q), 'ipr_N': float(i)} for l, a, q, i in zip(lam[above], A, p, ip)]
        print(per[-1], f'{time.time() - t0:.0f}s', flush=True)
    R = pd.DataFrame(rows); k, n = int((R.p < 0.05).sum()), len(R); st = share_test(k, n, 0.05)
    res = {'modes': n, 'aligned_p_lt_05': k, 'share': st['share'], 'binomial_p_one_sided': st['pvalue'],
           'decision_text_beyond_industry': bool(st['share'] > 0.05 and st['pvalue'] < 0.05), 'formations': len(YEARS)}
    pt = pd.DataFrame(per)
    md = lambda df: '\n'.join(['| ' + ' | '.join(df.columns) + ' |', '|' + '---|' * df.shape[1]] + ['| ' + ' | '.join(str(v) for v in r) + ' |' for r in df.itertuples(index=False)])
    txt = ['# B primary: residual modes aligned with text beyond industry', '',
           'Spec `B_primary_alignment_share`, PREREG frozen at d1df5c7, run through `src/runner.py`.', '',
           f"**{k} of {n} above-edge residual modes ({res['share']:.1%}) have beyond-industry dense alignment with p < 0.05; "
           f"one-sided binomial p vs 5% = {res['binomial_p_one_sided']:.3g}. Decision (share > 5% and p < 0.05): "
           f"{'text structure beyond industry' if res['decision_text_beyond_industry'] else 'not shown'}.**", '',
           md(pt), '', 'Modes pooled over 12 overlapping annual windows are not independent; the binomial test treats them as if they were (as registered).', '',
           f'Runtime {time.time() - t0:.0f} s.']
    (OUT / 'README.md').write_text('\n'.join(txt) + '\n'); print('\n'.join(txt))
    return res

if __name__ == '__main__':
    run()
