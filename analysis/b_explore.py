"""Element B exploratory specs (not primary; each through src/runner.py, counted for BH). Same sample, modes and empirical
edge as the primary run (analysis/b_primary.py, unchanged): 1 July 2014..2025, 500 firms, T = 756 rolling-beta FF6
residuals, circular-shift edge (200 shifts, seed = year), 1,000 relabellings (seed = year). Only G changes:
  sic3_share       B_x_sic3_share       G = SIC-3 co-membership (0/1, zero diagonal): how much SIC-3 alone aligns
  raw_dense_share  B_x_raw_dense_share  G = dense similarity, not residualised
  nested_sic       B_x_nested_sic       G = dense residualised on nested [1, same SIC-1, SIC-2, SIC-3, SIC-4] (the C
                                        industry controls): the "beyond industry" number (added after the freeze)
  ff48_share       B_x_ff48_share       G = dense residualised on same Fama-French 48 industry (added after the freeze)
  overlap          B_x_subspace_overlap squared principal-angle overlap of the above-edge modes with the top-K eigenvectors
                                        of the dense Gram matrix vs K/N; per-formation relabelling p, pooled by Fisher
  t1008            B_x_T1008            the primary statistic (dense residualised on SIC-3) with T = 1,008 trading days
                                        (q = 500/1,008): formations from the first July whose 1,008-day window lies inside
                                        the rolling-beta residuals (they start Jan 2011, so 1 July 2015) to 2025
Each returns share, binomial p (or overlap stats) and p_one_sided for the BH table. Writes analysis/output/b_explore/."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import networks as N, b_spectra as BS, e_signals as ES
from tfs_stats.rmt import circular_shift_edge
from tfs_stats.network import residualize_on_blocks, residualize_on_dummies, mode_alignment, share_test, subspace_overlap
from tfs_stats.multitest import fisher_combine

OUT = ROOT / 'analysis' / 'output' / 'b_explore'; YEARS = range(2014, 2026); _cache = {}

def _inputs(y):
    if y not in _cache:
        u, Rb, Eb, ndrop, d0, d1 = BS.sample_at(y); T, n = Eb.shape
        Ze = (Eb - Eb.mean(0)) / Eb.std(0); lam, V = np.linalg.eigh(Ze.T @ Ze / T)
        edge, _ = circular_shift_edge(Ze, draws=BS.DRAWS, seed=y)
        G = N.dense(u.accession.to_numpy()).astype(np.float64); np.fill_diagonal(G, 0)
        _cache[y] = (u, V[:, lam > edge], G)
    return _cache[y]

def _share(name, make_G):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); ps, per = [], {}
    for y in YEARS:
        u, U, G = _inputs(y); A, p = mode_alignment(U, make_G(u, G), n_perm=1000, seed=y); ps += list(p)
        per[y] = (int(U.shape[1]), int((p < 0.05).sum()))
    ps = np.array(ps); k, n = int((ps < 0.05).sum()), len(ps); st = share_test(k, n, 0.05)
    res = {'modes': n, 'aligned_p_lt_05': k, 'share': st['share'], 'binomial_p_one_sided': st['pvalue'], 'p_one_sided': st['pvalue'],
           'per_formation': {str(y): v for y, v in per.items()}, 'seconds': round(time.time() - t0)}
    (OUT / f'{name}.json').write_text(json.dumps(res, indent=1)); print(name, {k_: v for k_, v in res.items() if k_ != 'per_formation'})
    return res

def _sic(u, div): return np.floor(u.sic.to_numpy(dtype=float) / div)

def sic3_share(spec=None):
    def mk(u, G):
        s = _sic(u, 10); M = (s[:, None] == s[None, :]).astype(float) * (s[:, None] > 0); np.fill_diagonal(M, 0); return M
    return _share('sic3_share', mk)

def raw_dense_share(spec=None): return _share('raw_dense_share', lambda u, G: G)
def nested_sic(spec=None): return _share('nested_sic', lambda u, G: residualize_on_dummies(G, [_sic(u, 1000), _sic(u, 100), _sic(u, 10), _sic(u, 1)]))
def ff48_share(spec=None): return _share('ff48_share', lambda u, G: residualize_on_blocks(G, ES.ff48(u.sic.to_numpy(dtype=float))))

def overlap(spec=None):
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); rows = []
    for y in YEARS:
        u, U, G = _inputs(y); K = U.shape[1]
        w, W = np.linalg.eigh(G); ov, base, p = subspace_overlap(U, W[:, -K:], n_perm=1000, seed=y)
        rows.append({'year': y, 'K': K, 'overlap': ov, 'random': base, 'ratio': ov / base, 'p': p})
    R = pd.DataFrame(rows); pf = fisher_combine(R.p)
    res = {'mean_overlap': float(R.overlap.mean()), 'mean_random': float(R.random.mean()), 'mean_ratio': float(R.ratio.mean()),
           'formations_p_lt_05': int((R.p < 0.05).sum()), 'fisher_p': pf, 'p_one_sided': pf, 'seconds': round(time.time() - t0)}
    R.to_csv(OUT / 'overlap.csv', index=False); (OUT / 'overlap.json').write_text(json.dumps(res, indent=1)); print('overlap', res)
    return res

def t1008(spec=None):
    import c_panel as C
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True); T = 1008; ps, per = [], {}
    E, dates, _, _ = C._load(); first_day = dates[np.flatnonzero(np.isfinite(np.asarray(E[:600])).any(1))[0]]   # first residual day
    years = [y for y in range(2014, 2026) if dates[dates.searchsorted(pd.Timestamp(f'{y}-07-01')) - T] >= first_day]
    for y in years:
        u, Rb, Eb, ndrop, d0, d1 = BS.sample_at(y, T=T); Tn, Nn = Eb.shape
        Ze = (Eb - Eb.mean(0)) / Eb.std(0); lam, V = np.linalg.eigh(Ze.T @ Ze / Tn)
        edge, _ = circular_shift_edge(Ze, draws=BS.DRAWS, seed=y); U = V[:, lam > edge]
        G = N.dense(u.accession.to_numpy()).astype(np.float64); np.fill_diagonal(G, 0)
        A, p = mode_alignment(U, residualize_on_blocks(G, np.floor(u.sic.to_numpy(dtype=float) / 10)), n_perm=1000, seed=y)
        ps += list(p); per[str(y)] = {'N': int(Nn), 'T': int(Tn), 'modes': int(U.shape[1]), 'p_lt_05': int((p < 0.05).sum()), 'window': f'{d0.date()}..{d1.date()}'}
        print(y, per[str(y)], f'{time.time() - t0:.0f}s', flush=True)
    ps = np.array(ps); k, n = int((ps < 0.05).sum()), len(ps); st = share_test(k, n, 0.05)
    res = {'modes': n, 'aligned_p_lt_05': k, 'share': st['share'], 'binomial_p_one_sided': st['pvalue'], 'p_one_sided': st['pvalue'],
           'T': T, 'q': 500 / T, 'first_year': years[0], 'formations': len(years), 'per_formation': per, 'seconds': round(time.time() - t0)}
    (OUT / 't1008.json').write_text(json.dumps(res, indent=1)); print('t1008', {k_: v for k_, v in res.items() if k_ != 'per_formation'})
    return res
