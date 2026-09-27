# Text-Implied Factor Space — Project Specification (v1)

Single source of truth for the project. The live hub renders this file; coding sessions read it through the project rules. Each element follows one pattern: **what it is → what it gives us → data → procedure → parameters → validation → pitfalls → interview probes → deliverables.** The interview mapping, schedule and pitch live in the private plan (`docs/private/PLAN.md`, not committed). Every factual claim below was checked against the primary source by one of five research dossiers (26 Sep 2026) and a critic pass; anything still unverified is marked ⚠️.

## 1. Thesis and what "done" means {#thesis}

### The question

Every US public company describes its products and markets in Item 1 of its 10-K (Regulation S-K Item 101: "Describe the business done and intended to be done by the registrant"). Firms that describe similar products compete for the same customers and face the same demand shocks, so the text should define an **economic neighbourhood** that fixed industry codes capture only partly.

| # | Question | Why it matters | Element |
|---|---|---|---|
| Q1 | Does text similarity explain **residual return comovement** (after FF5 + momentum) beyond historical SIC/GICS? | A risk model must know which stocks co-move for reasons its factors miss. | B, C |
| Q2 | Does a covariance estimator that **uses the text structure** beat statistical estimators out of sample? | With N ≈ T the sample covariance is noise-dominated; structure must come from somewhere. | D |
| Q3 | Do returns of a firm's text peers **predict** its future return, and did that survive publication? | Slow diffusion across linked firms is a documented anomaly; its post-publication fate is open. | E |

Element A builds the text representations all three consume.

### What already exists, and what is new here

| Prior work (verified) | What it found | What this project adds |
|---|---|---|
| Hoberg & Phillips 2016 (JPE) | Binary noun/proper-noun vectors, words in >25% of filings dropped, cosine; a 21.32% similarity threshold gives the same 2.05% pair density as SIC-3 | A dense-embedding network calibrated to the same density, compared head to head |
| Hoberg & Phillips 2018 (JFQA) | Text-peer 12-month momentum: FM coefficient 0.008 (t = 4.36, Table 3A); EW quintile FF3 alpha 1.7%/month (t = 3.30), but with a UMD loading of 1.06 (R² 0.15 → 0.75 when UMD is added); sample Jul 1997 – Dec 2012. Their own sub-periods imply the univariate slope had already faded to ≈0.0017 in 2008–12 | Our sample starts Jul 2012, so it is essentially an **out-of-sample test** of their result |
| Ali & Hirshleifer 2020 (JFE) | Shared-analyst-coverage momentum subsumes text-based momentum (text alpha −0.08, t = −0.67, controlling for it) | We cannot observe analyst coverage (I/B/E/S not subscribed); stated as a limitation |
| Antón & Polk 2014 (JF) | Monthly FM regressions of pairwise abnormal-return correlation on pair characteristics | The template for Element C |
| Lu, Ndiaye & Simaan 2024 (IRFA) | Shrinks correlation toward a Hoberg–Phillips text-network target; GMV on 400+ assets | We add dense vs BoW vs TNIC, a nested PSD target where "text adds value" is a test of b = 0, analytic and validated intensities, residual-space shrinkage, and a permutation placebo |
| McLean & Pontiff 2016 (JF) | Anomaly returns 26% lower out of sample, 58% lower after publication | Sets the prior for Q3: expect ~0.42 × HP's magnitude |

The claim in interviews is **"replication and extension"**, never "discovery".

### Keep the three questions apart

Q1 is about second moments, Q2 about *forecast* second moments, Q3 about first moments. Hoberg & Phillips' Table 2 shows the gap: the contemporaneous text-peer coefficient is 0.036 (t = 33) against 0.008 at a one-month lag. Efficient pricing of common shocks gives Q1 > 0 and Q3 = 0, so a strong Q1 result implies nothing about Q3.

### Definition of done (first milestone, Thu 8 Oct)

- **Scope:** Element A validated; **Q1 (Elements B, C) complete**; **Q3 as the HP replication on the common sample** plus the out-of-sample extension; Q2 (Element D) is a stretch goal with the core estimators only. One clean result beats three half-done ones.
- `tfs_stats/` written by Abhi, all tests green.
- `docs/PREREG.md` frozen (git hash recorded) before any test-period result is looked at.
- `docs/RESULTS.md`: 2 pages; every number reproducible by one command.
- Résumé bullet built only from numbers that exist; a 2-minute pitch; answers to the probes in each element.
- **Compliance:** WRDS data use was cleared on 27 Sep 2026 under the conditions in §2.

## 2. Compliance and licensing — read first {#compliance}

Two WRDS rules govern how this project may use CRSP and Compustat. Both were checked on WRDS's own pages, and both were settled for this project on 27 Sep 2026.

| Rule (verbatim) | Source | Status for this project |
|---|---|---|
| "loading Data retrieved from WRDS into LLMs and other Generative A.I. tools is prohibited" — except "protected" enterprise versions with a no-training data-protection agreement; CRSP and S&P are among the vendors covered | WRDS AI Policy page | **Cleared.** CMU's WRDS representative confirmed that the AI plan used here is an enterprise instance with a no-training agreement, which is the policy's exception. The assistant sessions may read and process WRDS data. |
| "Users are not permitted to script or otherwise automate … the running of queries to download data from the website. Automation is permitted on the WRDS Cloud server." | WRDS Terms of Use §1 | **Cleared under a cap.** Scripted web queries are acceptable with a definitive limit; the clause targets continuous scraping. This project's cap: at most 10 submissions per calendar day and 30 per calendar month, one query running at a time, status checks no more than once a minute, never a loop that resubmits. Every submission is logged in `docs/WRDS_QUERIES.md` before it counts as done. |
| Redistribution: "you may not reproduce, distribute, modify, adapt, create derivative works of … the Proprietary Material" | WRDS Terms of Use §2 | **Binding, unchanged.** The public repo holds code, docs and non-invertible aggregates only (see below). |

The operating rules for the assistant sessions are rules 0 and 1 in the project rules. Until 27 Sep this section recorded the question as open (decision D0) and the assistant paused all WRDS-data work; the pulls made before then, submitted by the assistant through the WRDS web interface with Abhi's approval, are logged in `docs/WRDS_QUERIES.md`.

Everything SEC-derived (10-K text, embeddings, filing dates) is public: "Information presented on sec.gov is considered public information and may be copied or further distributed". Ken French factors are public with attribution. Hoberg–Phillips data carry no posted terms; cite them.

