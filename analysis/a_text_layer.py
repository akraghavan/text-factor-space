"""Element A validation (SPEC §5): are the dense and bag-of-words text networks sensible, and how do they relate to
historical SIC-3 and to Hoberg-Phillips TNIC-3?

Formation dates: 1 July of each year 2012-2026. Firms: CRSP universe at the end of June without SPAC months (D8; one
PERMNO per PERMCO, the largest), each with its latest linked 10-K filed before t and at most 15 months earlier, with >= 100 words of Item 1.
Networks (s_ij for i < j):
  dense      bge-small embeddings, centred on the cross-sectional mean and renormalised (SPEC §5.3)
  bow_all    binary word vectors, vocabulary from linked filings in [t - 365 d, t)  (src/bow.py, P6 v1)
  bow_nouns  the same restricted to nouns and proper nouns (HP)
  *_mult, *_add, *_null  D9 degree corrections of the BoW networks: s/(m_i m_j), s - (m_i + m_j)/2, s - m_i m_j/median(m);
                 m_i = median s_ij over j != i
Density calibration: pi = share of pairs sharing a historical SIC-3 (CRSP siccd, June), tau = (1 - pi) quantile of s.
TNIC-3 year Y is used from July Y+1 (unlagged file), so formation t uses Y = t.year - 1 (available to t = 2024).
Outputs (aggregates only) go to analysis/output/a_text_layer/: markdown tables, PNG figures; CSV copies stay local
(gitignored). AUCs, quantiles, Jaccards and rank correlations are descriptive numpy/scipy, not tfs_stats estimators.
Run: python analysis/a_text_layer.py   (SEC_USER_AGENT set: firm names for the neighbour table come from SEC EDGAR)"""
import sys, os, json, glob, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]; sys.path.insert(0, str(ROOT / 'src'))
from paths import RAW, INTERIM, PROCESSED, SEC_UA
import numpy as np, pandas as pd, requests
from scipy.stats import rankdata
import bow
from universe import exclude_spacs

OUT = ROOT / 'analysis' / 'output' / 'a_text_layer'; OUT.mkdir(parents=True, exist_ok=True)
YEARS = range(2012, 2027)
FIG_NETS = ['dense', 'bow_all', 'bow_nouns']
# D9: degree-corrected BoW, m_i = firm i's median similarity to the other firms in the cross-section.
# Under random word use E s_ij = sqrt(n_i n_j)/V = a_i a_j, m_i ~ a_i a_bar, so E0 s_ij = m_i m_j / median(m), Var0 s_ij ~ 1/V.
# mult: s_ij / (m_i m_j) (removes the null mean's length term as a ratio); add: s_ij - (m_i + m_j)/2 (assumes a_i + a_j);
# null: s_ij - m_i m_j / median(m) (subtracts the null mean; variance-stable, the analogue of modularity's A - k k'/2m).
NETS = FIG_NETS + ['bow_all_mult', 'bow_all_add', 'bow_all_null', 'bow_nouns_mult', 'bow_nouns_add', 'bow_nouns_null']
LABEL = {'dense': 'Dense (bge-small, centred)', 'bow_all': 'BoW, all words', 'bow_nouns': 'BoW, nouns + proper nouns',
         'bow_all_mult': 'BoW / (m_i m_j)', 'bow_all_add': 'BoW − (m_i + m_j)/2', 'bow_nouns_mult': 'BoW nouns / (m_i m_j)', 'bow_nouns_add': 'BoW nouns − (m_i + m_j)/2',
         'bow_all_null': 'BoW − m_i m_j / med(m)', 'bow_nouns_null': 'BoW nouns − m_i m_j / med(m)'}
FOCAL = ['AAPL', 'MSFT', 'NVDA', 'INTC', 'JPM', 'GS', 'XOM', 'JNJ', 'PFE', 'KO', 'WMT', 'HD', 'BA', 'DAL', 'TSLA', 'NFLX']
NEIGHBOUR_T = pd.Timestamp('2024-07-01')          # latest formation with TNIC-3 (Y = 2023)

