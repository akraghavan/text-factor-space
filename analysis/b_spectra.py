"""Element B inputs and spectra (SPEC §6), before the PREREG freeze. Computes the noise edges and the spectra of raw and
residual correlation matrices; deliberately does NOT compute any text alignment (B's primary statistic).

Per annual formation (1 July 2014..2025; the PREREG draft [PROPOSED] 2013 start is infeasible with rolling betas: residuals start Jan 2011): the 500 largest universe firms at the end of June
(SPAC months excluded) with complete returns and complete out-of-sample FF6 residuals (src/c_panel.py: rolling betas
re-estimated each month on the prior 252 days, SPEC §6.2) over the T = 756 trading days before 1 July; of any pair
with raw return correlation > 0.95, the one with the higher log daily Amihud illiquidity is dropped (candidates are
taken in size order until 500 remain). Standardised residuals Z, C = Z'Z/T.
Edges (tfs_stats.rmt): MP with sigma2 = 1 and q = N/T; MP with the iterated sigma2; circular-shift empirical edge
(95th percentile of the top eigenvalue over 200 shifted nulls, the primary edge in the PREREG draft). The residuals are
out-of-sample (betas from earlier windows), so no K + 1 degrees of freedom are used up inside the window and q = N/T.
Writes analysis/output/b_spectra/README.md and fig_spectrum.png (aggregates only)."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src')); sys.path.insert(0, str(ROOT))
import numpy as np, pandas as pd
import formation as F, c_panel as C
from tfs_stats.rmt import mp_edges, mp_sigma2_iterated, circular_shift_edge, ipr

N_TARGET, T_WIN, DRAWS = 500, 756, 200
OUT = ROOT / 'analysis' / 'output' / 'b_spectra'; OUT.mkdir(parents=True, exist_ok=True)

def sample_at(y):
    t = pd.Period(f'{y}-07', 'M'); u = F.universe_at(t).sort_values('me', ascending=False)
    E, dates, cols, _ = C._load(); dw, cw, R = F.daily_wide()
    k1 = dates.searchsorted(t.to_timestamp()); k0 = k1 - T_WIN
    pos = cols.get_indexer(pd.Index(u.permno)); rp = cw.get_indexer(pd.Index(u.permno))
    ok = (pos >= 0) & (rp >= 0)
    u, pos, rp = u[ok], pos[ok], rp[ok]
    Eb = np.asarray(E[k0:k1][:, pos], dtype=np.float64); Rb = R[k0:k1][:, rp].astype(np.float64)
    full = np.isfinite(Eb).all(0) & np.isfinite(Rb).all(0)
    u, Eb, Rb = u[full].reset_index(drop=True), Eb[:, full], Rb[:, full]
    cand = min(len(u), N_TARGET + 100); Cr = np.corrcoef(Rb[:, :cand], rowvar=False)
    ill = F.amihud_daily(t, u.permno.to_numpy()[:cand]); ill = ill.reindex(u.permno.to_numpy()[:cand]).fillna(np.inf).to_numpy()
    drop = set(); ii, jj = np.where(np.triu(Cr, 1) > 0.95)
    for a, b in zip(ii, jj):
        if a in drop or b in drop: continue
        drop.add(a if ill[a] > ill[b] else b)
    keep = [k for k in range(cand) if k not in drop][:N_TARGET]
    return u.iloc[keep], Rb[:, keep], Eb[:, keep], len(drop), dates[k0], dates[k1 - 1]

if __name__ == '__main__':
    t0 = time.time(); rows = []; spec = {}
    for y in range(2014, 2026):     # first 756-day window of out-of-sample residuals (from Jan 2011) ends June 2014
        u, Rb, Eb, ndrop, d0, d1 = sample_at(y); T, N = Eb.shape; q = N / T
        Zr = (Rb - Rb.mean(0)) / Rb.std(0); Ze = (Eb - Eb.mean(0)) / Eb.std(0)
        lr = np.linalg.eigvalsh(Zr.T @ Zr / T); le, Ve = np.linalg.eigh(Ze.T @ Ze / T)
        lo, hi1 = mp_edges(q); s2, hi_it, n_it, conv = mp_sigma2_iterated(le, q); s2r, hi_r, n_r, convr = mp_sigma2_iterated(lr, q)
        emp, _ = circular_shift_edge(Ze, draws=DRAWS, seed=y)
        above = le > emp; ip = ipr(Ve[:, above]) if above.any() else np.array([])
        rows.append({'formation': f'{y}-07-01', 'window': f'{d0.date()}..{d1.date()}', 'N': N, 'dropped >0.95': ndrop, 'q': round(q, 3),
                     'raw λ1': round(lr[-1], 1), 'raw λ1/N': f'{lr[-1] / N:.1%}', 'raw above MP(iter)': n_r,
                     'resid λ1': round(le[-1], 2), 'MP λ+ (σ²=1)': round(hi1, 3), 'MP λ+ (iter σ²)': round(hi_it, 3), 'iter converged': conv, 'empirical edge': round(emp, 3),
                     'resid above MP(σ²=1)': int((le > hi1).sum()), 'resid above empirical': int(above.sum()),
                     'median IPR above edge × N': round(float(np.median(ip) * N), 2) if len(ip) else '—', 'IPR noise ×N': round(3 * N / (N + 2), 2)})
        spec[y] = (lr, le, q, hi1, emp)
        print(rows[-1], f'{time.time() - t0:.0f}s', flush=True)
    r = pd.DataFrame(rows)
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    INK, INK2, GRID, SURF, BLUE = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb', '#2a78d6'
    y = 2019; lr, le, q, hi1, emp = spec[y]
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2)); x = np.linspace(mp_edges(q)[0], hi1, 400)
    dens = np.sqrt(np.maximum((hi1 - x) * (x - mp_edges(q)[0]), 0)) / (2 * np.pi * q * x)
    for ax, lam, title in ((axs[0], lr, f'Raw returns (λ1 = {lr[-1]:.0f} off the scale)'), (axs[1], le, 'Out-of-sample FF6 residuals')):
        ax.set_facecolor(SURF); ax.hist(lam[lam < 6], bins=80, density=True, color=BLUE, alpha=0.85, label='sample eigenvalues')
        ax.plot(x, dens, color=INK, lw=1.5, label='Marchenko–Pastur (σ² = 1)'); ax.axvline(hi1, color=INK2, ls=(0, (4, 3)), lw=1)
        ax.annotate(f'λ+ = {hi1:.2f}', (hi1, ax.get_ylim()[1] * 0.9), xytext=(4, 0), textcoords='offset points', fontsize=8, color=INK2)
        if ax is axs[1]:
            ax.axvline(emp, color=INK, lw=1); ax.annotate(f'empirical edge {emp:.2f}', (emp, ax.get_ylim()[1] * 0.75), xytext=(4, 0), textcoords='offset points', fontsize=8, color=INK)
        ax.set_title(title, loc='left', fontsize=10, color=INK); ax.set_xlabel('eigenvalue', color=INK2, fontsize=9); ax.set_ylabel('density', color=INK2, fontsize=9)
        ax.grid(axis='y', color=GRID, lw=0.8); ax.set_axisbelow(True)
        for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
        ax.tick_params(colors=INK2, labelsize=8)
    axs[0].legend(frameon=False, fontsize=8)
    fig.suptitle(f'Correlation spectrum, N = 500, T = 756 days to 30 June {y}', x=0.01, ha='left', fontsize=11, color=INK)
    fig.patch.set_facecolor(SURF); fig.tight_layout(); fig.savefig(OUT / 'fig_spectrum.png', dpi=160); plt.close(fig)
    md = lambda d: '\n'.join(['| ' + ' | '.join(map(str, d.columns)) + ' |', '|' + '---|' * d.shape[1]] + ['| ' + ' | '.join(str(v) for v in x) + ' |' for x in d.itertuples(index=False)])
    txt = ['# Element B: inputs and spectra (no text alignment before the PREREG freeze)', '', 'Generated by `analysis/b_spectra.py`.', '', md(r), '',
           'raw above MP(iter): eigenvalues of the raw-return correlation matrix above the MP edge with the iterated σ². '
           'Residual columns use out-of-sample FF6 residuals (rolling betas). Empirical edge: 95th percentile of the top eigenvalue '
           f'over {DRAWS} circular-shift nulls. IPR × N: 1 = spread evenly over all N stocks, 3 = random vector, large = localised.', '',
           '![spectrum](fig_spectrum.png)', '', f'Runtime {time.time() - t0:.0f} s.']
    (OUT / 'README.md').write_text('\n'.join(txt) + '\n'); print(r.to_string(index=False))
