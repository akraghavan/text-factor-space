"""Text networks for Elements B, C and E at a formation month (D4: monthly; text layer = tag text-layer-v1).

One builder so every element uses the same definitions:
  dense    centred, name-masked bge-small embeddings (D2: primary for H1 comovement)
  bow      bag-of-words nouns + proper nouns, point-in-time vocabulary, degree-corrected with CORRECTION (D11: 'null',
           s - m_i m_j / median(m)); D2: primary for H3 predictability
  bow_raw  the same without the correction (robustness only)
Density calibration (SPEC §5): pi = share of pairs with the same historical SIC-3; each network is cut at its (1 - pi)
quantile, so all networks have SIC-3 density. Firms come from formation.universe_at(t) (SPAC months excluded, D8)."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import INTERIM
import glob
import numpy as np, pandas as pd
import bow

CORRECTION = 'null'                       # D11 (adopted 27 Sep 2026). Do not change after the PREREG freeze.
NOUNS = 'nouns'                           # BoW variant: nouns + proper nouns (HP)
_cache = {}

def _emb():
    if 'emb' not in _cache:
        e = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(str(INTERIM / 'emb' / 'shard_*.parquet')))).drop_duplicates('accession')
        _cache['emb'] = (np.stack(e.emb.to_numpy()).astype(np.float32), pd.Series(np.arange(len(e)), index=e.accession.to_numpy()))
    return _cache['emb']

def _bow():
    if 'bow' not in _cache:
        B = bow.load(); lk = pd.read_parquet(INTERIM / 'tenk_linked.parquet', columns=['accession'])
        pos = pd.Series(np.arange(len(B['rows'])), index=B['rows'].accession.to_numpy())
        _cache['bow'] = (B, pos, B['rows'].accession.isin(set(lk.accession)))
    return _cache['bow']

def dense(accessions):
    """Centred (cross-sectional mean removed), unit-normalised embeddings -> n x n cosine matrix."""
    E, pos = _emb(); V = E[pos.loc[np.asarray(accessions)].to_numpy()]
    V = V - V.mean(0); V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-12
    return V @ V.T

def bow_sim(t, accessions, correction=CORRECTION, variant=NOUNS):
    """BoW cosine with the vocabulary of linked filings in [t - 365 d, t), then bow.degree_correct(., correction)."""
    B, pos, pool = _bow()
    X, _ = bow.formation_vectors(B, pd.Timestamp(t), pos.loc[np.asarray(accessions)].to_numpy(), pool, variant)
    S = (X @ X.T).toarray().astype(np.float32)
    return bow.degree_correct(S, correction)

def build(t, firms):
    """Similarity matrices for the firms (a formation.universe_at frame) at formation month t (Period[M] or date).
    Returns {'dense', 'bow', 'bow_raw'}: n x n float32, rows/cols in the order of `firms`."""
    date = pd.Period(t, 'M').to_timestamp() if not isinstance(t, pd.Timestamp) else t
    acc = firms.accession.to_numpy()
    raw = bow_sim(date, acc, 'raw')
    return {'dense': dense(acc).astype(np.float32), 'bow': bow.degree_correct(raw, CORRECTION), 'bow_raw': raw}

def density(firms):
    """pi: share of firm pairs with the same historical SIC-3 (pairs with a missing SIC excluded)."""
    sic = firms.sic.to_numpy(dtype=float); i, j = np.triu_indices(len(sic), 1)
    ok = (sic[i] > 0) & (sic[j] > 0)
    return float((np.floor(sic[i] / 10) == np.floor(sic[j] / 10))[ok].mean())

def peers(S, pi):
    """Density-calibrated peer matrix: s_ij > tau, tau = (1 - pi) quantile of the off-diagonal s. Boolean n x n, no self."""
    n = len(S); i, j = np.triu_indices(n, 1)
    tau = np.quantile(S[i, j], 1 - pi)
    A = S > tau; np.fill_diagonal(A, False)
    return A
