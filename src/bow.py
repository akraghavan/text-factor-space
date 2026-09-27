"""P6 v1: Hoberg-Phillips bag-of-words with a point-in-time vocabulary (SPEC §3, §5).

Build (python src/bow.py): one pass over the Item 1 shards (texts with >= 100 words) writes per-filing word counts over a
master vocabulary to data/interim/bow/: n_total (all occurrences), n_title (Title-case occurrences), n_lower (lower-case
occurrences; ALL-CAPS occurrences count only in n_total), plus rows.parquet (accession, cik, filing_date, n_words) and
vocab.parquet (word, stop, geo, noun). The master vocabulary is every alphabetic token of >= 3 letters in >= MIN_DF
filings overall; that is only a superset filter (a word below MIN_DF overall is below it in every window), so it
leaks nothing.

Use (formation_vectors): at formation date t the vocabulary is built only from the filings in the pool filed in
[t - 365 days, t): keep words that are not stop words or geographic terms, appear in >= MIN_DF of those filings and in
<= 25% of them (HP drop words in more than 25% of documents). variant='nouns' also requires a WordNet noun or a proper
noun, i.e. Title-case in >= 90% of its non-ALL-CAPS occurrences within the window (HP's rule). Vectors are binary
word presence, unit-normalised, so s_ij = v_i . v_j is the HP cosine.
The build prints a per-year summary and the correlation with the v0 (calendar-year vocabulary) similarities."""
import sys, os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); from paths import RAW, INTERIM
import re, glob, time
from collections import Counter
import numpy as np, pandas as pd, scipy.sparse as sp

OUT = INTERIM / 'bow'
TOKEN = re.compile(r'[A-Za-z]{3,}')
MIN_DF, MAX_DF, CAP_SHARE, WINDOW_DAYS = 5, 0.25, 0.9, 365

def _count_shard(path):
    d = pd.read_parquet(path, columns=['accession', 'item1', 'n_words'])
    d = d[d.n_words >= 100]
    local = {}; r_, c_, tot, tit, low = [], [], [], [], []
    for r, t in enumerate(d.item1):
        agg = {}
        for tok, n in Counter(TOKEN.findall(t)).items():
            w = tok.lower(); a = agg.setdefault(w, [0, 0, 0]); a[0] += n
            if tok[0].isupper():
                if not tok.isupper(): a[1] += n
            else: a[2] += n
        for w, (n0, n1, n2) in agg.items():
            r_.append(r); c_.append(local.setdefault(w, len(local))); tot.append(n0); tit.append(n1); low.append(n2)
    words = np.array(sorted(local, key=local.get))
    return (d.accession.tolist(), d.n_words.to_numpy(), words,
            *(np.asarray(x, dtype=np.int32) for x in (r_, c_, tot, tit, low)))