# ---------------------------------------------------------------- data
def load():
    lk = pd.read_parquet(INTERIM / 'tenk_linked.parquet', columns=['accession', 'permno', 'gvkey', 'cik', 'filing_date'])
    m = pd.read_parquet(PROCESSED / 'crsp_monthly.parquet', columns=['permno', 'permco', 'ym', 'me', 'sic', 'in_universe'])
    B = bow.load()
    e = pd.concat(pd.read_parquet(f) for f in sorted(glob.glob(str(INTERIM / 'emb' / 'shard_*.parquet'))))
    e = e.drop_duplicates('accession')
    E = np.stack(e.emb.to_numpy()).astype(np.float32); epos = pd.Series(np.arange(len(e)), index=e.accession.to_numpy())
    brow = pd.Series(np.arange(len(B['rows'])), index=B['rows'].accession.to_numpy())
    lk = lk[lk.accession.isin(epos.index) & lk.accession.isin(brow.index)].copy()
    pool = B['rows'].accession.isin(set(lk.accession))                       # linked filings shape the vocabulary
    return dict(lk=lk, m=m, B=B, E=E, epos=epos, brow=brow, pool=pool)

def firms_at(D, t):
    ym = (t - pd.Timedelta(days=1)).to_period('M')
    u = exclude_spacs(D['m'][(D['m'].ym == ym) & D['m'].me.notna() & D['m'].in_universe])     # D8; exit-month rows are not members
    u = u.sort_values('me', ascending=False).drop_duplicates('permco')
    f = D['lk'][(D['lk'].filing_date < t) & (D['lk'].filing_date >= t - pd.DateOffset(months=15))]
    f = f.sort_values('filing_date').drop_duplicates('permno', keep='last')
    x = u.merge(f, on='permno').reset_index(drop=True)
    x['nw'] = D['B']['rows'].n_words.to_numpy()[D['brow'].loc[x.accession.to_numpy()].to_numpy()]
    return x

def dense_vectors(D, acc, centre=None):
    V = D['E'][D['epos'].loc[np.asarray(acc)].to_numpy()]
    mu = V.mean(0) if centre is None else centre
    V = V - mu; V /= np.linalg.norm(V, axis=1, keepdims=True) + 1e-12
    return V, mu

def sims(D, t, x):
    """n x n similarity matrices for every network in NETS (float32)."""
    S = {}
    V, _ = dense_vectors(D, x.accession); S['dense'] = V @ V.T
    rows = D['brow'].loc[x.accession.to_numpy()].to_numpy()
    for var, name in (('all', 'bow_all'), ('nouns', 'bow_nouns')):
        X, _ = bow.formation_vectors(D['B'], t, rows, D['pool'], var)
        S[name] = (X @ X.T).toarray().astype(np.float32)
        for kind in ('mult', 'add', 'null'): S[f'{name}_{kind}'] = bow.degree_correct(S[name], kind)   # D9
    return S

def auc(score, label):
    r = rankdata(score); npos = int(label.sum()); nneg = len(label) - npos
    return (r[label].sum() - npos * (npos + 1) / 2) / (npos * nneg)

def load_tnic():
    cache = INTERIM / 'tnic3.parquet'
    if not cache.exists():
        import zipfile
        with zipfile.ZipFile(RAW / 'tnic3_data.zip') as z, z.open('tnic3_data.txt') as fh:
            it = pd.read_csv(fh, sep='\t', dtype={'year': 'int16', 'gvkey1': 'int32', 'gvkey2': 'int32', 'score': 'float32'},
                             chunksize=5_000_000)
            t = pd.concat(c[(c.year >= 2010) & (c.gvkey1 < c.gvkey2)] for c in it)   # each pair once, no self-pairs
        t.to_parquet(cache)
    return pd.read_parquet(cache)

