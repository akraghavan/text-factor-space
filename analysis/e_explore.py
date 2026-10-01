"""Element E exploratory specs (test period Dec 2018 - Jun 2026; each through src/runner.py, counted for BH). Same
construction as the confirmatory run (analysis/e_h3.py and src/e_signals.py, both unchanged); each spec swaps one
ingredient for the duration of the run and restores it:
  delist_0 / delist_m100  E_x_delist_0 / E_x_delist_m100  SPEC §3 delisting delta set to 0 / -100% for every imputed
                          row (primary: -30% NYSE/AMEX, -55% Nasdaq). delist_0 also records the test-period firm-month
                          counts before and after the complete-case drop (the counts do not depend on delta).
  nearest5   E_x_nearest5  peers = each firm's 5 most similar firms on the same BoW null-corrected similarity (so the
                           ~25% of firms with no peer at SIC-3 density stay in the sample)
  stale_y3   E_x_stale_y3  peers from the network 36 months earlier: similarity among the firms' filings as of t-36
                           (universe_at(t-36)), mapped to today's firms by PERMNO; firms absent then have no peers; the
                           SIC-3 density pi_t is applied over the pairs where both firms existed at t-36 (calibrating over
                           all of today's pairs would roughly double the density among the firms that did exist)
Statistic: test-period Fama-MacBeth slope on PEERMOM (same controls, winsorising, z-scoring), NW(3) t, one-sided p."""
import sys, time, json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / 'src', ROOT / 'analysis', ROOT): sys.path.insert(0, str(p))
import numpy as np, pandas as pd
import formation as F, networks as N, delisting, e_h3
from paths import PROCESSED
from tfs_stats.regression import nw_lags_rule, one_sided_p

OUT = ROOT / 'analysis' / 'output' / 'e_explore'

def _base_panel(delta='primary'):
    F._cache.pop('m', None); F._cache['m'], _ = delisting.adjust(F.monthly(), delta=delta)

def _result(name, P, d, extra=None):
    T = d.t.nunique(); L = nw_lags_rule(T); r = e_h3.fm(d, L)
    res = {'slope': float(r['coef'][1]), 'se_nw': float(r['se'][1]), 't_nw': float(r['tstat'][1]), 'nw_lags': L,
           'p_one_sided': float(one_sided_p(r['tstat'][1])), 'months': int(T), 'firm_months': int(len(d)), 'firm_months_before_drop': int(len(P))}
    res.update(extra or {}); OUT.mkdir(parents=True, exist_ok=True)
    (OUT / f'{name}.json').write_text(json.dumps(res, indent=1)); print(name, res)
    return res

def _run_test(name, delta='primary', extra=None):
    _base_panel(delta); P, d = e_h3.panel(*e_h3.TEST)
    return _result(name, P, d, extra)

def delist_0(spec=None):
    _base_panel(0.0); P, d = e_h3.panel(*e_h3.TEST)
    counts = {'test_firm_months_before_complete_case': int(len(P)), 'test_firm_months_after_complete_case': int(len(d)),
              'dropped_missing_by_column': {c: int(P[c].isna().sum()) for c in ['exret'] + e_h3.RHS}}
    (OUT.mkdir(parents=True, exist_ok=True), (OUT / 'test_period_counts.json').write_text(json.dumps(counts, indent=1)))
    return _result('delist_0', P, d, counts)

def delist_m100(spec=None): return _run_test('delist_m100', -1.0)

def _knn_peers(k):
    def peers(S, pi):
        S = np.array(S, dtype=np.float64); np.fill_diagonal(S, -np.inf)
        idx = np.argpartition(-S, k, axis=1)[:, :k]; A = np.zeros(S.shape, bool)
        A[np.arange(len(S))[:, None], idx] = True; np.fill_diagonal(A, False); return A
    return peers

def nearest5(spec=None):
    orig = N.peers; N.peers = _knn_peers(5)
    try: return _run_test('nearest5')
    finally: N.peers = orig

def stale_y3(spec=None):
    orig = N.bow_sim; lk = F.linked().set_index('accession').permno
    def stale(t, accessions, correction=N.CORRECTION, variant=N.NOUNS):
        t = pd.Timestamp(t); t_old = (t.to_period('M') - 36)
        old = F.universe_at(t_old)
        S_old = orig(t_old.to_timestamp(), old.accession.to_numpy(), correction, variant)
        pos = pd.Series(np.arange(len(old)), index=old.permno.to_numpy()); pos = pos[~pos.index.duplicated()]
        now = lk.reindex(np.asarray(accessions)).to_numpy(); k = pos.reindex(now).to_numpy()
        S = np.full((len(now), len(now)), -np.inf); ok = np.isfinite(k); ki = k[ok].astype(int)
        S[np.ix_(ok, ok)] = S_old[np.ix_(ki, ki)]
        return S
    orig_peers = N.peers
    def peers_finite(S, pi):
        i, j = np.triu_indices(len(S), 1); v = S[i, j]; tau = np.quantile(v[np.isfinite(v)], 1 - pi)
        A = S > tau; np.fill_diagonal(A, False); return A
    N.bow_sim = stale; N.peers = peers_finite
    try: return _run_test('stale_y3')
    finally: N.bow_sim = orig; N.peers = orig_peers
