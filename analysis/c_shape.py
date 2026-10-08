"""C_shape_r2 (diagnostic, SPEC §7 deliverables, D24): the shape and size of H1's effect, not a test. Same months, firms,
outcome, controls and complete-case sample as H1 (analysis/c_h1.py, src/c_panel.py, unchanged).
  1. Mean z by similarity percentile: within each month, rank s_dense over the month's regression pairs into 100
     percentile bins; pool z over months per bin (all pairs, and pairs not in the same SIC-3). Figure + table.
  2. Incremental in-sample R2 of s~: each month's OLS (tfs_stats.regression.ols_qr) with and without s~,
     R2 = 1 - SSR / sum (z - mean z)^2; reported as the mean over months of R2(full) - R2(no s~).
  3. Out-of-sample R2: from the 13th month on, predict month t's z with X_t times the mean of the monthly coefficients
     of months before t (expanding window), with and without s~. R2_OOS = 1 - SSE(model) / SSE(benchmark), the
     benchmark being the expanding mean of past months' z (Campbell-Thompson); Delta R2_OOS = full - no s~.
Writes analysis/output/c_shape/ (README.md, bins.csv is gitignored, fig_z_by_similarity.png). Aggregates only."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import c_panel as C, c_h1 as H
from tfs_stats.regression import ols_qr

OUT = ROOT / 'analysis' / 'output' / 'c_shape'
CTRL = [c for c in H.X_COLS if c != 's_tilde']

def run(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); months = pd.period_range(H.FIRST, H.LAST, freq='M')
    zs, cnt, zs_x, cnt_x = np.zeros(100), np.zeros(100), np.zeros(100), np.zeros(100)
    r2_full, r2_rest, bf, br = [], [], [], []
    sse = {'full': 0.0, 'rest': 0.0, 'bench': 0.0}; zsum, zn = 0.0, 0
    for k, t in enumerate(months):
        f, P = C.c_month(t)
        D = P[['z', 's_dense'] + CTRL].astype(np.float64); D = D[np.isfinite(D.to_numpy()).all(1)]
        D['s_tilde'] = (D.s_dense - D.s_dense.mean()) / D.s_dense.std(); y = D.z.to_numpy()
        b = np.minimum((D.s_dense.rank(method='first').to_numpy() - 1) * 100 // len(D), 99).astype(int)
        zs += np.bincount(b, y, 100); cnt += np.bincount(b, minlength=100)
        x3 = D.same_sic3.to_numpy() == 0; zs_x += np.bincount(b[x3], y[x3], 100); cnt_x += np.bincount(b[x3], minlength=100)
        Xf = np.column_stack([np.ones(len(D)), D[H.X_COLS].to_numpy()]); Xr = np.column_stack([np.ones(len(D)), D[CTRL].to_numpy()])
        if k >= 12:                                                            # out of sample: past coefficients only
            mb_f, mb_r = np.mean(bf, 0), np.mean(br, 0)
            sse['full'] += np.sum((y - Xf @ mb_f) ** 2); sse['rest'] += np.sum((y - Xr @ mb_r) ** 2); sse['bench'] += np.sum((y - zsum / zn) ** 2)
        cf, ef = ols_qr(Xf, y); cr, er = ols_qr(Xr, y); sst = np.sum((y - y.mean()) ** 2)
        r2_full.append(1 - ef @ ef / sst); r2_rest.append(1 - er @ er / sst); bf.append(cf); br.append(cr)
        zsum += y.sum(); zn += len(y)
        if t.month == 1: print(t, f'{time.time() - t0:.0f}s', flush=True)
    bins = pd.DataFrame({'pct_bin': np.arange(1, 101), 'mean_z': zs / cnt, 'pairs': cnt, 'mean_z_not_same_sic3': zs_x / cnt_x, 'pairs_not_same_sic3': cnt_x})
    bins.to_csv(OUT / 'bins.csv', index=False)
    oos_f, oos_r = 1 - sse['full'] / sse['bench'], 1 - sse['rest'] / sse['bench']
    res = {'mean_r2_full': float(np.mean(r2_full)), 'mean_r2_without_s': float(np.mean(r2_rest)),
           'incremental_r2_in_sample': float(np.mean(np.array(r2_full) - np.array(r2_rest))),
           'r2_oos_full': float(oos_f), 'r2_oos_without_s': float(oos_r), 'delta_r2_oos': float(oos_f - oos_r), 'oos_months': len(months) - 12,
           'mean_z_bottom_pct': float(bins.mean_z.iloc[0]), 'mean_z_median_bins_50_51': float(bins.mean_z.iloc[49:51].mean()),
           'mean_z_top_pct': float(bins.mean_z.iloc[-1]), 'mean_z_top_pct_not_same_sic3': float(bins.mean_z_not_same_sic3.iloc[-1]),
           'months': len(months), 'seconds': round(time.time() - t0)}
    _figure(bins); (OUT / 'summary.json').write_text(json.dumps(res, indent=1))
    txt = ['# C_shape_r2 (diagnostic): the shape and size of H1', '',
           f"Months {months[0]}..{months[-1]} (T = {len(months)}), H1's pairs and controls.", '',
           f"- Mean z by dense-similarity percentile (pooled over months): bottom 1% {res['mean_z_bottom_pct']:.3f}, median {res['mean_z_median_bins_50_51']:.3f}, "
           f"top 1% {res['mean_z_top_pct']:.3f}; top 1% excluding same-SIC-3 pairs {res['mean_z_top_pct_not_same_sic3']:.3f}. Figure: `fig_z_by_similarity.png`.",
           f"- In-sample R² of the monthly regressions: {res['mean_r2_full']:.4f} with s̃, {res['mean_r2_without_s']:.4f} without; incremental R² of s̃ "
           f"{res['incremental_r2_in_sample']:.4f} (mean over months).",
           f"- Out-of-sample R² (months 13..{len(months)}, expanding-mean coefficients, benchmark = expanding mean of z): {res['r2_oos_full']:.4f} with s̃, "
           f"{res['r2_oos_without_s']:.4f} without; ΔR²_OOS = {res['delta_r2_oos']:.4f}.", '', f"Runtime {res['seconds']} s."]
    (OUT / 'README.md').write_text('\n'.join(txt) + '\n'); print('\n'.join(txt))
    return res

def _figure(bins):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(bins.pct_bin, bins.mean_z, color='#1f4e79', lw=1.8, label='all pairs')
    ax.plot(bins.pct_bin, bins.mean_z_not_same_sic3, color='#c55a11', lw=1.4, ls='--', label='pairs not in the same SIC-3')
    ax.set_xlabel('dense text similarity, within-month percentile'); ax.set_ylabel('mean Fisher z of residual correlation')
    ax.set_title('Residual comovement by text similarity (165 months, top 1,000 firms)', fontsize=10, loc='left')
    ax.grid(alpha=0.3); ax.legend(frameon=False); fig.tight_layout(); fig.savefig(OUT / 'fig_z_by_similarity.png', dpi=150); plt.close(fig)