**What may go in the public repo:** code, configs, docs, SEC-derived text features keyed by CIK + accession (not by PERMNO/gvkey), regression tables, t-statistics, figures. **Never:** any firm-level CRSP/Compustat/CCM/TNIC row, anything keyed by PERMNO or gvkey, the CIK↔PERMNO crosswalk, firm-level residuals, betas or return-based signals (a published signal s = W r with public W is invertible back to r). The README carries WRDS's required citation sentence.

## 3. Data, universe and point-in-time rules {#data}

### Sources

| Source | Gives us | Coverage pulled | Key | Licence |
|---|---|---|---|---|
| SEC bulk `submissions.zip` (incl. overflow files) | Form, filing date, acceptance time (UTC), primary document for every filing | All filers | CIK | Public |
| EDGAR 10-K primary documents | Item 1 text | 61,589 10-K/10-KT, Jun 2011 – Sep 2026 (start chosen so every firm has a 10-K by Jul 2012, when the daily-return window allows the first estimates; ≈4,000 per year matches the universe) | CIK + accession | Public |
| CRSP Stock v2 (CIZ) monthly | Total return (delisting folded in), market cap ($000s), share/issuer type, exchange | 2009-01 → 2026-06 | PERMNO | WRDS |
| CRSP Stock v2 (CIZ) daily | Daily total return, market cap | 2010-01-04 → 2026-03-31, 16.1M rows for universe PERMNOs | PERMNO | WRDS |
| CCM link table | gvkey ↔ PERMNO history, current CIK, SIC, GICS | 32,948 links | gvkey | WRDS |
| CCM Fundamentals Annual | Book equity inputs, historical SIC (`sich`) | FY2008 → FY2026 | gvkey | WRDS |
| Ken French library | FF5 (2×3) + momentum, daily and monthly (CIZ-based since Jan 2025) | to 2026-08 | date | Public, cite |
| Hoberg–Phillips TNIC-3 | Pairwise text network, `score` = similarity − threshold, unlagged, keyed by gvkey and datadate year | 1989 → 2023 | gvkey | Cite |

### Universe (corrected in v1)

US-incorporated operating common stock on NYSE, NYSE American or Nasdaq, as of each month:
`ShareType = NS`, `SecurityType = EQTY`, `SecuritySubType = COM`, `USIncFlg = Y`, **`IssuerType ∈ {ACOR, CORP}`**, `PrimaryExch ∈ {N, A, Q}`, `ConditionalType ∈ {RW, NW}`.
This reproduces legacy `SHRCD ∈ {10, 11}` (CRSP share-code crosswalk; Tidy Finance). **v0 omitted IssuerType and so included REITs (legacy code 18).** `TradingStatusFlg` is applied at formation only, so a delisting month's return is kept. Market cap = `MthCap × 1000`.

**Shell companies excluded (D8, 27 Sep).** A firm-year is dropped when its 10-K is a blank-check (SPAC) filing: historical SIC ∈ {6770, 6799} and the first ~2,000 words of Item 1 contain "blank check", "business combination" or "trust account". The flag is set per filing, so a SPAC that completes its merger re-enters with its first operating 10-K. The reason is economic and was fixed before any return-based test was run: a SPAC has no operating business, its Item 1 is boilerplate shared with other SPACs (a text cluster with no economic content), and its shares trade near the trust value, so its returns are close to a T-bill's. 468 were in the June 2022 universe. The count of true operating firms in SIC 6799 caught by the text rule is reported.

### Delisting returns

CIZ `MthRet` "will include delisting returns if appropriate". Where `MthDelFlg ∈ {M, G}` (missing, or more than 10 days from delisting) the delisting return is excluded; impute δ = −30% (NYSE/AMEX) or −55% (Nasdaq, Shumway & Warther 1999) for performance-related delistings, with sensitivity δ ∈ {0, −30%, −100%}, and report counts. In daily data the delisting return sits on the trading day after the last trade.

### Linking text to returns

CIK → gvkey → PERMNO: CCM links with `LINKTYPE ∈ {LC, LU}`, `LINKPRIM ∈ {P, C}`, valid **on the 10-K availability date**; null end dates mean active. Compustat stores only the *current* CIK (Hoberg–Phillips readme), so firms whose CIK changed are lost: 92.3% of the 61,589 indexed filings mapped under the v0 universe; with REITs excluded (v1), 54,602 map and 54,254 firm-years remain. Enforce one PERMNO per gvkey-date and one gvkey per PERMNO-date; collapse to one PERMNO per PERMCO (largest cap); dedupe co-registrant filings by accession.

### Point-in-time rules

| Information | Usable from | Rationale |
|---|---|---|
| A 10-K | the NYSE trading day after its **filing date** | Filings submitted after 5:30 pm ET are dated the next business day (17 CFR 232.13); `acceptanceDateTime` is genuine UTC (checked against index pages) and is used only for audit |
| A text vintage | until the next 10-K; dropped if older than 15 months | 12 months + 90-day deadline + 15-day 12b-25 extension |
| Book equity | Fama–French convention (fiscal year ending in t−1 used from June t) | at least a 6-month gap |
| Industry codes | Compustat historical `sich`; GICS history if available | Header SIC/GICS are current snapshots and would leak reclassifications |
| Size, universe | end of the prior month | |
| Bag-of-words vocabulary | filings available in the trailing 12 months at formation | a calendar-year vocabulary would include future filings |

### Structural break

SEC Release 33-10825 (effective 9 Nov 2020) made Item 101 principles-based and added human capital disclosure, which raises baseline similarity across all firms. Similarities are demeaned within each cross-section, and results are reported pre/post FY2020.

## 4. Ingestion pipeline {#pipeline}