# ---------------------------------------------------------------- per-year statistics
def year_stats(D, t, x, S, tnic):
    n = len(x); iu = np.triu_indices(n, 1)
    sic = x.sic.to_numpy(dtype=float); sic3 = np.floor(sic / 10)
    valid = (sic[iu[0]] > 0) & (sic[iu[1]] > 0)
    same = (sic3[iu[0]] == sic3[iu[1]]) & valid
    pi = same[valid].mean()
    nspac = sic != 6799                                   # blank-check companies (SPAC boom 2020-23): sensitivity only
    valid_x = valid & nspac[iu[0]] & nspac[iu[1]]
    rows, shape, tn_rows = [], [], []
    logn = np.log(x.nw.to_numpy())
    # TNIC pairs among these firms
    tn_pairs = None
    if tnic is not None and t.year - 1 <= int(tnic.year.max()):
        g = tnic[tnic.year == t.year - 1]
        pos = pd.Series(np.arange(n), index=x.gvkey.to_numpy()); pos = pos[~pos.index.duplicated()]
        covered = np.zeros(n, bool); covered[pos.reindex(np.union1d(g.gvkey1, g.gvkey2)).dropna().astype(int)] = True
        g = g[g.gvkey1.isin(pos.index) & g.gvkey2.isin(pos.index)]
        a, b = pos[g.gvkey1].to_numpy(), pos[g.gvkey2].to_numpy(); lo, hi = np.minimum(a, b), np.maximum(a, b)
        flat = lo.astype(np.int64) * n + hi
        pair_flat = iu[0].astype(np.int64) * n + iu[1]
        in_tn = np.isin(pair_flat, flat)
        tn_score = np.full(len(pair_flat), np.nan, np.float32)
        order = np.argsort(pair_flat); loc = np.searchsorted(pair_flat[order], flat); tn_score[order[loc]] = g.score.to_numpy()
        both_cov = covered[iu[0]] & covered[iu[1]]
        tn_pairs = (in_tn, tn_score, both_cov)
        tn_rows.append({'formation': t.date(), 'network': 'SIC-3', 'firms_covered': int(covered.sum()),
                        'tnic_density': in_tn[both_cov].mean(), 'net_density': same[both_cov].mean(),
                        'jaccard': (in_tn & same & both_cov).sum() / ((in_tn | same) & both_cov).sum(),
                        'recall_tnic': (in_tn & same)[both_cov].sum() / in_tn[both_cov].sum(),
                        'auc_tnic': np.nan, 'spearman_score': np.nan})
    for net in NETS:
        s = S[net][iu]
        tau = float(np.quantile(s, 1 - pi)); edge = s > tau
        q = np.quantile(s, [.01, .05, .25, .5, .75, .95, .99])
        rowmean = (S[net].sum(1) - np.diag(S[net])) / (n - 1)
        rec = {'formation': t.date(), 'network': net, 'n_firms': n, 'n_pairs': len(s), 'pi_sic3': pi, 'tau': tau,
               **{f'q{int(p * 100):02d}': v for p, v in zip([.01, .05, .25, .5, .75, .95, .99], q)},
               'auc_sic3': auc(s[valid], same[valid]), 'auc_sic3_ex6799': auc(s[valid_x], same[valid_x]),
               'n_sic6799': int((~nspac).sum()),
               'mean_within': s[same].mean(), 'mean_cross': s[valid & ~same].mean(),
               'precision_sic3': same[edge & valid].mean(), 'recall_sic3': (edge & same).sum() / same.sum(),
               'jaccard_sic3': (edge & same).sum() / ((edge | same) & valid).sum(),
               'corr_len_rowmean': np.corrcoef(logn, rowmean)[0, 1],
               'near_dup_pairs': int((s > 0.98).sum())}
        rows.append(rec)
        # shape: share of same-SIC-3 pairs by similarity percentile (100 bins) and within the top 2% (20 bins)
        r = rankdata(s[valid]) / valid.sum(); sv = same[valid]
        b100 = np.minimum((r * 100).astype(int), 99); b_top = np.minimum(((r - 0.98) / 0.001).astype(int), 19)
        sh = np.bincount(b100, sv, 100) / np.bincount(b100, None, 100)
        top = r > 0.98; sht = np.bincount(b_top[top], sv[top], 20) / np.bincount(b_top[top], None, 20)
        shape += [{'formation': t.date(), 'network': net, 'pct': (k + .5), 'share_same_sic3': sh[k]} for k in range(100)]
        shape += [{'formation': t.date(), 'network': net, 'pct': 98 + (k + .5) * 0.1, 'share_same_sic3': sht[k], 'top2': True}
                  for k in range(20)]
        if tn_pairs is not None:
            in_tn, tn_score, both_cov = tn_pairs
            e2 = edge & both_cov; k = in_tn & both_cov
            has = ~np.isnan(tn_score)
            tn_rows.append({'formation': t.date(), 'network': net, 'firms_covered': int(covered.sum()),
                            'tnic_density': in_tn[both_cov].mean(), 'net_density': edge[both_cov].mean(),
                            'jaccard': (e2 & k).sum() / (e2 | k).sum(), 'recall_tnic': (e2 & k).sum() / k.sum(),
                            'auc_tnic': auc(s[both_cov], in_tn[both_cov]),
                            'spearman_score': np.corrcoef(rankdata(s[has]), rankdata(tn_score[has]))[0, 1]})
    return rows, shape, tn_rows

