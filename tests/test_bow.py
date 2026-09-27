"""P6 v1 (src/bow.py): the vocabulary at formation date t depends only on filings filed before t."""
import os, sys
import numpy as np, pandas as pd, scipy.sparse as sp
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))
import bow

WORDS = ['pump', 'valve', 'bank', 'loan', 'acme', 'the', 'texas', 'future']
def make_B(counts, title=None, dates=None):
    n_total = sp.csr_matrix(np.asarray(counts, dtype=np.int32))
    n_title = sp.csr_matrix(np.asarray(title if title is not None else np.zeros_like(counts), dtype=np.int32))
    n_lower = sp.csr_matrix(np.asarray(counts, dtype=np.int32) - n_title.toarray())
    vocab = pd.DataFrame({'word': WORDS, 'stop': [w == 'the' for w in WORDS], 'geo': [w == 'texas' for w in WORDS],
                          'noun': [w in ('pump', 'valve', 'bank', 'loan', 'future') for w in WORDS]})
    rows = pd.DataFrame({'filing_date': pd.to_datetime(dates)})
    return {'n_total': n_total, 'n_title': n_title, 'n_lower': n_lower, 'rows': rows, 'vocab': vocab,
            'present': (n_total > 0).astype(np.float32).tocsr()}

# 8 past filings: 4 pump/valve firms, 4 bank/loan firms; everyone says 'the' and 'texas'; 'acme' is a Title-case name.
PAST = [[1, 1, 0, 0, 1, 3, 1, 0]] * 4 + [[0, 0, 1, 1, 1, 3, 1, 0]] * 4
PAST_TITLE = [[0, 0, 0, 0, 1, 0, 0, 0]] * 8
DATES = ['2019-01-15'] * 8 + ['2019-08-01'] * 2
FUTURE = [[0, 0, 0, 0, 0, 1, 0, 5]] * 2          # filed after t: 'future' must not enter the vocabulary
T = '2019-07-01'

def test_future_filings_do_not_change_vectors():
    B1 = make_B(PAST + FUTURE, PAST_TITLE + [[0] * 8] * 2, DATES)
    B2 = make_B(PAST + [[9] * 8] * 2, PAST_TITLE + [[0] * 8] * 2, DATES)   # different future text
    docs = np.arange(8)
    X1, c1 = bow.formation_vectors(B1, T, docs, min_df=1, max_df=0.6)
    X2, c2 = bow.formation_vectors(B2, T, docs, min_df=1, max_df=0.6)
    assert np.array_equal(c1, c2) and np.allclose(X1.toarray(), X2.toarray())
    assert 'future' not in set(B1['vocab'].word[c1])

def test_stop_geo_and_max_df_dropped_and_unit_norm():
    B = make_B(PAST + FUTURE, PAST_TITLE + [[0] * 8] * 2, DATES)
    X, cols = bow.formation_vectors(B, T, np.arange(8), min_df=1, max_df=0.6)
    kept = set(B['vocab'].word[cols])
    assert kept == {'pump', 'valve', 'bank', 'loan'}          # 'acme' is in 100% of filings > 60%; stop/geo dropped
    assert np.allclose(np.sqrt(X.multiply(X).sum(1)).A1, 1)
    S = (X @ X.T).toarray()
    assert np.isclose(S[0, 1], 1) and np.isclose(S[0, 4], 0)

def test_nouns_variant_keeps_proper_nouns_only_by_capitalisation():
    B = make_B(PAST + FUTURE, PAST_TITLE + [[0] * 8] * 2, DATES)
    B['vocab'].loc[B['vocab'].word == 'valve', 'noun'] = False    # not a noun and never capitalised -> dropped
    _, cols = bow.formation_vectors(B, T, np.arange(8), variant='nouns', min_df=1, max_df=1.0)
    kept = set(B['vocab'].word[cols])
    assert 'valve' not in kept and 'acme' in kept and 'pump' in kept

def test_null_correction_removes_the_length_term():
    """D11: under random word use s_ij ~ a_i a_j (a_i ~ sqrt(n_i/V)); subtracting m_i m_j / median(m) removes the length
    term from each firm's mean similarity, while the raw mean tracks length and the additive form leaves most of it."""
    rng = np.random.default_rng(0); n = 400
    a = np.sqrt(rng.uniform(200, 5000, n) / 20000)                     # document lengths 200-5,000 words, V = 20,000
    S = np.outer(a, a) + rng.normal(0, 0.003, (n, n)); S = (S + S.T) / 2; np.fill_diagonal(S, 1)
    rowmean = lambda M: (M.sum(1) - np.diag(M)) / (n - 1)
    # length term left in firm mean similarity = slope of the row mean on a, relative to the raw slope
    slope = {k: np.polyfit(a, rowmean(bow.degree_correct(S, k)), 1)[0] for k in ('raw', 'add', 'null')}
    assert abs(slope['null'] / slope['raw']) < 0.05      # null removes >= 95% of the length term
    assert slope['add'] / slope['raw'] > 0.4             # additive leaves about half of it
    assert bow.degree_correct(S, 'raw') is S
