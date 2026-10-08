"""Element E exploratory specs, the remaining pre-listed ones plus one post-freeze addition (SPEC D23, D24; each through
src/runner.py, counted for BH). Same sample (price >= $1, >= 1 BoW peer), controls, winsorising, z-scoring, test
period (Dec 2018 - Jun 2026) and Fama-MacBeth as H3 (analysis/e_h3.py, src/e_signals.py, both unchanged); each spec
replaces PEERMOM (or the sample) for the duration of the run. Horizon returns need 2/3 of their months.
  sim_weighted    E_x_sim_weighted    peer weights w_ij proportional to (s_ij - tau_t)+ on the BoW null-corrected
                                      similarity (tau_t = the density cut), peers with no R(t-12, t-1) left out
  h_6_1           E_x_h_6_1           peer mean of R(t-6, t-1) (>= 4 of 6 months)
  h_12_7          E_x_h_12_7          peer mean of R(t-12, t-7) (>= 4 of 6)
  grundy_martin   E_x_grundy_martin   peer mean of R(t-12, t-2) (>= 8 of 11; the headline) and of r(t-1), both on the RHS
  placebo_24_13   E_x_placebo_24_13   peer mean of R(t-24, t-13) (>= 8 of 12); no predicted sign, so its BH p is two-sided
  text_only       E_x_text_only       peers in BoW but not SIC-3       } NaN when the set is empty, and the complete-case
  sic_only        E_x_sic_only        peers in SIC-3 but not BoW       } rule drops those rows; firm-months kept are
  both            E_x_both            peers in both                    } reported
  dense_only      E_x_dense_only      dense peers (universe dense similarity at SIC-3 density) not in TNIC-3 or SIC-3
  perm_stratified E_x_perm_stratified the stratified-substitution null (SPEC §9 (a)), see perm_stratified below
  post_sep2023    E_x_post_sep2023    H3 as registered on formation months Oct 2023 - Jun 2026, NW by the rule
  sich            E_x_sich            pi_t, SIC-3 peer momentum and the FF-48 assignment from Compustat sich
                                      (src/industry.py, fallback siccd)
  nyse20          E_x_nyse20          H3 without firms below the NYSE 20th percentile of ME at t-1 (added after the freeze)
Every FM entry saves its monthly slope series (output/e_explore3/series/<spec>.json) for Romano-Wolf (D25).
Mechanics: signals_at is wrapped for the run; the wrapper sees the BoW similarity S, the density pi and the three peer
matrices signals_at builds (BoW A, SIC-3, TNIC-3, in that order), all indexed by universe_at(t), and overwrites columns
of signals_at's output before e_h3.panel winsorises, z-scores and drops incomplete rows. Writes
analysis/output/e_explore3/. Aggregates only."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
from scipy import stats
import formation as F, networks as N, e_signals as ES, e_h3, e_explore as EX, industry, series_out
from tfs_stats.regression import fama_macbeth, nw_lags_rule, one_sided_p

OUT = ROOT / 'analysis' / 'output' / 'e_explore3'

def _panel(make=None, first=None, last=None, rhs=None, filt=None, universe=None):
    """e_h3.panel with signals_at wrapped. make(t, univ, cap) -> {column: array aligned with univ} overwrites columns;
    filt(t, univ, u) -> u restricts the sample; universe(t, u) -> u replaces universe_at's frame (sich)."""
    EX._base_panel('primary')
    o_sig, o_peers, o_pm, o_ua, o_rhs = ES.signals_at, N.peers, ES._peer_mean, F.universe_at, e_h3.RHS
    cap = {}
    def peers(S, pi):
        A = o_peers(S, pi); cap.update(S=S, pi=pi, A=A); return A
    def pm(A, v):
        cap.setdefault('mats', []).append(A); return o_pm(A, v)
    def ua(t, *a, **k): return universe(t, o_ua(t, *a, **k))
    def sig(t, monthly=None):
        t = pd.Period(t, 'M'); cap.clear(); u = o_sig(t); univ = F.universe_at(t).reset_index(drop=True)
        assert cap['mats'][0] is cap['A'] and len(cap['mats']) == 3                    # BoW, SIC-3, TNIC-3, in that order
        if make is not None:
            for c, v in make(t, univ, cap).items(): u[c] = pd.Series(v, index=univ.permno.to_numpy()).reindex(u.permno).to_numpy()
        return u if filt is None else filt(t, univ, u)
    N.peers, ES._peer_mean, ES.signals_at = peers, pm, sig
    if universe is not None: F.universe_at = ua
    if rhs is not None: e_h3.RHS = rhs
    try: P, d = e_h3.panel(first or e_h3.TEST[0], last or e_h3.TEST[1])
    finally: N.peers, ES._peer_mean, ES.signals_at, F.universe_at, e_h3.RHS = o_peers, o_pm, o_sig, o_ua, o_rhs
    return P, d