def build():
    from multiprocessing import Pool
    t0 = time.time(); OUT.mkdir(parents=True, exist_ok=True)
    shards = sorted(glob.glob(str(INTERIM / 'item1' / 'shard_*.parquet')))
    with Pool(max(1, (os.cpu_count() or 2) - 2)) as p: parts = p.map(_count_shard, shards)
    vocab = np.array(sorted(set().union(*(set(x[2]) for x in parts))))
    rows_acc, rows_nw, R, C, T, TI, LO = [], [], [], [], [], [], []
    off = 0
    for acc, nw, words, r, c, tot, tit, low in parts:
        R.append(r + off); C.append(np.searchsorted(vocab, words)[c]); T.append(tot); TI.append(tit); LO.append(low)
        rows_acc += acc; rows_nw.append(nw); off += len(acc)
    R, C = np.concatenate(R), np.concatenate(C)
    mk = lambda v: sp.csr_matrix((np.concatenate(v), (R, C)), shape=(off, len(vocab)), dtype=np.int32)
    n_total, n_title, n_lower = mk(T), mk(TI), mk(LO)
    rows = pd.DataFrame({'accession': rows_acc, 'n_words': np.concatenate(rows_nw)})
    keep_r = ~rows.accession.duplicated().to_numpy()                 # an accession appears once with >= 100 words
    df_all = np.asarray((n_total[keep_r] > 0).sum(0)).ravel(); keep_c = df_all >= MIN_DF
    n_total, n_title, n_lower = (m[keep_r][:, keep_c].tocsr() for m in (n_total, n_title, n_lower))
    idx = pd.read_parquet(INTERIM / 'tenk_index.parquet', columns=['accession', 'cik', 'filing_date'])
    rows = rows[keep_r].reset_index(drop=True).merge(idx, on='accession', how='left')
    rows['filing_date'] = pd.to_datetime(rows.filing_date)
    vocab = pd.DataFrame({'word': vocab[keep_c]})
    from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS
    from geo_terms import GEO
    import nltk; nltk.data.path.insert(0, str(RAW / 'nltk_data')); from nltk.corpus import wordnet as wn
    vocab['stop'] = vocab.word.isin(ENGLISH_STOP_WORDS); vocab['geo'] = vocab.word.isin(GEO)
    vocab['noun'] = [bool(wn.synsets(w, pos='n')) for w in vocab.word]
    for name, m in (('n_total', n_total), ('n_title', n_title), ('n_lower', n_lower)): sp.save_npz(OUT / f'{name}.npz', m)
    rows.to_parquet(OUT / 'rows.parquet'); vocab.to_parquet(OUT / 'vocab.parquet')
    print(f'bow build: {len(rows)} filings x {len(vocab)} words (df >= {MIN_DF} overall), nnz {n_total.nnz:,}, '
          f'{vocab.noun.mean():.1%} WordNet nouns, {int(vocab.geo.sum())} geo, {int(vocab.stop.sum())} stop, '
          f'{time.time() - t0:.0f}s', flush=True)

def load(path=OUT):
    """Everything formation_vectors needs: rows, vocab, n_total, n_title, n_lower."""
    B = {k: sp.load_npz(path / f'{k}.npz') for k in ('n_total', 'n_title', 'n_lower')}
    B['rows'] = pd.read_parquet(path / 'rows.parquet'); B['vocab'] = pd.read_parquet(path / 'vocab.parquet')
    B['present'] = (B['n_total'] > 0).astype(np.float32).tocsr()
    return B

def window_rows(B, t, pool=None, days=WINDOW_DAYS):
    """Row indices of filings in the pool filed in [t - days, t)."""
    fd = B['rows'].filing_date; m = (fd >= pd.Timestamp(t) - pd.Timedelta(days=days)) & (fd < pd.Timestamp(t))
    if pool is not None: m &= pool
    return np.flatnonzero(m.to_numpy())

def formation_vectors(B, t, docs, pool=None, variant='all', min_df=MIN_DF, max_df=MAX_DF, cap_share=CAP_SHARE):
    """Unit-normalised binary vectors for rows `docs` with the vocabulary of formation date t.
    pool: boolean Series over B['rows'] of filings allowed to shape the vocabulary (e.g. the linked universe).
    Returns (X csr float32, len(docs) x K; word indices into B['vocab'])."""
    w = window_rows(B, t, pool)
    if len(w) == 0: raise ValueError(f'no filings in the vocabulary window before {t}')
    v = B['vocab']; df = np.asarray(B['present'][w].sum(0)).ravel()
    keep = (~v.stop.to_numpy()) & (~v.geo.to_numpy()) & (df >= min_df) & (df <= max_df * len(w))
    if variant == 'nouns':
        ti = np.asarray(B['n_title'][w].sum(0)).ravel(); lo = np.asarray(B['n_lower'][w].sum(0)).ravel()
        proper = ti >= cap_share * np.maximum(ti + lo, 1)
        keep &= v.noun.to_numpy() | proper
    elif variant != 'all': raise ValueError(variant)
    cols = np.flatnonzero(keep)
    X = B['present'][docs][:, cols].tocsr()
    nrm = np.sqrt(np.asarray(X.multiply(X).sum(1)).ravel()); nrm[nrm == 0] = 1
    return sp.diags(1 / nrm).dot(X).astype(np.float32).tocsr(), cols