| Stage | Script | Output | Status / checks |
|---|---|---|---|
| P0 WRDS to parquet | `src/convert_wrds.py` | `crsp_msf`, `crsp_dsf_*`, `ccm_funda` parquet | Row counts match `docs/WRDS_QUERIES.md` |
| P1 Filing index | `src/build_filing_index.py` | 61,589 10-K/10-KT (parses `recent` and overflow files) | Check: JPM, BAC, GS, C have one 10-K per year 2012–2026 |
| P2 Item 1 extraction | `src/scrape_item1.py`, `src/item1.py`, `src/rescue_item1.py` (P2b) | Item 1 text shards | ≤8 req/s. v1 left 3.7% with 0 words (concentrated in SIC 29/10/13/49: "Items 1 and 2" headings); 0/60 sampled failures incorporate Item 1 from EX-13. The v2 fallback recovers 1,836 of 2,254; 99.2% of 61,589 filings now > 300 words. **D10 (27 Sep):** one re-download of all 61,589 primary documents with the raw HTML stored gzip-compressed (`data/raw/edgar_html/`), v1 and v2 run on each, the canonical span chosen by a structural rule validated on ~100 hand-checked v1/v2 disagreements; the text layer is then frozen |
| P3 Links | `src/build_links.py` | 54,254 firm-years (v0: 56,495) | Re-run with the corrected universe (27 Sep) |
| P4 Panels | `src/build_panel.py` | monthly, daily, FF | Re-run with IssuerType/ConditionalType filters (27 Sep) |
| P5 Embeddings | `src/embed_item1.py` | 384-d unit vectors | First 2 × 500 tokens; firm names anonymised in a later pass (see A) |
| P6 Bag of words | `src/bow.py` (v1; `src/tfidf.py` = v0) | per-filing word counts; binary unit vectors per formation date | Vocabulary from filings in [t − 365 d, t); nouns variant (WordNet nouns + proper nouns). v1 vs v0 pair-similarity correlation 0.98–1.00 |

**Item 1 method.** Strip HTML (drop `ix:header` and hidden nodes), find every "Item 1 Business" heading and every "Item 1A / 1B / 1C / Item 2" heading, take the longest start-to-end span with no other "Item 1" heading inside (that rejects table-of-contents entries). Where that yields < 300 words, a line-aware v2 (headings only at line starts, plural "Items 1 and 2", "Description of Business", zero-width characters) is used if it finds more text; on 40 filings where v1 works, the two agree (word-set Jaccard median 1.00, 82% > 0.8). Validation against EDGAR-CORPUS (Loukas et al. 2021) on the 2011–2020 overlap: word-set Jaccard, share above 0.8. EDGAR-CORPUS cannot replace the scraper: it stops in 2020.

## 5. Element A — Text networks {#element-a}

### What it gives us

For each formation date, a similarity $s_{ij}$ for every pair of firms and a peer set $P_i$. Four networks, all calibrated to the **same pair density**, so no network wins just by being coarser or finer.

### Networks