def _result(name, P, d, spec, rhs=None, extra=None):
    rhs = rhs or e_h3.RHS; T = d.t.nunique(); L = nw_lags_rule(T)
    r = fama_macbeth(d.exret.to_numpy(), d[rhs].to_numpy(), d.t.astype(str).to_numpy(), nw_lags=L)
    series_out.save(OUT, spec, name, r['periods'], r['lambdas'][:, 1]); t = float(r['tstat'][1])
    res = {'slope': float(r['coef'][1]), 'se_nw': float(r['se'][1]), 't_nw': t, 'nw_lags': L, 'p_one_sided': float(one_sided_p(t)),
           'p_two_sided': float(2 * stats.norm.sf(abs(t))), 'months': int(T), 'first': str(d.t.min()), 'last': str(d.t.max()),
           'firm_months': int(len(d)), 'firm_months_before_drop': int(len(P))}
    if extra: res.update(extra(r) if callable(extra) else extra)
    OUT.mkdir(parents=True, exist_ok=True); (OUT / f'{name}.json').write_text(json.dumps(res, indent=1)); print(name, res)
    return res

def _R(t, back, skip, min_obs, univ): return ES.cum_return(t, back, skip, min_obs=min_obs).reindex(univ.permno).to_numpy()
def _pmean(A, v): return ES._peer_mean(A, v)[0]

def sim_weighted(spec=None):
    def make(t, univ, cap):
        S, A, pi = cap['S'], cap['A'], cap['pi']; i, j = np.triu_indices(len(S), 1); tau = np.quantile(S[i, j], 1 - pi)  # as networks.peers
        R = _R(t, 12, 1, 8, univ); ok = np.isfinite(R); W = np.where(A & ok[None, :], S - tau, 0.0); w = W.sum(1)
        with np.errstate(invalid='ignore', divide='ignore'): v = (W @ np.where(ok, R, 0.0)) / w
        v[w <= 0] = np.nan; return {'peermom': v}
    P, d = _panel(make); return _result('sim_weighted', P, d, spec)

def _horizon(name, back, skip, min_obs, spec):
    P, d = _panel(lambda t, univ, cap: {'peermom': _pmean(cap['A'], _R(t, back, skip, min_obs, univ))})
    return _result(name, P, d, spec)

def h_6_1(spec=None): return _horizon('h_6_1', 6, 1, 4, spec)
def h_12_7(spec=None): return _horizon('h_12_7', 12, 7, 4, spec)
def placebo_24_13(spec=None): return _horizon('placebo_24_13', 24, 13, 8, spec)

def grundy_martin(spec=None):
    rhs = e_h3.RHS + ['peer_r1']
    make = lambda t, univ, cap: {'peermom': _pmean(cap['A'], _R(t, 12, 2, 8, univ)), 'peer_r1': _pmean(cap['A'], _R(t, 1, 1, 1, univ))}
    P, d = _panel(make, rhs=rhs)
    return _result('grundy_martin', P, d, spec, rhs=rhs, extra=lambda r: {'peer_r1_slope': float(r['coef'][-1]), 'peer_r1_t_nw': float(r['tstat'][-1])})

def _split(name, which, spec):
    def make(t, univ, cap):
        A, As = cap['mats'][0], cap['mats'][1]
        M = {'text_only': A & ~As, 'sic_only': As & ~A, 'both': A & As}[which]
        return {'peermom': _pmean(M, _R(t, 12, 1, 8, univ)), 'n_set': M.sum(1)}
    P, d = _panel(make); return _result(name, P, d, spec, extra={'mean_set_size': float(d.n_set.mean())})