def yoy(D, t, x, x_prev):
    """Similarity of each firm's filing at t with its filing at the previous formation (different accession)."""
    p = x.merge(x_prev[['permno', 'accession']], on='permno', suffixes=('', '_prev'))
    p = p[p.accession != p.accession_prev]
    if len(p) == 0: return {}
    V, mu = dense_vectors(D, x.accession)
    a, _ = dense_vectors(D, p.accession, mu); b, _ = dense_vectors(D, p.accession_prev, mu)
    out = {'dense': np.sum(a * b, 1)}
    for var, name in (('all', 'bow_all'), ('nouns', 'bow_nouns')):
        rows = np.concatenate([D['brow'].loc[p.accession.to_numpy()].to_numpy(), D['brow'].loc[p.accession_prev.to_numpy()].to_numpy()])
        X, _ = bow.formation_vectors(D['B'], t, rows, D['pool'], var); k = len(p)
        out[name] = np.asarray(X[:k].multiply(X[k:]).sum(1)).ravel()
    return {net: (len(p), float(np.median(v)), float(np.quantile(v, .1))) for net, v in out.items()}

# ---------------------------------------------------------------- names (public, SEC EDGAR)
def sec_names(ciks):
    cache = RAW / 'sec_names.json'
    names = json.loads(cache.read_text()) if cache.exists() else {}
    tick = RAW / 'sec_company_tickers.json'
    hdr = {'User-Agent': SEC_UA}
    if not tick.exists():
        tick.write_text(requests.get('https://www.sec.gov/files/company_tickers.json', headers=hdr, timeout=60).text)
    for v in json.loads(tick.read_text()).values(): names.setdefault(str(v['cik_str']), v['title'])
    for c in ciks:
        if str(c) in names: continue
        time.sleep(0.15)
        r = requests.get(f'https://data.sec.gov/submissions/CIK{int(c):010d}.json', headers=hdr, timeout=60)
        names[str(c)] = r.json().get('name', str(c)) if r.status_code == 200 else str(c)
    cache.write_text(json.dumps(names)); return names

def ticker_ciks():
    tick = RAW / 'sec_company_tickers.json'
    if not tick.exists(): sec_names([])
    return {v['ticker']: int(v['cik_str']) for v in json.loads(tick.read_text()).values()}

def short(s, k=28):
    import re
    s = re.sub(r'\s*/[A-Za-z]{2,3}/?\s*$', '', str(s))                       # EDGAR state suffixes: /DE/, /MD/
    s = re.sub(r'(?i)(?<!&)[\s,]+(inc|corp|corporation|co|company|ltd|plc|n\.?v|s\.?a)\.?$', '', s.strip()).strip(' .,')
    s = re.sub(r'(?i)(?<!&)[\s,]+(inc|corp|corporation|co|ltd)\.?$', '', s).strip(' .,').title()
    return s if len(s) <= k else s[:k - 1] + '…'

