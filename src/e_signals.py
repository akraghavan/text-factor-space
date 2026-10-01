"""Element E signals (SPEC §9; PREREG draft, Element E): text-peer momentum and its controls at a formation month t.

For firms in formation.universe_at(t) (CRSP month t-1, SPAC months excluded, one PERMNO per PERMCO, a text vintage):
  R_j(t-12, t-1)  compounded monthly return, log1p summed; a firm needs >= 8 of the 12 months (the same observed-share
                  rule as formation.momentum), else NaN (and it is left out of any peer average)
  peermom         equal-weighted mean of R_j(t-12, t-1) over i's text peers: networks.bow_sim (BoW nouns, null-corrected,
                  D11) cut at the SIC-3 density pi_t (networks.peers); self excluded; one PERMNO per PERMCO already
  sic3mom         the same over firms sharing i's historical SIC-3 (CRSP siccd at t-1)
  tnicmom         the same over i's TNIC-3 peers, TNIC year Y used from July Y+1 to June Y+2 (unlagged file); the file
                  ends with FY2023, so for July 2025 - June 2026 the FY2023 network is carried forward (PREREG D14) and
                  the rows are flagged tnic_carried = True
  indmom          value-weighted (ME at t-1) R(t-12, t-1) of i's Fama-French 48 industry (Ken French's Siccodes48
                  mapping, public), including i itself (Moskowitz-Grinblatt convention)
  own controls    log ME (t-1), log B/M (formation.book_to_market), r_{t-1}, R(t-12, t-2) (formation.momentum)
  sample filter   |price| >= $1 at t-1 and at least one text peer (HP)
The dependent variable, the month-t excess return, is attached by the caller, so a caller can hold back months it must
not see (analysis/e_dev.py truncates returns at Nov 2018)."""
import sys, os, zipfile, re; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM
import numpy as np, pandas as pd
import formation as F, networks as N

_cache = {}

def ff48_map():
    """SIC code -> FF-48 industry number, from data/raw/Siccodes48.zip (Ken French data library)."""
    if 'ff48' not in _cache:
        txt = zipfile.ZipFile(RAW / 'Siccodes48.zip').read('Siccodes48.txt').decode('latin1').splitlines()
        rng, ind = [], None
        for line in txt:
            m = re.match(r'^\s*(\d+)\s+\S+', line)
            r = re.match(r'^\s+(\d{4})-(\d{4})', line)
            if r and ind is not None: rng.append((int(r.group(1)), int(r.group(2)), ind))
            elif m and not r: ind = int(m.group(1))
        _cache['ff48'] = rng
    return _cache['ff48']

def ff48(sic):
    out = np.full(len(sic), np.nan)
    for a, b, k in ff48_map(): out[(sic >= a) & (sic <= b)] = k
    return out

def cum_return(t, months_back=12, skip=1, min_obs=8, monthly=None):
    """R(t-months_back, t-skip) per permno, compounded; >= min_obs observed months."""
    t = pd.Period(t, 'M'); m = F.monthly() if monthly is None else monthly
    w = m[(m.ym >= t - months_back) & (m.ym <= t - skip)]
    g = w.groupby('permno').ret; r = np.expm1(g.apply(lambda s: np.log1p(s.dropna()).sum()))
    return r[g.count() >= min_obs]

def _peer_mean(A, v):
    """Equal-weighted mean of v over each row's peers (A boolean n x n); peers with NaN v are left out."""
    ok = np.isfinite(v); Aok = A & ok[None, :]; cnt = Aok.sum(1)
    with np.errstate(invalid='ignore'): out = (Aok @ np.where(ok, v, 0.0)) / cnt
    out[cnt == 0] = np.nan
    return out, cnt

def _tnic():
    if 'tnic' not in _cache: _cache['tnic'] = pd.read_parquet(INTERIM / 'tnic3.parquet')
    return _cache['tnic']

def tnic_pairs(year):
    t = _tnic(); return t[t.year == year]

def signals_at(t, monthly=None):
    """Firm-level signals and controls at formation month t (see module docstring). Returns a DataFrame."""
    t = pd.Period(t, 'M')
    u = F.universe_at(t).reset_index(drop=True)
    m = F.monthly() if monthly is None else monthly
    prev = m[m.ym == t - 1].set_index('permno')
    u['prc'] = prev.mthprc.abs().reindex(u.permno).to_numpy(); u['r_1'] = prev.ret.reindex(u.permno).to_numpy()
    R12 = cum_return(t, 12, 1, monthly=m).reindex(u.permno).to_numpy()
    u['r12_2'] = F.momentum(t).reindex(u.permno).to_numpy(); u['R12'] = R12
    u['log_me'] = np.log(u.me); u['log_bm'] = np.log(F.book_to_market(t).reindex(u.permno)).to_numpy()
    # text peers (D2: BoW nouns, null-corrected) at SIC-3 density
    S = N.bow_sim(t.to_timestamp(), u.accession.to_numpy())
    pi = N.density(u); A = N.peers(S, pi)
    u['peermom'], u['n_peers'] = _peer_mean(A, R12)
    sic3 = np.floor(u.sic.to_numpy(dtype=float) / 10); sic_ok = u.sic.to_numpy(dtype=float) > 0
    As = (sic3[:, None] == sic3[None, :]) & sic_ok[:, None] & sic_ok[None, :]; np.fill_diagonal(As, False)
    u['sic3mom'], _ = _peer_mean(As, R12)
    # TNIC-3: year Y from July Y+1
    Y = t.year - 1 if t.month >= 7 else t.year - 2
    Ymax = int(_tnic().year.max())
    carried = Y > Ymax; Y = min(Y, Ymax)
    lk = F.linked().set_index('accession').gvkey
    gv = lk.reindex(u.accession).to_numpy(); pos = pd.Series(np.arange(len(u)), index=gv); pos = pos[~pos.index.duplicated() & pd.notna(pos.index)]
    g = tnic_pairs(Y); g = g[g.gvkey1.isin(pos.index) & g.gvkey2.isin(pos.index)]
    At = np.zeros_like(A); a, b = pos[g.gvkey1].to_numpy(), pos[g.gvkey2].to_numpy(); At[a, b] = True; At[b, a] = True
    u['tnicmom'], u['n_tnic'] = _peer_mean(At, R12); u['tnic_year'] = Y; u['tnic_carried'] = carried
    # FF-48 industry momentum, value-weighted by ME at t-1, including the firm itself
    u['ff48'] = ff48(u.sic.to_numpy(dtype=float))
    d = u[['ff48', 'me', 'R12']].dropna()
    vw = (d.me * d.R12).groupby(d.ff48).sum() / d.me.groupby(d.ff48).sum()
    u['indmom'] = vw.reindex(u.ff48).to_numpy()
    u['pi'] = pi; u['t'] = t
    return u[(u.prc >= 1) & (u.n_peers > 0)].reset_index(drop=True)