def text_only(spec=None): return _split('text_only', 'text_only', spec)
def sic_only(spec=None): return _split('sic_only', 'sic_only', spec)
def both(spec=None): return _split('both', 'both', spec)

def dense_only(spec=None):
    o_peers = N.peers                                                              # the unwrapped networks.peers
    def make(t, univ, cap):
        Ad = o_peers(N.dense(univ.accession.to_numpy()), cap['pi'])                # dense peers at SIC-3 density, whole universe
        M = Ad & ~(cap['mats'][2] | cap['mats'][1])
        return {'peermom': _pmean(M, _R(t, 12, 1, 8, univ)), 'n_set': M.sum(1)}
    P, d = _panel(make); return _result('dense_only', P, d, spec, extra={'mean_set_size': float(d.n_set.mean())})

def post_sep2023(spec=None):
    P, d = _panel(first=pd.Period('2023-10', 'M'), last=e_h3.TEST[1]); return _result('post_sep2023', P, d, spec)

def sich(spec=None):
    share = []
    def universe(t, u):
        w = industry.with_sich(u, t); share.append(float((w.sic_source == 'sich').mean())); return w
    P, d = _panel(universe=universe)
    return _result('sich', P, d, spec, extra={'share_universe_on_sich': float(np.mean(share))})

def nyse20(spec=None):
    def filt(t, univ, u):
        thr = np.percentile(univ.loc[univ.primaryexch == 'N', 'me'], 20); return u[u.me >= thr].reset_index(drop=True)
    P, d = _panel(filt=filt); return _result('nyse20', P, d, spec)

# ---------------------------------------------------------------- the stratified-substitution null
M1, M2, M3 = np.uint64(0x9E3779B97F4A7C15), np.uint64(0xBF58476D1CE4E5B9), np.uint64(0x94D049BB133111EB)

def _mix(x):
    """splitmix64 finaliser on a uint64 array (wraps mod 2^64)."""
    x = x + M1; x = (x ^ (x >> np.uint64(30))) * M2; x = (x ^ (x >> np.uint64(27))) * M3
    return x ^ (x >> np.uint64(31))

def _uniform(draw, a, b):
    """u in [0, 1) from a hash of (draw, a, b): the same triple always gives the same u, without a generator per pair."""
    h = _mix(_mix(_mix(np.full(len(a), draw, dtype=np.uint64)) ^ a.astype(np.uint64)) ^ b.astype(np.uint64))
    return (h >> np.uint64(11)).astype(np.float64) * 2.0 ** -53