def degree_correct(S, kind='null'):
    """D9 degree correction of a dense n x n BoW similarity matrix (diagonal ignored). m_i = firm i's median similarity to
    the others in the cross-section. Under random word use E0 s_ij = sqrt(n_i n_j)/V = a_i a_j with m_i ~ a_i a_bar, so
    E0 s_ij ~ m_i m_j / median(m) and Var0 s_ij ~ 1/V (length-free).
      'null' (adopted, D11, 27 Sep): s - m_i m_j / median(m)  -- subtracts the null mean; variance-stable
      'mult': s / (m_i m_j)   'add': s - (m_i + m_j)/2   'raw': s
    Chosen on Element A diagnostics only (analysis/output/a_text_layer)."""
    if kind == 'raw': return S
    T = np.array(S, dtype=np.float32, copy=True); np.fill_diagonal(T, np.nan)
    m = np.maximum(np.nanmedian(T, axis=1), 1e-6).astype(np.float32)
    if kind == 'null': return S - np.outer(m, m) / np.median(m)
    if kind == 'mult': return S / np.outer(m, m)
    if kind == 'add': return S - (m[:, None] + m[None, :]) / 2
    raise ValueError(kind)

def summary():
    """Annual formation dates (1 July): window size, vocabulary sizes, words per filing; v1 vs v0 similarity."""
    B = load(); rows = B['rows']
    lk = pd.read_parquet(INTERIM / 'tenk_linked.parquet', columns=['accession'])
    pool = rows.accession.isin(lk.accession)
    rng = np.random.default_rng(0); out = []
    for y in range(2012, 2027):
        t = pd.Timestamp(f'{y}-07-01'); docs = window_rows(B, t, pool)
        rec = {'formation': t.date(), 'n_window': len(docs)}
        for var in ('all', 'nouns'):
            X, cols = formation_vectors(B, t, docs, pool, var)
            rec[f'K_{var}'] = len(cols); rec[f'words_per_doc_{var}'] = round(X.nnz / X.shape[0])
            if var == 'all':
                i, j = rng.integers(0, len(docs), (2, 200_000)); ok = i != j
                s1 = np.asarray(X[i[ok]].multiply(X[j[ok]]).sum(1)).ravel(); rec['mean_s_all'] = round(float(s1.mean()), 4)
            else:
                s2 = np.asarray(X[i[ok]].multiply(X[j[ok]]).sum(1)).ravel()
                rec['corr_all_nouns'] = round(float(np.corrcoef(s1, s2)[0, 1]), 3)
        v0 = INTERIM / 'tfidf'                                  # v0: calendar-year vocabulary of year y-1
        if (v0 / f'X_{y-1}.npz').exists():
            X0 = sp.load_npz(v0 / f'X_{y-1}.npz'); r0 = pd.read_parquet(v0 / f'rows_{y-1}.parquet')
            X1, _ = formation_vectors(B, t, docs, pool, 'all')
            a = rows.accession.to_numpy()[docs]; pos0 = pd.Series(np.arange(len(r0)), r0.accession)
            common = np.flatnonzero(pd.Series(a).isin(r0.accession).to_numpy())
            i, j = rng.choice(common, (2, 200_000)); ok = i != j; i, j = i[ok], j[ok]
            s1 = np.asarray(X1[i].multiply(X1[j]).sum(1)).ravel()
            i0, j0 = pos0.loc[a[i]].to_numpy(), pos0.loc[a[j]].to_numpy()
            s0 = np.asarray(X0[i0].multiply(X0[j0]).sum(1)).ravel()
            rec['corr_v0_v1'] = round(float(np.corrcoef(s0, s1)[0, 1]), 3)
        out.append(rec)
    s = pd.DataFrame(out); print(s.to_string(index=False)); return s

if __name__ == '__main__':
    if '--summary-only' not in sys.argv: build()
    summary()