def neighbours(D, tnic):
    t = NEIGHBOUR_T; x = firms_at(D, t); S = sims(D, t, x)
    tc = ticker_ciks(); cik_pos = pd.Series(np.arange(len(x)), index=x.cik.to_numpy())
    cik_pos = cik_pos[~cik_pos.index.duplicated()]
    g = tnic[tnic.year == t.year - 1]; gpos = pd.Series(np.arange(len(x)), index=x.gvkey.to_numpy())
    gpos = gpos[~gpos.index.duplicated()]
    table, need = [], set()
    for tk in FOCAL:
        c = tc.get(tk)
        if c is None or c not in cik_pos.index: continue
        i = int(cik_pos[c]); row = {'ticker': tk, 'cik': c}
        for net in ('dense', 'bow_nouns', 'bow_nouns_mult', 'bow_nouns_add', 'bow_nouns_null'):
            s = S[net][i].copy(); s[i] = -np.inf
            row[net] = list(x.cik.to_numpy()[np.argsort(-s)[:10]])
        gv = x.gvkey.iloc[i]
        h = pd.concat([g[g.gvkey1 == gv].rename(columns={'gvkey2': 'peer'}), g[g.gvkey2 == gv].rename(columns={'gvkey1': 'peer'})])
        h = h[h.peer.isin(gpos.index)].sort_values('score', ascending=False).head(10)
        row['tnic'] = list(x.cik.to_numpy()[gpos[h.peer].to_numpy()])
        need |= {c, *row['dense'], *row['bow_nouns'], *row['bow_nouns_mult'], *row['bow_nouns_add'], *row['bow_nouns_null'], *row['tnic']}; table.append(row)
    nm = sec_names(sorted(need))
    lines = [f'# Top-10 text neighbours, formation {t.date()}', '',
             'Firms in the CRSP universe with a linked 10-K; names from SEC EDGAR. Dense = centred bge-small cosine; '
             'BoW nouns = binary noun/proper-noun vectors (vocabulary from the prior 12 months); TNIC-3 = Hoberg–Phillips '
             f'FY{t.year - 1} peers restricted to the same firm set, ranked by score. Firms sharing the focal firm\'s '
             'historical SIC-3 are marked *.', '']
    sic3 = pd.Series((x.sic.to_numpy(dtype=float) // 10), index=x.cik.to_numpy()); sic3 = sic3[~sic3.index.duplicated()]
    overlap = []
    pub = [f'# Top-10 text neighbours, formation {t.date()}', '',
           'Text-only networks built from public SEC 10-K text; names from SEC EDGAR. Dense = centred bge-small cosine; '
           'BoW nouns = binary noun/proper-noun vectors (vocabulary from the prior 12 months). The version with TNIC-3 peers '
           'and SIC-3 marks (firm-level TNIC/CRSP data, SPEC §2) stays local: neighbours_full.md.', '']
    for r in table:
        f3 = sic3[r['cik']]
        fmt = lambda cs, mark=True: '; '.join(short(nm.get(str(c), c)) + ('*' if mark and sic3.get(c) == f3 else '') for c in cs) or '—'
        head = [f"**{r['ticker']}** — {short(nm.get(str(r['cik']), r['cik']), 40)}", '', '| Network | Neighbours (most similar first) |', '|---|---|']
        lines += head + [f"| Dense | {fmt(r['dense'])} |", f"| BoW nouns | {fmt(r['bow_nouns'])} |", f"| BoW nouns / (m_i m_j) | {fmt(r['bow_nouns_mult'])} |",
                          f"| BoW nouns − (m_i+m_j)/2 | {fmt(r['bow_nouns_add'])} |", f"| BoW nouns − m_i m_j/med(m) | {fmt(r['bow_nouns_null'])} |",
                          f"| TNIC-3 | {fmt(r['tnic'])} |", '']
        pub += head + [f"| Dense | {fmt(r['dense'], False)} |", f"| BoW nouns | {fmt(r['bow_nouns'], False)} |",
                       f"| BoW nouns / (m_i m_j) | {fmt(r['bow_nouns_mult'], False)} |", f"| BoW nouns − (m_i+m_j)/2 | {fmt(r['bow_nouns_add'], False)} |",
                       f"| BoW nouns − m_i m_j/med(m) | {fmt(r['bow_nouns_null'], False)} |", '']
        overlap.append({'ticker': r['ticker'], 'dense∩bow': len(set(r['dense']) & set(r['bow_nouns'])),
                        'dense∩tnic': len(set(r['dense']) & set(r['tnic'])), 'bow∩tnic': len(set(r['bow_nouns']) & set(r['tnic'])),
                        'mult∩tnic': len(set(r['bow_nouns_mult']) & set(r['tnic'])), 'add∩tnic': len(set(r['bow_nouns_add']) & set(r['tnic'])),
                        'null∩tnic': len(set(r['bow_nouns_null']) & set(r['tnic'])), 'bow∩null': len(set(r['bow_nouns']) & set(r['bow_nouns_null'])),
                        'bow∩mult': len(set(r['bow_nouns']) & set(r['bow_nouns_mult']))})
    o = pd.DataFrame(overlap)
    lines += ['**Overlap of top-10 lists (out of 10)**', '', to_md(o), '',
              f"Mean: dense∩BoW {o['dense∩bow'].mean():.1f}, dense∩TNIC {o['dense∩tnic'].mean():.1f}, BoW∩TNIC {o['bow∩tnic'].mean():.1f}."]
    (OUT / 'neighbours_full.md').write_text('\n'.join(lines) + '\n')     # gitignored: firm-level TNIC and CRSP SIC
    pub += ['**Overlap of top-10 lists (out of 10; TNIC counts are aggregates)**', '', to_md(o)]
    (OUT / 'neighbours.md').write_text('\n'.join(pub) + '\n')
    return o

# ---------------------------------------------------------------- figures
INK, INK2, GRID, SURF = '#0b0b0b', '#52514e', '#e4e3df', '#fcfcfb'
COL = {'dense': '#2a78d6', 'bow_all': '#eb6834', 'bow_nouns': '#1baf7a'}
def style(ax, title, ylabel, xlabel=None):
    ax.set_facecolor(SURF); ax.set_title(title, loc='left', color=INK, fontsize=11, pad=10)
    ax.set_ylabel(ylabel, color=INK2, fontsize=9)
    if xlabel: ax.set_xlabel(xlabel, color=INK2, fontsize=9)
    ax.grid(axis='y', color=GRID, lw=0.8); ax.set_axisbelow(True)
    for sp in ('top', 'right'): ax.spines[sp].set_visible(False)
    for sp in ('left', 'bottom'): ax.spines[sp].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)

def endlabel(ax, xs, ys, text, color, dy=0):
    ax.plot(xs, ys, color=color, lw=2, marker='o', ms=4, solid_capstyle='round', label=text)
    ax.annotate(text, (xs[-1], ys[-1]), xytext=(6, dy), textcoords='offset points', va='center', fontsize=8, color=INK)

def figures(st, sh, tn):
    import matplotlib; matplotlib.use('Agg'); import matplotlib.pyplot as plt
    plt.rcParams.update({'font.family': 'sans-serif', 'figure.facecolor': SURF, 'savefig.facecolor': SURF})
    yrs = sorted({d.year for d in st.formation})
    # 1. AUC for same SIC-3 over time
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for k, net in enumerate(FIG_NETS):
        d = st[st.network == net]; endlabel(ax, [f.year for f in d.formation], d.auc_sic3.to_numpy(), LABEL[net], COL[net], dy=(k - 1) * 9)
    style(ax, 'How well each text network ranks same-SIC-3 pairs (AUC)', 'AUC, same historical SIC-3', 'Formation (1 July)')
    ax.set_xlim(min(yrs) - .5, max(yrs) + 4.5); ax.set_xticks(yrs[::2]); ax.legend(frameon=False, fontsize=8, loc='lower left')
    fig.tight_layout(); fig.savefig(OUT / 'fig_auc_sic3.png', dpi=160); plt.close(fig)
    # 2. shape: share same-SIC-3 by similarity percentile, pooled over years; full range and top 2%
    fig, axs = plt.subplots(1, 2, figsize=(10, 4.2))
    pi = st.groupby('formation').pi_sic3.first().mean()
    for top, ax in ((False, axs[0]), (True, axs[1])):
        for net in FIG_NETS:
            d = sh[(sh.network == net) & (sh.top2.fillna(False) == top)].groupby('pct').share_same_sic3.mean()
            ax.plot(d.index, d.to_numpy(), color=COL[net], lw=2, label=LABEL[net])
        ax.axhline(pi, color=INK2, lw=1, ls=(0, (4, 3))); ax.annotate(f'unconditional {pi:.1%}', (ax.get_xlim()[0], pi), xytext=(4, 5),
                                                                     textcoords='offset points', fontsize=8, color=INK2)
        style(ax, 'Top 2% of pairs (0.1-point bins)' if top else 'All pairs (1-point bins)', 'Share of pairs in the same SIC-3',
              'Similarity percentile within formation')
    axs[0].legend(frameon=False, fontsize=8, loc='upper left')
    fig.suptitle('Where the industry signal lives: same-SIC-3 share by similarity percentile (mean over formations)',
                 x=0.01, ha='left', fontsize=11, color=INK)
    fig.tight_layout(); fig.savefig(OUT / 'fig_shape.png', dpi=160); plt.close(fig)
    # 3. TNIC agreement at matched density
    if len(tn):
        fig, ax = plt.subplots(figsize=(8, 4.2)); tyrs = sorted({d.year for d in tn.formation})
        for k, net in enumerate(FIG_NETS):
            d = tn[tn.network == net]; endlabel(ax, [f.year for f in d.formation], d.jaccard.to_numpy(), LABEL[net], COL[net], dy=(k - 1) * 9)
        d = tn[tn.network == 'SIC-3']
        ax.plot([f.year for f in d.formation], d.jaccard.to_numpy(), color=INK2, lw=1.5, ls=(0, (4, 3)), label='SIC-3 (reference)')
        ax.annotate('SIC-3 (reference)', (d.formation.iloc[-1].year, d.jaccard.iloc[-1]), xytext=(6, 0), textcoords='offset points',
                    va='center', fontsize=8, color=INK2)
        style(ax, 'Agreement with Hoberg–Phillips TNIC-3 at matched density (edge-set Jaccard)', 'Jaccard of peer pairs', 'Formation (1 July)')
        ax.set_xlim(min(tyrs) - .5, max(tyrs) + 4.5); ax.set_xticks(tyrs[::2]); ax.set_ylim(0, None); ax.legend(frameon=False, fontsize=8, loc='lower left')
        fig.tight_layout(); fig.savefig(OUT / 'fig_tnic_jaccard.png', dpi=160); plt.close(fig)

# ---------------------------------------------------------------- main
def to_md(d):
    cols = [str(c) for c in d.columns]
    return '\n'.join(['| ' + ' | '.join(cols) + ' |', '|' + '---|' * len(cols)] +
                     ['| ' + ' | '.join(str(v) for v in r) + ' |' for r in d.itertuples(index=False)])

def md(df, cols, fmt):
    d = df[cols].copy()
    for c, f in fmt.items(): d[c] = d[c].map(lambda v: f.format(v) if pd.notna(v) else '—')
    return to_md(d)

def main():
    t0 = time.time(); D = load(); tnic = load_tnic()
    st, sh, tn, yy = [], [], [], []; x_prev = None
    for y in YEARS:
        t = pd.Timestamp(f'{y}-07-01'); x = firms_at(D, t); S = sims(D, t, x)
        a, b, c = year_stats(D, t, x, S, tnic); st += a; sh += b; tn += c
        if x_prev is not None:
            for net, (k, med, p10) in yoy(D, t, x, x_prev).items(): yy.append({'formation': t.date(), 'network': net, 'n': k, 'median': med, 'p10': p10})
        x_prev = x; print(y, len(x), 'firms', f'{time.time() - t0:.0f}s', flush=True)
    st, sh, tn, yy = map(pd.DataFrame, (st, sh, tn, yy))
    for name, d in (('summary', st), ('shape', sh), ('tnic', tn), ('yoy', yy)): d.to_csv(OUT / f'{name}.csv', index=False)
    o = neighbours(D, tnic); figures(st, sh, tn)
    f = {'pi_sic3': '{:.2%}', 'tau': '{:.3f}', 'q50': '{:.3f}', 'q99': '{:.3f}', 'auc_sic3': '{:.3f}', 'auc_sic3_ex6799': '{:.3f}', 'mean_within': '{:.3f}',
         'mean_cross': '{:.3f}', 'precision_sic3': '{:.3f}', 'recall_sic3': '{:.3f}', 'jaccard_sic3': '{:.3f}', 'corr_len_rowmean': '{:+.2f}'}
    agg = st.groupby('network')[list(f)].mean().reindex(NETS).reset_index()
    tagg = tn.groupby('network')[['jaccard', 'recall_tnic', 'auc_tnic', 'spearman_score']].mean().reindex(['SIC-3'] + NETS).reset_index()
    yagg = yy.groupby('network')[['median', 'p10']].mean().reindex(FIG_NETS).reset_index()
    rep = ['# Element A — text-network validation', '',
           f'Generated by `analysis/a_text_layer.py` ({pd.Timestamp.now():%Y-%m-%d}). Formations: 1 July {min(YEARS)}–{max(YEARS)}; '
           f'{int(st[st.network == "dense"].n_firms.min())}–{int(st[st.network == "dense"].n_firms.max())} firms per formation. '
           'Every text network is cut at the (1 − π) quantile, π = same-SIC-3 pair share, so all have SIC-3 density. SPAC '
           'firm-months are excluded (D8). `*_mult` / `*_add` / `*_null` are the D9 degree-corrected BoW networks: s/(m_i m_j), '
           's − (m_i + m_j)/2 and s − m_i m_j / median(m), m_i = firm i\'s median similarity to the others.', '',
           '## Averages over formations', '', md(agg, ['network'] + list(f), f), '',
           'precision/recall/Jaccard: text edges (s > τ) vs same-SIC-3 pairs. corr_len_rowmean: correlation across firms of '
           'log Item 1 length with the firm\'s mean similarity to all others (hub/length effect).', '',
           f'## Agreement with TNIC-3 at matched density (formations {tn.formation.min()}–{tn.formation.max()}, means)', '',
           md(tagg, ['network', 'jaccard', 'recall_tnic', 'auc_tnic', 'spearman_score'],
              {'jaccard': '{:.3f}', 'recall_tnic': '{:.3f}', 'auc_tnic': '{:.3f}', 'spearman_score': '{:.3f}'}), '',
           'jaccard: edge sets among firms covered by TNIC that year; recall_tnic: share of TNIC pairs that are edges; auc_tnic: '
           'AUC of s for TNIC membership; spearman_score: rank correlation of s with the TNIC score over TNIC pairs.', '',
           '## Same-firm similarity with the previous formation\'s filing (means over formations)', '',
           md(yagg, ['network', 'median', 'p10'], {'median': '{:.3f}', 'p10': '{:.3f}'}), '',
           '## Per formation', '',
           md(st, ['formation', 'network', 'n_firms', 'n_sic6799', 'pi_sic3', 'tau', 'q50', 'q99', 'auc_sic3', 'auc_sic3_ex6799', 'precision_sic3', 'jaccard_sic3'],
              {k: v for k, v in f.items() if k in ('pi_sic3', 'tau', 'q50', 'q99', 'auc_sic3', 'auc_sic3_ex6799', 'precision_sic3', 'jaccard_sic3')}), '',
           md(tn, ['formation', 'network', 'firms_covered', 'jaccard', 'recall_tnic', 'auc_tnic', 'spearman_score'],
              {'jaccard': '{:.3f}', 'recall_tnic': '{:.3f}', 'auc_tnic': '{:.3f}', 'spearman_score': '{:.3f}'}), '',
           '## Figures', '', '![AUC](fig_auc_sic3.png)', '', '![shape](fig_shape.png)', '', '![TNIC](fig_tnic_jaccard.png)', '',
           'Neighbour spot checks: [neighbours.md](neighbours.md).']
    (OUT / 'README.md').write_text('\n'.join(rep) + '\n')
    print(agg.to_string(index=False)); print(tagg.to_string(index=False)); print(yagg.to_string(index=False))
    print(o.mean(numeric_only=True).round(2).to_dict()); print(f'done {time.time() - t0:.0f}s')

if __name__ == '__main__':
    main()