def perm_stratified(spec=None, n_perm=999):
    """E_x_perm_stratified (SPEC §9 null (a)). Each draw replaces every counted peer j of firm i (a BoW peer with an
    R(t-12, t-1)) by a firm from j's cell at t-1: FF-48 industry (unmapped SIC = one cell) x NYSE size tercile (NYSE
    universe firms' ME terciles that month), among universe firms with an R(t-12, t-1), never i itself (the universe
    has one security per company, so never a same-company firm either). The member is the one at index floor(u x size)
    of the cell sorted by permno, u = hash(draw, i's 10-K accession, permno_j): a substitute stays fixed while i's
    vintage, the link and the cell are unchanged. PEERMOM is recomputed, winsorised and z-scored as in H3, and the FM t
    recorded; p = (1 + #{t_b >= t_obs}) / (B + 1). The null keeps each peer's industry and size and breaks only the
    tie to the specific text-linked firm."""
    t0 = time.time(); keep = {}
    def make(t, univ, cap):
        keep[t] = (cap['A'], univ[['permno', 'me', 'primaryexch', 'sic', 'accession']].copy(), _R(t, 12, 1, 8, univ)); return {}
    P, d = _panel(make)
    d = d.sort_values('t', kind='stable').reset_index(drop=True); L = nw_lags_rule(d.t.nunique())
    t_obs = float(fama_macbeth(d.exret.to_numpy(), d[e_h3.RHS].to_numpy(), d.t.astype(str).to_numpy(), nw_lags=L)['tstat'][1])
    acc_id = pd.Index(pd.unique(np.concatenate([k[1].accession.to_numpy() for k in keep.values()])))
    rows, cells, owns, accs, perms, Rall, order_all, first_all, size_all, cnt_all, true_pm, starts = [], [], [], [], [], [], [], [], [], [], [], [0]
    U = C0 = D0 = O0 = 0                                     # offsets: universe rows, cells, regression rows, cell members
    for t, g in d.groupby('t', sort=True):
        A, univ, R = keep[t]; ok = np.isfinite(R); n = len(univ)
        ff = ES.ff48(univ.sic.to_numpy(dtype=float)); ff = np.where(np.isfinite(ff), ff, 0).astype(int)
        bp = np.percentile(univ.loc[univ.primaryexch == 'N', 'me'], [100 / 3, 200 / 3]); terc = np.searchsorted(bp, univ.me.to_numpy(), side='right')
        cell = ff * 3 + terc; cell[~ok] = -1; cid, cell = np.unique(cell, return_inverse=True); cell = cell - (1 if cid[0] == -1 else 0)
        nc = int(cell.max()) + 1; order = np.lexsort((univ.permno.to_numpy(), cell))[(~ok).sum():]                # members by (cell, permno)
        size = np.bincount(cell[ok], minlength=nc); first = np.r_[0, np.cumsum(size)[:-1]]
        pos = pd.Index(univ.permno).get_indexer(g.permno.to_numpy()); rr, cc = np.nonzero(A[pos] & ok[None, :])
        cnt = np.bincount(rr, minlength=len(pos)); obs = np.bincount(rr, R[cc], minlength=len(pos)) / cnt
        assert np.allclose(obs, P.set_index(['t', 'permno']).loc[[(t, q) for q in g.permno], 'peermom'].to_numpy())   # = e_signals' PEERMOM
        rows.append(rr + D0); cells.append(cell[cc] + C0); owns.append(pos[rr] + U)
        accs.append(acc_id.get_indexer(univ.accession.to_numpy()[pos[rr]])); perms.append(univ.permno.to_numpy()[cc])
        Rall.append(R); order_all.append(order + U); first_all.append(first + O0); size_all.append(size); cnt_all.append(cnt); true_pm.append(obs)
        U += n; C0 += nc; D0 += len(pos); O0 += len(order); starts.append(D0)
    rows, cells, owns, accs, perms = map(np.concatenate, (rows, cells, owns, accs, perms))
    Rall, order_all, first_all, size_all, cnt_all, true_pm = map(np.concatenate, (Rall, order_all, first_all, size_all, cnt_all, true_pm))
    starts = np.array(starts); X = d[e_h3.RHS].to_numpy().copy(); y = d.exret.to_numpy(); tt = d.t.astype(str).to_numpy()
    tb = np.empty(n_perm); corr = []
    from e_explore2 import _zwin_blocks
    for b in range(n_perm):
        u = _uniform(b + 1, accs, perms); sz = size_all[cells]; idx = np.minimum((u * sz).astype(np.int64), sz - 1)
        k = order_all[first_all[cells] + idx]; clash = k == owns
        k[clash] = order_all[first_all[cells[clash]] + (idx[clash] + 1) % sz[clash]]
        pm = np.bincount(rows, Rall[k], minlength=len(y)) / cnt_all
        if b < 20: corr.append(np.corrcoef(pm, true_pm)[0, 1])
        X[:, 0] = _zwin_blocks(pm, starts); tb[b] = fama_macbeth(y, X, tt, nw_lags=L)['tstat'][1]
        if b % 100 == 0: print('draw', b, f'{time.time() - t0:.0f}s', flush=True)
    res = {'t_obs': t_obs, 'p_one_sided': float((1 + np.sum(tb >= t_obs)) / (n_perm + 1)), 'mean_t_perm': float(tb.mean()),
           'sd_t_perm': float(tb.std()), 'p95_t_perm': float(np.quantile(tb, 0.95)), 'n_perm': n_perm, 'nw_lags': L,
           'mean_corr_random_vs_true_peermom': float(np.mean(corr)), 'firm_months': int(len(d)), 'slots_per_draw': int(len(rows)),
           'seconds': round(time.time() - t0)}
    OUT.mkdir(parents=True, exist_ok=True); (OUT / 'perm_stratified.json').write_text(json.dumps(res, indent=1)); print('perm_stratified', res)
    return res