1. **HP TNIC-3 (benchmark).** Drop self-pairs; map gvkey → PERMNO with links valid at formation; `score` is $s_{ij} - \tau$. Year = fiscal-year-end year, unlagged in the file: use year $Y$ from July $Y{+}1$ to June $Y{+}2$. Available through formation June 2025.
2. **Bag-of-words (our HP replication).** Binary word-presence vector $b_i$, unit-normalised $v_i = b_i/\lVert b_i\rVert$, similarity $s_{ij} = v_i^\top v_j$. Vocabulary: alphabetic tokens, stop words and geographic terms removed, words in more than 25% of documents dropped; a **nouns and proper nouns** variant (proper noun = capitalised at least 90% of the time, the HP rule). HP found "uniform weights outperform TF-IDF weights". **Length correction (D9, 27 Sep).** Binary cosine rises mechanically with document length. If firm $i$ uses $n_i$ of $V$ vocabulary words roughly at random, $\mathbb E\,|b_i \wedge b_j| \approx n_i n_j / V$, so $\mathbb E\, s_{ij} \approx \sqrt{n_i n_j}/V$ (observed: the correlation of log Item 1 length with a firm's mean similarity is +0.94 for BoW, −0.23 for the dense embedding). Peers are therefore chosen on a degree-corrected similarity. With $m_i$ firm $i$'s median similarity in the formation cross-section, $m_i \propto \sqrt{n_i}$ under that null, so the matching correction is multiplicative, $\tilde s_{ij} = s_{ij}/(m_i m_j)$; the additive form $s_{ij} - \tfrac12(m_i + m_j)$ is computed alongside. The version is chosen on Element A diagnostics only (length correlation removed; same-SIC-3 AUC and TNIC-3 agreement kept) before any return-based test is run. Raw BoW stays as a robustness network, and length terms stay in C. Optional: purge vertical pairs (>1% input share in BEA Use tables).
3. **Dense (bge-small-en-v1.5, 384-d).** Average chunk embeddings, centre each cross-section and renormalise:
$$ \tilde e_i = \frac{e_i - \bar e}{\lVert e_i - \bar e\rVert}, \qquad s^{D}_{ij} = \tilde e_i^\top \tilde e_j . $$
Raw bge cosines are compressed into a high band, so absolute levels mean nothing; only ranks and density-calibrated thresholds are used.
4. **Industry baselines.** Same SIC-3 (historical), same GICS industry where history is available.

### Density calibration (Hoberg–Phillips' core principle)

Each formation date, $\pi = $ share of all pairs that share a SIC-3 code (≈2.05% in HP). For each text network, choose $\tau$ as the $(1-\pi)$ quantile of $s_{ij}$; peers are pairs with $s_{ij} > \tau$. Also build SIC-4-, SIC-2- and SIC-1-matched bands (HP Table 7).

### Validation

- AUC of $s_{ij}$ for classifying same-SIC-3 pairs; within- vs cross-industry means.
- Top-10 neighbours for 15 well-known firms, checked by eye.
- Agreement with TNIC-3: Jaccard of peer sets at matched density; rank correlation of scores.
- Same-firm year-over-year similarity.
- Correlation of similarity with document length (should be near zero after normalisation).

### Pitfalls

- **Pretraining look-ahead.** bge-small-en-v1.5 was released 12 Sep 2023 and trained on web text written after most of the sample. HP avoid BERT/GPT for this reason. Guards: bag-of-words is pretraining-free; a post-Sep-2023 subsample is a clean test; firm names and tickers are masked before embedding (Glasserman & Lin 2023).
- **Truncation.** v1 embeds only the first ~1,000 tokens (the overview). That also partly protects against the post-2020 human-capital boilerplate, which sits later in Item 1; a full-text version must strip that subsection first.
- **Missing text.** Firms without a usable Item 1 are excluded from the text networks (a centred mean embedding is the zero vector and cannot be normalised); coverage is reported and inverse-probability weights are a robustness check.
- **Hub firms.** Conglomerates and boilerplate-heavy filings are similar to everyone; firm fixed effects and length controls in C.
- **Duplicates.** Same-PERMCO share classes and co-registrant filings have similarity ≈ 1; excluded.

### Interview probes

- *Why calibrate to SIC-3 density?* Otherwise a finer network looks "better" only because it is finer; matched density makes the comparison about which pairs, not how many.
- *Why centre the embeddings?* Sentence embeddings share a dominant common direction; removing the mean makes similarity reflect differences between firms.
- *Could the embedding know the future?* Yes in principle; hence the BoW control and the post-2023 window.

### Deliverables

AUC and agreement tables, neighbour table, density-band definitions; `analysis/a_text_layer.py`.

## 6. Element B — The residual factor space and its spectrum {#element-b}

### What it gives us

What structure is left in returns after standard factors, separated from noise by random matrix theory, and whether that structure lines up with text.

### Procedure

1. **Universe.** The 500 largest stocks at each formation date with complete daily returns over the window; one PERMNO per PERMCO; of any pair with correlation above 0.95, drop the less liquid stock.
2. **Residualise with rolling betas.** For each stock, regress daily excess returns on FF5 + momentum over the 252 trading days ending at the formation date:
$$ x_{it} = \alpha_i + \beta_i^\top f_t + \varepsilon_{it}. $$
Full-sample betas are rejected: they are look-ahead, and drifting betas leave $(\beta_{it}-\bar\beta_i)^\top\Sigma_f(\beta_{jt}-\bar\beta_j)$ in the residual covariance, which is larger for economically similar firms and would manufacture the result.
3. **Correlation matrix** of standardised residuals, $C = \frac{1}{T} Z^\top Z$, with effective $q = N/(T-K-1)$.
4. **Noise edge.** Marchenko–Pastur: $\lambda_\pm = \sigma^2(1 \pm \sqrt q)^2$. For raw returns, Laloux et al. (1999) set $\sigma^2 = 1 - \lambda_{\max}/N$ (they found 0.85; best fit 0.74). Generalise by iterating $\sigma^2 = 1 - \sum_{\lambda_k > \lambda_+}\lambda_k / N$ to convergence. Empirical edge: circularly shift each stock's series by a random offset (200 draws), keeping each series' autocorrelation but destroying synchrony; take the 95th percentile of the top eigenvalue. Heteroskedasticity and autocorrelation widen the bulk ($q_{\text{eff}} \approx 1.1$–$1.2\,q$ in Bun, Bouchaud & Potters 2017).

| N | T | q | λ₊ | λ₋ |
|---|---|---|---|---|
| 500 | 1008 | 0.496 | 2.905 | 0.087 |
| 500 | 756 | 0.661 | 3.288 | 0.035 |
| 500 | 504 | 0.992 | 3.984 | ≈ 0 |

For residuals the effective q is $N/(T-K-1)$: at $T = 504$, $K = 6$ it is $500/497 > 1$, so the residual sample matrix is singular, not merely ill-conditioned. Element B therefore uses $T = 756$ or $1{,}008$.

5. **Localisation.** $\text{IPR}_k = \sum_i u_{ki}^4$ (Plerou et al. 2002, eq. 20); $1/\text{IPR}_k$ is the effective number of stocks in mode $k$. Random vectors give IPR ≈ 1/N.
6. **Text alignment per mode.** $A_k = u_k^\top \tilde G\, u_k$ with $\tilde G$ the similarity matrix with zero diagonal; p-value from 1,000 relabellings of firms. Repeat with the SIC-3 co-membership matrix, and with text similarity residualised on industry dummies ("beyond industry").
7. **Subspace overlap.** Principal angles between the span of residual modes above the edge and the top-K eigenvectors of the text Gram matrix; a random K-dimensional subspace has expected squared overlap K/N.

### Reference result

Plerou et al. (2002): after removing the market mode, deviating eigenvectors group "similar or related industries", and one ($u_{995}$) mixes three industries whose firms share "significant business activity in Latin America", a link SIC misses. That is the kind of mode text should catch.

### Interview probes

- *Why does the sample matrix mislead?* In-sample risk of an optimised portfolio is understated: $R^2_{\text{in}} = (1-q)R^2_{\text{true}}$, $R^2_{\text{out}} = R^2_{\text{true}}/(1-q)$ (Bun, Bouchaud & Potters 2017, eq. 7.19).
- *Why $\sigma^2 = 1 - \lambda_1/N$?* The trace of a correlation matrix is $N$; the market mode takes $\lambda_1$ of it.
- *Does MP need Gaussian returns?* No; temporal dependence does shift the effective q.

### Deliverables

Spectrum vs MP density (raw and residual), eigenvalues above the edge per year, IPR plot, alignment z-scores for text vs SIC, subspace-overlap series.

## 7. Element C — Pairwise comovement beyond industry codes {#element-c}

### What it gives us

The direct answer to Q1: how much a pair's residual correlation rises with text similarity, holding industry, size, value and momentum similarity fixed, with inference that respects dependence between pairs.

### Procedure (Antón & Polk 2014 template)

1. **Pairs.** Each month, the 1,000 largest stocks: 499,500 pairs.
2. **Outcome.** Within-month correlation of daily FF6 residuals (betas from the trailing 252 days ending the day **before** the month, at least 15 days in the month), Fisher-transformed: $z_{ij,t} = \operatorname{atanh}(\hat\rho_{ij,t})$. Antón & Polk report a cross-sectional SD of about 0.25; a single month's $\hat\rho$ from ~21 days has SE ≈ 0.22, so 12-month non-overlapping windows are the robustness version.
3. **Framing: a forecast.** Text is dated before the window in which comovement is measured. That rules out reverse causality (firms that co-move copying each other's descriptions).
4. **Regression each month:**
$$ z_{ij,t} = a_t + b_t\,\tilde s_{ij} + \phi_t\, z^{\text{lag}}_{ij} + \sum_{\ell} c_{\ell t}\,\mathbb 1[\text{same SIC-}\ell] + d_t^\top w_{ij} + u_{ij,t}, $$
where $\tilde s$ is standardised within the month; $z^{\text{lag}}_{ij}$ is the pair's residual correlation over the prior 12 months, **the history baseline**: the best predictor of future comovement is past comovement, so text must add to it; $w_{ij}$ holds Antón–Polk rank distances in size, book-to-market and momentum, $|\Delta\hat\beta_k|$ per factor, liquidity (Amihud) distance, same fiscal-year-end month (earnings-announcement clustering), document-length terms and a same-exchange dummy.
5. **Estimate** $\bar b = \frac1T\sum_t b_t$ from monthly sufficient statistics ($X^\top X$, $X^\top y$); the ~1B pair-month panel is never materialised.
6. **Shape.** Plot mean $z$ by similarity percentile: the economics should live in the top ~2%.
7. **Beyond statistical factors.** Robustness: residualise on FF6 plus 5–10 principal components. Text that only proxies unmodelled macro betas (oil, rates, dollar) loses its coefficient there.

### Inference

Pairs sharing a firm are dependent: information scales with the number of firms, not pairs (Graham: rate $\sqrt N$).

- **Primary:** Fama–MacBeth with Newey–West, $L = \lfloor 4(T/100)^{2/9}\rfloor = 4$ at $T = 167$; also EWC with $\nu = \lfloor 0.4\,T^{2/3}\rfloor = 12$ and $t_{12}$ critical values (Lazarus, Lewis, Stock & Watson 2018: short NW lags over-reject). Report the autocorrelation of $b_t$: pair effects are persistent, and Petersen (2009) shows FM-NW is then still biased down.
- **Robustness 1: MRQAP, double semi-partialling** (Dekker, Krackhardt & Snijders 2007) on annual July–June cross-sections: residualise $s$ on the controls, permute firm labels of the residual (rows and columns together), re-fit, record the OLS t (pivotal), 999 draws, $p = (1 + \#\{|t_b| \ge |t_{obs}|\})/1000$; pool years with the same permutation.
- **Robustness 2: pooled OLS with dyadic-robust errors** (Aronow, Samii & Assenova 2015; Cameron & Miller 2014): meat $= \sum_i g_i g_i^\top - \sum_{i<j} h_{ij}h_{ij}^\top$, finite-sample factor $G/(G-1)\cdot n/(n-k)$, $t_{G-1}$ critical values.

### Pitfalls

Size (large firms are both more similar and more correlated), asynchronous trading of illiquid pairs (Epps effect; Dimson lags, 2-day or weekly returns), noisy similarity attenuating $b$ toward zero (so "text beats SIC" partly rewards the less noisy measure), and confounds we cannot observe with current data: common institutional ownership (13F), analyst co-coverage (I/B/E/S), index/ETF co-membership, vertical input–output links. Continuous similarity has more degrees of freedom than industry dummies, so horse races against SIC also use the density-matched binary network.

### Interview probes

- *Why isn't t = 500 with half a million pairs?* Dependence through shared firms; show the dyadic-robust SE.
- *Explain QAP.* Relabel firms jointly on rows and columns: keeps the network's structure, breaks only the link between X and Y. DSP permutes the part of X orthogonal to the controls, so collinearity with SIC does not break the test.
- *Why Fisher-z?* It makes the variance of $\hat\rho$ roughly $1/(T-3)$, independent of $\rho$.

### Deliverables

$\bar b$ with FM-NW, EWC, MRQAP and dyadic columns; incremental $R^2$ over industry; out-of-sample predictive $R^2$ of next-month pair correlations.

## 8. Element D — Covariance horse race {#element-d}

### What it gives us

A practical test of Q2: does text structure make covariance matrices that build lower-risk portfolios?

### The text target (and why it is a valid correlation matrix)

With unit-norm rows in $V$ ($N\times d$), $G = VV^\top$ is PSD ($x^\top G x = \lVert V^\top x\rVert^2 \ge 0$), has unit diagonal, and $|g_{ij}| \le 1$. It is rank-deficient when $d < N$ and mis-scaled, so use the nested target
$$ T(a,b) = a\,\mathbf 1\mathbf 1^\top + b\,G + (1-a-b)\,I,\qquad a,b \ge 0,\; a+b<1 , $$
positive definite with unit diagonal. $b = 0$ is exactly Ledoit–Wolf's constant-correlation target, so **"text adds value" is the test $H_0: b = 0$.** Industry codes fit the same template ($B = ZZ^\top$ from one-hot industry dummies). $(a, b)$ are fitted by constrained least squares of off-diagonal residual correlations on $g_{ij}$ over a window that ends before the estimation window. Thresholded networks (TNIC top-k) are not PSD and must be projected (Higham 2002).

### Shrinkage intensity

For one entry with sample value $u$ ($E u = \rho$) and fixed target $t$: $E[(\delta t + (1-\delta)u - \rho)^2] = (1-\delta)^2\operatorname{Var}(u) + \delta^2 (t-\rho)^2$, minimised at $\delta^* = \operatorname{Var}(u)/[\operatorname{Var}(u) + (t-\rho)^2]$. Summing over pairs:
$$ \hat\delta = \frac{\sum_{i\ne j}\widehat{\operatorname{Var}}(r_{ij})}{\sum_{i\ne j}(r_{ij} - t_{ij})^2} \in [0,1] $$
(Schäfer & Strimmer 2005, eq. 8). A useless target inflates the denominator and drives $\hat\delta \to 0$ automatically. Because Frobenius-optimal is not GMV-optimal, also report a validated intensity chosen on the last 63 days of each window.

### Estimators (same universe, same variance model $\hat\Sigma = \hat D^{1/2}\hat R\hat D^{1/2}$)

| # | Estimator | Source |
|---|---|---|
| 1 | Sample | — |
| 2 | Ledoit–Wolf, identity target | LW 2004 JMVA |
| 3 | Ledoit–Wolf, single-index target | LW 2003 JEF |
| 4 | Ledoit–Wolf, constant correlation = $T(a,0)$ | LW 2004 JPM |
| 5 | RMT clipping (bulk eigenvalues → their mean, trace kept) | Laloux et al. 1999; BBP eq. 7.55 |
| 6 | Rotationally invariant estimator | BBP 2017 |
| 7 | Analytical nonlinear shrinkage | LW 2020 AoS |
| 8 | Industry target $T_{\text{ind}}(a,b)$ | this project |
| 9 | Text targets (BoW, dense, TNIC) | this project |
| 10 | Text-preconditioned nonlinear shrinkage | LW 2017 RFS eq. 16 |
| 11 | FF6 factor model, diagonal residuals | — |
| 12 | FF6 factor model + text-shrunk residual correlation | this project |
| 13 | **Placebo:** #9 with $G$ replaced by $PGP^\top$ (random relabelling) | same spectrum, no content |
| 14 | 1/N | DeMiguel, Garlappi & Uppal 2009 |
| 15 | PCA / POET statistical factor model | practitioner benchmark |
| 16 | GICS industry + style factor model (Barra-like) | practitioner benchmark |

### Protocol (Engle, Ledoit & Wolf 2019; LW 2017)

Rebalance every 21 trading days from July 2012 to March 2026 (about 3,450 out-of-sample days). Estimation window $T = 252$ primary (the LW 2017 template); 504 and 1,008 as robustness; $N = 500$, with $N = 1{,}000$ as a mid-cap robustness where industry codes are coarser and text may help more. **Primary benchmark: LW analytical nonlinear shrinkage** (#7); the practitioner benchmarks a PCA/POET statistical factor model and a GICS industry-plus-style model are added. The question is "does text beat a statistical risk model", not only "does it beat Ledoit–Wolf". GMV portfolios concentrate in low-volatility defensives, so factor-neutral long-short test portfolios and bias statistics on random portfolios are reported too. Universe requires only a complete *past* window (the "complete future" filter is infeasible in real time); after delisting, the position earns the risk-free rate. Unconstrained GMV $w = \hat\Sigma^{-1}\mathbf 1/(\mathbf 1^\top\hat\Sigma^{-1}\mathbf 1)$ via a linear solve; long-only as robustness (constraints act as shrinkage and hide differences, Jagannathan & Ma 2003).

**Metrics:** annualised out-of-sample SD (primary), turnover, gross leverage, max weight, bias ratio $\sigma^2_{\text{realised}}/\sigma^2_{\text{predicted}}$.

**Test:** $\Delta = \log\hat\sigma^2_A - \log\hat\sigma^2_B$ with the prewhitened HAC method (Ledoit & Wolf 2011) and a studentised circular block bootstrap; Holm/Romano–Wolf across estimators. The F-test is invalid for correlated, heavy-tailed returns. **Power:** with $T_{out} \approx 3{,}450$ and correlation 0.95 between the two portfolios, $\operatorname{SE}(\hat\Delta) \approx \sqrt{4(1-0.95^2)/3450} = 0.0106$; the smallest detectable difference is about 2% in variance (≈1% in volatility), and fat tails raise that 1.4–2×. BBP's own gaps between good estimators are 0.1–0.2 volatility points (RIE 10.4, LW 10.5, clipping 10.6, sample 11.6), so a null is a likely outcome and must be reported as a confidence interval.

### Interview probes

- *Why GMV?* Its weights depend only on $\Sigma$, so realised volatility isolates covariance quality.
- *Derive GMV weights.* Minimise $w^\top\Sigma w$ s.t. $\mathbf 1^\top w = 1$: $\Sigma w = \lambda\mathbf 1$.
- *Nonlinear shrinkage is optimal, so why text?* Only among estimators that keep the sample eigenvectors; text carries information about the eigenvectors themselves, which preconditioning uses.

## 9. Element E — Text-peer momentum, out of sample {#element-e}

### What it gives us

A test of whether shocks to a firm's text peers diffuse slowly into its price, on a sample that starts where Hoberg & Phillips (2018) ended.

### Signals (pre-registered)

With $R_j(a,b) = \prod_{m=a}^{b}(1+r_{jm}) - 1$ and $P_i$ the density-calibrated peer set excluding $i$ and same-PERMCO firms:

1. **Primary (HP's definition):** $\text{PEERMOM}_i = \frac{1}{|P_i|}\sum_{j\in P_i} R_j(t-12, t-1)$, equal-weighted peers (HP: shocks to small, less-watched peers are priced more slowly). Construction fixed in advance: peers are fixed at the formation date, each peer's own 12-month return is compounded, then averaged (HP Table 1's mean of 0.158 is consistent with a cumulative return); price ≥ $1 as in HP.
2. Similarity-weighted: $w_{ij} \propto (s_{ij}-\tau)_+$.
3. Horizon splits: $R(t-6,t-1)$ vs $R(t-12,t-7)$; $R(t-12,t-2)$ with $R(t-1)$ separate (Grundy–Martin); $R(t-24,t-13)$ as a placebo.
4. Idiosyncratic peer returns: $e_{jm} = r_{jm} - \hat\beta_j^\top f_m$ with trailing betas.
5. Visibility: TEXT-only ($P^{text}\setminus P^{SIC3}$), SIC-only, both; and **DENSE-only** $= P^{dense}\setminus(P^{TNIC}\cup P^{SIC3})$, links invisible to both SIC and the public TNIC file (new).

### Tests

- **Fama–MacBeth** on excess returns, right-hand side z-scored monthly, winsorised 1/99: controls log ME, log BM, own $r_{t-1}$, own $R(t-12,t-2)$, value-weighted FF-48 industry momentum, TNIC momentum (in the extension), input–output customer/supplier momentum where available. Connected-firm (analyst co-coverage) momentum needs I/B/E/S and is a stated gap: Ali & Hirshleifer subsume a *1-month, score-weighted* text signal, so for HP's 12-month signal the question is open. NW(2) for comparability with HP, NW(4) and EWC(12) as the honest version.
- **Portfolios:** quintile (HP) and decile sorts, NYSE breakpoints, equal- and value-weighted, 1-month hold; FF3, FF3+UMD, FF5+UMD and FF5+UMD+short-term-reversal alphas; price ≥ $1 and ≥ $5; NYSE-20th-percentile screen; net of costs; event-time long-short returns for months +1 to +24. The HP long-short loads 1.06 on UMD, so momentum-crash risk (2009) is reported explicitly.
- **Permutation nulls (a uniform shuffle is too weak: random peers average toward the market):** (a) stratified peer substitution within FF-48 industry × NYSE size tercile, held fixed within each vintage, 999 draws, one-sided $p = (1+\#\{t_b \ge t_{obs}\})/(B+1)$, and report the mean $t_b$; (b) Moskowitz–Grinblatt/HP random peers matched on past-return rank; (c) stale network from year $y-3$.
- **Periods:** development Jul 2012 – Nov 2018 (tuning allowed), test Dec 2018 – Jun 2026 (HP 2018 appeared online 9 Nov 2018, print December; untouched until PREREG is frozen); plus post-Sep-2023 for the encoder. The paper was on SSRN from Oct 2014 and TNIC data were public earlier, so the development period is "out-of-sample, pre-journal", not truly pre-publication. For the *new* dense-only signal a test-period drop means overfitting or time variation, not publication decay.
- **HP benchmark:** reproduce HP Table 3A (0.008, t = 4.36) and Table 11B (1.7%/month, t = 3.30) with their own TNIC-3 on the common sample, then swap in our networks holding everything else fixed.

### Power (derived from HP's own numbers)

**What to expect.** HP's full-sample and pre-2008 Fama–MacBeth means imply the 2008–12 mean: $\bar b_{08\text{–}12} = (186\,\bar b_{\text{full}} - 126\,\bar b_{\text{pre}})/60$. With the univariate slope (0.008 full, 0.011 pre) that is ≈0.0017 (bounds −0.0009 to 0.0043 from rounding); with full controls (0.008, 0.009) it is ≈0.0059 (0.0033 to 0.0085). The univariate effect had largely faded before our sample begins; the controlled one had not.

**Fama–MacBeth power.** Full-control spec: SE $= 0.008/4.36 = 0.00183$ over 186 months, so the SD of monthly slopes is $\sigma_b = 0.00183\sqrt{186} = 0.0250$.

| True slope | t at T = 90 (test period) | t at T = 165 (full) |
|---|---|---|
| 0.0034 (McLean–Pontiff 58% decay) | 1.3 | 1.7 |
| 0.0059 (HP's own 2008–12, controlled) | 2.2 | 3.0 |

**Portfolio power.** From HP Table 11B, residual SD $\sigma_\varepsilon = \sqrt{12}\,\alpha/\text{Sharpe}$: ≈6.9%/month (FF3) and ≈3.9%/month (FF3 + UMD). Minimum detectable alpha at 80% power is $2.80\,\sigma_\varepsilon/\sqrt T$:

| Model | T = 90 | T = 165 |
|---|---|---|
| FF3 | 2.0%/month | 1.5%/month |
| FF3 + UMD | 1.15%/month | 0.85%/month |

**So an insignificant test-period result is not evidence the effect is gone.** Report confidence intervals and the pre/post difference, never a significance verdict alone.

### Interview probes

- *Isn't this own momentum?* Own $R(t-12,t-2)$ and $r_{t-1}$ are controls, UMD is in the alphas; in HP the text coefficient barely moves.
- *Risk or mispricing?* Only idiosyncratic peer shocks predict beyond two months (HP Table 8) and only local bands matter (Table 7); diversifiable local shocks should not carry a premium.
- *What does your permutation null preserve?* Degree, weights, peers' industry and size composition, within-vintage persistence; it destroys only which specific firms are the peers.
- *Analyst co-coverage?* Ali & Hirshleifer show it subsumes text momentum; not observable here, stated as a limitation.

## 10. Inference and pre-registration protocol {#inference}

1. **Registry.** `docs/PREREG.md` + `specs.yaml` list every specification (id, hypothesis, family, predicted sign), committed with a git hash before any test-period code runs. The runner rejects unregistered specs and appends each execution to `runs.log`; the count of specs for multiple-testing adjustments comes from that log.
2. **Confirmatory family (3 tests, Holm at 5%: thresholds 0.0167, 0.025, 0.05).** H1: $\bar b > 0$ in C (one similarity measure chosen in advance). H2: $\sigma_{\text{text}} < \sigma_{\text{LW-NL}}$ (analytical nonlinear shrinkage) in the test period (D; stretch goal, so H2 may be deferred and the family shrinks to two). H3: PEERMOM slope > 0 with SIC-3 and TNIC controls (E), also reported against the Harvey–Liu–Zhu $t > 3$ hurdle.
3. **Exploratory family.** Benjamini–Hochberg at $q = 0.10$; Benjamini–Yekutieli as a check under arbitrary dependence; Romano–Wolf stepdown with a block bootstrap of months across FM slope series.
4. **Standard errors by problem.** Monthly slope series → NW + EWC. Pairs → MRQAP-DSP + dyadic-robust. Variance comparisons → LW 2011 HAC + block bootstrap.
5. **Placebos.** Relabelled networks (B, C, D), stratified peer substitution (E), stale networks, lagged-returns placebo.
6. **Report everything run** (Harvey 2017: "Report all results").

## 11. Repository, tooling and ownership {#repo}

```
text-factor-space/
├── docs/  SPEC · STATUS · PREREG · DATA · RESULTS
├── src/          pipeline P1–P6
├── tfs_stats/    estimators and inference (Abhi writes these)
├── tests/        checked against statsmodels / scikit-learn; unimplemented = skipped
├── analysis/     element scripts → tables and figures
├── hub/          builds the hub from docs/SPEC.md
└── data/         gitignored
```

| Part | Written by |
|---|---|
| Pipeline, parsing, plotting, hub, tests | AI assistant |
| `tfs_stats/` | **Abhi**, by hand |
| `analysis/` | Abhi drives; The assistant assists (WRDS use cleared, §2); every estimator comes from `tfs_stats/` |

**Sync model.** Long jobs (EDGAR scraping, embeddings on the Mac's GPU, panel builds) run on the Mac under a local session, which owns `git pull --rebase` and `git push`. A cloud session plans, reviews and keeps the status hub current; it writes into `~/Downloads/text-factor-space` and commits with a `` prefix. The two sessions exchange requests and progress reports through a gitignored `notes/` folder, and context passes through the project rules, `docs/SPEC.md` and `docs/STATUS.md`.

## 12. Risks and limitations {#risks}

| Risk | Effect | Mitigation |
|---|---|---|
| WRDS licence and query terms | Redistribution would breach the licence; an uncapped query loop would breach the Terms of Use | The assistant use cleared 27 Sep (§2); `data/` gitignored, aggregates only; query cap and log in `docs/WRDS_QUERIES.md` |
| Low power post-2018 (E) and small gaps between estimators (D) | Nulls likely | Power analysis stated up front; confidence intervals; pre/post differences |
| Current-only CIK | ~8% of filings unmapped, possibly non-random | Report coverage by size/industry; EDGAR `formerNames` matching as fallback |
| Item 1 extraction failures (~9%) | Skews away from banks, small firms, incorporation-by-reference filers | Coverage report; EX-13 fallback; inverse-probability weights |
| Encoder pretraining look-ahead | Dense results could be flattered | BoW control, post-Sep-2023 window, name masking |
| Nov 2020 Item 101 change | Baseline similarity shift | Cross-sectional demeaning; pre/post FY2020 |
| Analyst co-coverage not observable | Text effect may proxy for it | Stated limitation (Ali & Hirshleifer 2020) |
| Time | Scope creep before 8 Oct | Hard stop Fri 2 Oct; cut order |

## 13. Decisions {#decisions}

**Open**

| ID | Decision | Recommendation |
|---|---|---|
| D5 | Element D design | Stretch goal; T = 252, N = 500, primary benchmark LW nonlinear shrinkage |
| D6 | What is public in the repo | Public: research design, code, data-reproduction docs. Private (gitignored, on the Mac and in the hub only): interview mapping, schedule, pitch, live status seed |

**Resolved**

| ID | Decision | Outcome |
|---|---|---|
| D0 | How to handle WRDS data given the AI and automation terms (§2) | Cleared 27 Sep 2026: enterprise no-training plan confirmed by CMU's WRDS representative; scripted queries capped (§2) |
| D1 | Repo name | `akraghavan/text-factor-space`, created 27 Sep |
| D7 | Align this spec and the local permissions with the WRDS clearance | Done 27 Sep |
| D2 | Primary similarity for the confirmatory tests | Adopted (27 Sep): dense embedding (centred, names masked) for H1, comovement, where pretraining leakage matters least; bag-of-words for H3, predictability, which must be leakage-free |
| D3 | Embedding input | Adopted (27 Sep): first 2 × 500 tokens of Item 1 for v1; a full-text version only with the human-capital subsection stripped |
| D4 | Network formation | Adopted (27 Sep): monthly-updated networks (latest 10-K available by month-end, ≤ 15 months old) as primary; the annual July–June schedule only for the TNIC-3 head-to-head |
| D8 | Exclude SPACs (blank-check shells) from the universe? | Yes (27 Sep): per-filing flag, SIC ∈ {6770, 6799} plus blank-check language in Item 1 (§3). Justified on economics before any return test |
| D9 | Correct the length bias of bag-of-words similarity? | Yes (27 Sep): degree-corrected similarity for peer selection, multiplicative $s_{ij}/(m_i m_j)$ vs additive, chosen on Element A diagnostics only; raw BoW kept as robustness (§5) |
| D10 | Re-download all filings to fix mis-cut Item 1 spans? | Yes (27 Sep): one pass with raw HTML stored, v1 and v2 compared, rule validated on ~100 hand-checked disagreements, then the text layer is frozen (§4) |

## 14. References {#references}

✅ = checked against the primary source in the research pass.

**Text and cross-firm predictability.** Hoberg & Phillips (2010), RFS 23(10):3773–3811 ✅ (WP). Hoberg & Phillips (2016), JPE 124(5):1423–1465 ✅ (NBER w15991: 25% cutoff, 21.32% threshold, 2.05% density). Hoberg & Phillips (2018), JFQA 53(6):2355–2388 ✅ (Tables 3A, 7, 8, 10, 11). Hoberg–Phillips data library readmes (TNIC-3, ETNIC) ✅. Cohen & Frazzini (2008), JF 63(4):1977–2011 ✅. Moskowitz & Grinblatt (1999), JF 54(4):1249–1290 ✅. Menzly & Ozbas (2010), JF 65(4):1555–1580 ✅ (abstract). Lee, Sun, Wang & Zhang (2019), JFE 132(3):76–96 ✅ (abstract). Ali & Hirshleifer (2020), JFE 136(3):649–675 ✅. McLean & Pontiff (2016), JF 71(1):5–32 ✅. Antón & Polk (2014), JF 69(3):1099–1127 ✅. Vamvourellis et al. (2023), arXiv 2308.08031 ✅. Glasserman & Lin (2023), arXiv 2309.17322 ✅. He, Lv, Manela & Wu (2025), arXiv 2502.21206 ✅.

**RMT and covariance.** Marčenko & Pastur (1967) ✅. Laloux, Cizeau, Bouchaud & Potters (1999), PRL 83:1467 ✅. Plerou et al. (1999), PRL 83:1471 ✅; (2002), PRE 65:066126 ✅. Bun, Bouchaud & Potters (2017), Physics Reports 666:1–109 ✅. Ledoit & Wolf (2003) JEF 10:603–621 ✅; (2004) JMVA 88:365–411 ✅; (2004) JPM 30:110–119 ✅ (WP); (2011) Wilmott ✅; (2017) RFS 30:4349–4388 ✅; (2020) AoS 48(5):3043–3065 ✅. Schäfer & Strimmer (2005), SAGMB 4(1) ✅. Engle, Ledoit & Wolf (2019), JBES 37(2):363–375 ✅. Jagannathan & Ma (2003), JF 58(4) ✅. DeMiguel, Garlappi & Uppal (2009), RFS 22(5) ✅. Higham (2002), IMA JNA 22(3) ✅. Lu, Ndiaye & Simaan (2024), IRFA 96(A):103572 ✅ (abstract only; method ⚠️).

**Inference.** Fama & MacBeth (1973), JPE 81(3) (formula ⚠️ verbatim). Newey & West (1987; 1994) ✅. Petersen (2009), RFS 22(1) ✅. Lazarus, Lewis, Stock & Watson (2018), JBES 36(4) ✅. Krackhardt (1988) ✅. Dekker, Krackhardt & Snijders (2007), Psychometrika 72(4) ✅. Aronow, Samii & Assenova (2015), Political Analysis 23(4) ✅. Cameron & Miller (2014) WP ✅. Harvey, Liu & Zhu (2016), RFS 29(1) ✅. Harvey (2017), JF 72(4) ✅. Hou, Xue & Zhang (2020), RFS 33(5) ✅. Britten-Jones, Neuberger & Nolte (2011) ✅. Shanken (1992) ✅.

**Data and rules.** CRSP CIZ Flat File Guide 2.0 (Jul 2026) ✅; CRSP share-code crosswalk ✅; CCM Guide ✅; 17 CFR 232.13 ✅; Form 10-K General Instructions ✅; 17 CFR 229.101 ✅; SEC Release 33-10825 ✅; SEC EDGAR access and privacy pages ✅; WRDS Terms of Use and AI Policy ✅; Shumway & Warther (1999), JF 54(6) ✅; Schwarz, Walter & Weiss (2026), JFQA ✅ (abstract); Loukas et al. (2021) EDGAR-CORPUS ✅.
