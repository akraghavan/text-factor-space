# Pre-registration

> **DRAFT, NOT FROZEN (drafted 27 Sep 2026 by the local Claude Code session for Abhi's review; freeze target Thu 1 Oct).**
> Nothing below binds yet. Items marked **[PROPOSED]** are choices the SPEC leaves open; each needs Abhi's yes/no before the freeze. Items marked **[OPEN]** must be resolved before the freeze. Remove this box when freezing.

**Frozen at commit:** `TODO (full commit hash)` on `TODO (date, ET)`
**Text layer:** git tag `text-layer-v1` = commit `34d722ce383e5e55c0cb01099e542818c11e78f8` (27 Sep 2026). No extractor, vocabulary, masking or SPAC-rule change after it.

Protocol (SPEC §10): freeze this file before running any confirmatory test (H1–H3) and before looking at any test-period result in Element D or E. After the freeze the primary specifications below do not change; every other specification, variant or subsample is reported as **exploratory**, counted in the log at the bottom, and corrected across with Benjamini–Hochberg (q = 0.10; Benjamini–Yekutieli as a check). Changes after the freeze go in the change log, never in place.

**What has been looked at before this draft (disclosure).** Only text-side diagnostics: Element A (similarity distributions, same-SIC-3 AUC, TNIC-3 agreement, neighbour spot checks, length correlations; `analysis/output/a_text_layer/`) and data-coverage counts (universe sizes, book-to-market and momentum coverage in `src/formation.py`). No return outcome (residual correlations, future returns, portfolio variances) has been computed. D8 (SPAC exclusion) and D11 (BoW correction) were chosen on text diagnostics and filing-date names only.

## Common to all elements

- **Sample period and data.** CRSP CIZ monthly 2009-01 → 2026-06, daily 2010-01-04 → 2026-03-31; Fama–French 5 factors + momentum (daily and monthly) to 2026-08; 10-K filings Jun 2011 → Sep 2026. Formation months (D4, monthly): **Jul 2012 → Mar 2026** (165) for B, C and D (daily data needed after formation); **Jul 2012 → Jun 2026** for E (monthly returns).
- **Universe at formation month t** (SPEC §3; `src/universe.py`, `src/formation.py:universe_at`). CRSP rows of month t−1 with `ShareType = NS`, `SecurityType = EQTY`, `SecuritySubType = COM`, `USIncFlg = Y`, `IssuerType ∈ {ACOR, CORP}`, `ConditionalType ∈ {RW, NW}`, `PrimaryExch ∈ {N, A, Q}`; SPAC firm-months excluded (D8: Item 1 says "we are / is a blank check company" in its first 500 words or "initial business combination" ≥ 3 times in its first 2,000 words); one PERMNO per PERMCO (largest market cap at t−1); a text vintage: the latest linked 10-K filed before the first day of t and at most 15 months earlier, with ≥ 100 words of Item 1. Size = CRSP market cap at the end of t−1, in dollars.
- **Point in time.** A 10-K is usable from the first trading day after its filing date (implemented as filed before the first calendar day of the formation month). Book equity (Davis–Fama–French: SEQ, else CEQ + PSTK, else AT − LT; plus TXDITC; minus PSTKRV, else PSTKL, else PSTK) for fiscal years ending in calendar year y−1 is used from July y over December y−1 market equity summed by PERMCO. BoW vocabulary: linked filings in [t − 365 days, t).
- **Industry codes. [PROPOSED]** Historical CRSP `siccd` of month t−1 (point in time, monthly) for all SIC-based controls and for the density π, as implemented. SPEC §3's table names Compustat `sich`; proposal: CRSP `siccd` primary, Compustat `sich` as robustness. Abhi to confirm and the SPEC table to be aligned.
- **Delisting returns. [OPEN]** CIZ `MthRet` already includes delisting returns where CRSP has them. SPEC §3's imputation (δ = −30% NYSE/AMEX, −55% Nasdaq when the delisting return is missing) needs `MthDelFlg` / delisting codes, which the current monthly pull does not contain. Options: (a) one WRDS query for the CIZ delisting fields (within the cap) and apply SPEC §3 with sensitivity δ ∈ {0, −30%, −100%}; (b) register CIZ `MthRet` as is and report the count of missing delisting returns as a limitation. Needed for E only (C and D use daily data).
- **Text representations** (text layer v1; `src/networks.py`, the single builder for B, C, D and E):
  - **Dense:** bge-small-en-v1.5 embeddings of the first 2 × 500 tokens of Item 1 (D3), the filer's own name and ticker masked (`src/mask_names.py`), averaged and unit-normalised; centred on the formation cross-section mean and renormalised; s = cosine.
  - **BoW:** binary noun and proper-noun vectors (WordNet nouns; proper noun = Title-case in ≥ 90% of occurrences in the window), stop words and geographic terms removed, words in ≥ 5 and ≤ 25% of the window's filings, unit-normalised; s = cosine, then the D11 correction s̃ = s − m_i m_j / median(m), m_i = firm i's median similarity to the other firms at t (`bow.degree_correct(S, 'null')`).
  - **Primary by hypothesis (D2):** H1 (Element C) and H2 (Element D) use the dense network; H3 (Element E) uses BoW (null-corrected). Raw BoW, BoW all-words and TNIC-3 are robustness networks.
- **Peer sets and density (SPEC §5).** π_t = share of firm pairs at t with the same historical SIC-3 (pairs with a missing SIC excluded). Each network is cut at its (1 − π_t) quantile of s over i < j; peers of i are {j : s_ij > τ_t}, excluding i and same-PERMCO firms. Monthly updated (D4); TNIC-3 only in its annual July–June head-to-head (year Y used from July Y+1).

## Element A — Text representations (SPEC §5)

Completed before this draft; descriptive, no hypothesis test. Recorded here so the text layer is fixed.

- **Primary specification:** the networks above, annual 1 July formations 2012–2026, SPAC months excluded (`analysis/a_text_layer.py`).
- **Single primary statistic:** same-SIC-3 AUC of the primary network, averaged over formations. Realised on text-layer-v1: dense 0.882, BoW null-corrected 0.905 (raw BoW nouns 0.882); TNIC-3 edge Jaccard at matched density 0.361 (dense), 0.647 (BoW null), 0.277 (SIC-3 itself).
- **Decision rule:** a network is usable if its AUC exceeds 0.8 and its peers are not a relabelling of SIC-3 (share of edges crossing SIC-3 > 50%). Both primary networks pass (edges crossing SIC-3: 66% dense, 57% BoW null).

## Element B — Residual factor space and its spectrum (SPEC §6)

Descriptive element; not in the confirmatory family.

- **Primary specification. [PROPOSED]** Annual formations at the end of June, 2013–2025 (13 cross-sections; the first 756-day window starts in Jan 2010). N = the 500 largest universe firms at t−1 with complete daily returns over the window; of any pair with return correlation > 0.95, drop the one with the higher Amihud illiquidity. Window **T = 756** trading days ending on the last trading day before t (primary; T = 1,008 as robustness). Each stock's daily excess returns are regressed on FF5 + momentum over the same window with `tfs_stats.regression.ols_qr`; residuals are standardised; C = ZᵀZ/T; q = N/(T − 7). Noise edge: the empirical edge (95th percentile of the top eigenvalue over 200 independent circular shifts of each series) is primary; the iterated Marchenko–Pastur edge σ² = 1 − Σ_{λ_k > λ₊} λ_k/N is reported beside it.
- **Single primary statistic. [PROPOSED]** For each residual mode k above the empirical edge, the beyond-industry alignment A_k = u_kᵀ G̃ u_k, with G̃ the dense similarity matrix residualised on SIC-3 co-membership (zero diagonal), and its p-value from 1,000 joint row/column relabellings of firms. Statistic: the share of above-edge modes, pooled over the 13 formations, with p < 0.05.
- **Decision rule. [PROPOSED]** "Residual modes carry text structure beyond industry" if that share exceeds 5% with a one-sided binomial p < 0.05. Reported beside it: the same share with the SIC-3 matrix and with the raw dense matrix; IPR per mode; subspace overlap with the top-K text eigenvectors against the K/N benchmark.

## Element C — Pairwise comovement beyond industry codes (SPEC §7) — confirmatory H1

- **Primary specification.** Each formation month t, Jul 2012 → Mar 2026 (T = 165): the 1,000 largest universe firms at t−1; pairs i < j (499,500 per month).
  - Outcome z_ij,t = atanh of the correlation of daily FF6 residuals within month t, residuals from betas estimated with `tfs_stats.regression.ols_qr` on the 252 trading days ending the day before t; a firm enters month t if it has ≥ 200 of those 252 returns **[PROPOSED]** and ≥ 15 residual days in t.
  - Regression each month: z_ij,t = a_t + b_t s̃_ij + φ_t z^lag_ij + Σ_{ℓ=1..4} c_ℓt 1[same SIC-ℓ] + d_tᵀ w_ij + u_ij,t.
  - s̃ = the **dense** similarity (D2), standardised within month.
  - z^lag = Fisher z of the pair's residual correlation over the 12 months before t (same residual construction, month by month, pooled).
  - w_ij = Antón–Polk percentile-rank distances in size, book-to-market and momentum R(t−12, t−2); |Δβ̂_k| for each of the six factors; the rank distance in log daily Amihud illiquidity over the 12 months before t (D12; zero-volume days skipped; the monthly proxy is used only if the daily files are unavailable); same fiscal-year-end month; log length sum and |log length difference|; same primary exchange (`src/formation.py:pair_frame`).
  - b̄ = (1/T) Σ_t b_t, estimated from monthly sufficient statistics.
- **Single primary statistic.** b̄ with its Newey–West t-statistic, L = ⌊4(T/100)^{2/9}⌋ = 4 (Fama–MacBeth via `tfs_stats.regression.fama_macbeth`). Reported beside it: EWC with ν = ⌊0.4 T^{2/3}⌋ = 12 and t₁₂ critical values; the autocorrelation of b_t; MRQAP-DSP (999 relabellings, annual July–June cross-sections); pooled OLS with dyadic-robust errors.
- **Decision rule (H1).** H1: b̄ > 0. One-sided p from the NW t-statistic; H1 is supported if p is below its Holm threshold within the confirmatory family (below). A positive b̄ that fails Holm is reported with its confidence interval, not as "no effect".
- **Robustness (exploratory, pre-listed):** BoW null and raw BoW in place of dense; density-matched binary text network in place of the continuous s̃; FF6 plus 5 and 10 principal components; 12-month non-overlapping windows; pre/post FY2020 (Item 101 change); Dimson-lagged residuals.

## Element D — Covariance horse race (SPEC §8) — confirmatory H2 (stretch; may be deferred)

- **Primary specification. [PROPOSED where noted]** N = 500 largest universe firms at each rebalance with a complete past window; estimation window T = 252 trading days (D5); rebalance every 21 trading days. Development period Jul 2012 – Nov 2018, **test period Dec 2018 – Mar 2026 [PROPOSED: same split as E]**. Variance model Σ̂ = D̂^{1/2} R̂ D̂^{1/2}. The text estimator is the nested target T(a, b) = a11ᵀ + bG + (1 − a − b)I with G from the **dense** network **[PROPOSED; D2 names dense for second moments]**; (a, b) fitted by constrained least squares of off-diagonal residual correlations on g_ij over the window ending before the estimation window; intensity by the Schäfer–Strimmer analytic formula (primary), 63-day validated intensity as robustness. Benchmark: LW analytical nonlinear shrinkage (#7). Unconstrained GMV weights by a linear solve; a delisted position earns the risk-free rate.
- **Single primary statistic.** Δ = log σ̂²_text − log σ̂²_LW-NL of out-of-sample daily GMV returns over the test period, with the prewhitened HAC standard error (Ledoit & Wolf 2011).
- **Decision rule (H2).** H2: Δ < 0. One-sided p from the HAC test within the confirmatory family; studentised circular block bootstrap reported beside it. If Element D is not complete by the freeze, H2 is dropped before the freeze and the family has two tests.

## Element E — Text-peer momentum, out of sample (SPEC §9) — confirmatory H3

- **Primary specification.**
  - Monthly formation t, peers from the **BoW null-corrected** network (D2, D11) at density π_t, excluding i and same-PERMCO firms.
  - PEERMOM_i,t = equal-weighted mean over peers of each peer's compounded return R_j(t−12, t−1).
  - Sample: universe firms at t−1 with price ≥ $1 at t−1 and at least one peer.
  - Fama–MacBeth of the excess return in month t on PEERMOM and controls, all right-hand variables winsorised at 1/99 and z-scored each month. Controls: log ME, log B/M, own r_{t−1}, own R(t−12, t−2), value-weighted FF-48 industry momentum R(t−12, t−1), SIC-3 peer momentum (equal-weighted, same construction), and TNIC-3 peer momentum. **[PROPOSED]** TNIC-3 ends with FY2023, used through June 2025; for July 2025 – June 2026 the FY2023 network is carried forward and flagged.
  - **Test period Dec 2018 – Jun 2026 (T = 91)**; development period Jul 2012 – Nov 2018 (T = 77) is where the specification was fixed.
- **Single primary statistic.** The test-period FM mean slope on PEERMOM with a Newey–West t-statistic, L = ⌊4(91/100)^{2/9}⌋ = 3. **[PROPOSED]** SPEC §9 quotes NW(4) and EWC(12), which are the formula values at T ≈ 165; at T = 91 the same formulas give L = 3 and ν = 8. Reported beside it: NW(2) for comparability with HP, EWC(8) with t₈ critical values, the Harvey–Liu–Zhu t > 3 hurdle, the pre/post difference against the development period, and the full-sample slope.
- **Decision rule (H3).** H3: slope > 0. One-sided p within the confirmatory family. The power analysis (SPEC §9: t ≈ 1.3 at a McLean–Pontiff-decayed slope, 2.2 at HP's 2008–12 controlled slope) is part of this registration: a non-significant test-period slope is reported with its confidence interval and is not read as evidence that the effect is gone.
- **Pre-listed exploratory:** similarity-weighted peers; horizon splits (t−6..t−1 vs t−12..t−7; Grundy–Martin; t−24..t−13 placebo); idiosyncratic peer returns; visibility splits (TEXT-only, SIC-only, both, DENSE-only); quintile and decile portfolios with FF3, FF3+UMD, FF5+UMD, +STR alphas (NYSE breakpoints, EW/VW, price ≥ $1 and ≥ $5); permutation nulls (stratified substitution, matched random peers, stale y−3 network); the HP replication with TNIC-3 on the common sample; the post-Sep-2023 subsample for the encoder.

## Confirmatory family and multiple testing (SPEC §10.2)

- Family: {H1, H3} plus H2 if Element D is complete at the freeze. Holm at 5%: with three tests, thresholds 0.0167, 0.025, 0.05; with two, 0.025, 0.05. All one-sided, direction as stated.
- H3 is also reported against the Harvey–Liu–Zhu t > 3 hurdle.
- Everything else is exploratory: Benjamini–Hochberg at q = 0.10 across the exploratory log, Benjamini–Yekutieli as a check, Romano–Wolf stepdown (block bootstrap of months) across FM slope series.

## Flags raised while building (28 Sep; for review, nothing below changes a specification)

1. **B formations start in 2014, not 2013.** Rolling out-of-sample residuals (betas re-estimated monthly on the prior 252 days, SPEC §6.2) exist from January 2011 (daily data start January 2010), so the first complete 756-day residual window ends June 2014: 12 formations, 2014–2025.
2. **B residual construction: this draft said "regressed … over the same window"; SPEC §6.2 says rolling betas.** The code follows SPEC (the out-of-sample residual panel in `src/c_panel.py`), and then q = N/T (no in-window degrees of freedom are used). The B paragraph above should be reworded to rolling betas at the freeze.
3. **C: pairs with a missing B/M are ~10% of pairs** (negative or missing book equity, no Compustat link); under the draft they drop out of the monthly regression. Option: keep them with a missing-B/M indicator and rank distance set to the median.
4. **C: z_lag requires ≥ 126 common residual days** over the prior 12 months (a design choice made in code, not yet stated above).
5. **E: a peer's R(t−12, t−1) requires ≥ 8 of 12 monthly returns** (same rule as own momentum); not yet stated above.
6. **E: about a quarter of universe firms have no text peer at SIC-3 density** (null-corrected BoW: 22.6% in Jul 2013, 25.0% in Jul 2016; raw BoW 30–34%; median degree 4–5, mean ~70, degree correlates +0.4–0.5 with Item 1 length). The "≥ 1 peer" filter (as in HP) drops them from E. A per-firm top-k peer set would keep them but is a different network definition; decide before the freeze whether to add it as a pre-listed exploratory variant (not primary).

## Before the freeze (checklist)

- [ ] Abhi decides every [PROPOSED] item; [OPEN] delisting returns resolved.
- [x] `tfs_stats` on standard libraries (D13) with tests green: 30 pass (28 Sep).
- [x] D12 daily price/volume converted and merged; daily Amihud coverage 99.8% of C's top 1,000 (27 Sep).
- [ ] `specs.yaml` registry and the runner that rejects unregistered specs and appends to `runs.log` (SPEC §10.1).
- [ ] SPEC §3 industry-code row aligned with the choice above.
- [ ] Record the freeze commit hash and date above; remove the DRAFT box.

## Exploratory specifications run

Count and list here as they are run (SPEC §10.3).

- None yet.

## Change log (after freeze only)

- None yet.
