# Pre-registration

**Frozen at commit:** `d1df5c795b83d7e1f3d04a23a31fe0174b6aa047` on 2026-09-30, 20:03 ET (Abhi's go)
The hash is the commit whose PREREG.md and specs.yaml are frozen; the freeze commit itself only records it, removes the draft box and ticks the checklist. `src/runner.py` checks every confirmatory and primary spec against specs.yaml at this hash.
**Text layer:** git tag `text-layer-v1` = commit `34d722ce383e5e55c0cb01099e542818c11e78f8` (27 Sep 2026). No extractor, vocabulary, masking or SPAC-rule change after it.

Protocol (SPEC §10): every reported statistic is a registered spec in `specs.yaml`, executed only through `src/runner.py` and logged in `runs.log`; the Benjamini–Hochberg count comes from that log (`python src/runner.py count`). Freeze this file before running any confirmatory test (H1, H3) and before looking at any test-period result in Element D or E. After the freeze the primary specifications below do not change; every other specification, variant or subsample is reported as **exploratory**, counted in the log at the bottom, and corrected across with Benjamini–Hochberg (q = 0.10; Benjamini–Yekutieli as a check). Changes after the freeze go in the change log, never in place.

**What has been looked at before the freeze (disclosure).** Text-side diagnostics: Element A (similarity distributions, same-SIC-3 AUC, TNIC-3 agreement, neighbour spot checks, length correlations; `analysis/output/a_text_layer/`) and data-coverage counts. Since 28 Sep, construction checks that touch returns but none of the primary statistics: C's outcome and controls on three months (distribution of within-month residual correlations, same-SIC-3 vs other pairs, correlation with z_lag, coverage; no association between the outcome and text similarity; `analysis/output/c_panel/`); B's raw and residual spectra and noise edges (no text alignment; `analysis/output/b_spectra/`); and E on the development period only, Jul 2012 – Nov 2018, with CRSP truncated at Nov 2018 before any computation (`analysis/output/e_dev/`), which this protocol allows for tuning. Not computed: C's b̄ or any z–text statistic, B's alignment share, any E test-period return, any D portfolio variance. D8 (SPAC exclusion) and D11 (BoW correction) were chosen on text diagnostics and filing-date names only.

## Common to all elements

- **Sample period and data.** CRSP CIZ monthly 2009-01 → 2026-06, daily 2010-01-04 → 2026-03-31; Fama–French 5 factors + momentum (daily and monthly) to 2026-08; 10-K filings Jun 2011 → Sep 2026. Formation months (D4, monthly): **Jul 2012 → Mar 2026** (165) for C and D (daily data needed after formation); **Jul 2012 → Jun 2026** for E (monthly returns). B uses annual formations (below).
- **Universe at formation month t** (SPEC §3; `src/universe.py`, `src/formation.py:universe_at`). CRSP rows of month t−1 with `ShareType = NS`, `SecurityType = EQTY`, `SecuritySubType = COM`, `USIncFlg = Y`, `IssuerType ∈ {ACOR, CORP}`, `ConditionalType ∈ {RW, NW}`, `PrimaryExch ∈ {N, A, Q}`; SPAC firm-months excluded (D8: Item 1 says "we are / is a blank check company" in its first 500 words or "initial business combination" ≥ 3 times in its first 2,000 words); one PERMNO per PERMCO (largest market cap at t−1); a text vintage: the latest linked 10-K filed before the first day of t and at most 15 months earlier, with ≥ 100 words of Item 1. Size = CRSP market cap at the end of t−1, in dollars. Membership is fixed at formation (SPEC §3): a firm formed at t−1 keeps its month-t return even if it leaves the universe in t (exit months, mostly delisting months, kept with `in_universe = False`).
- **Point in time.** A 10-K is usable from the first trading day after its filing date (implemented as filed before the first calendar day of the formation month). Book equity (Davis–Fama–French: SEQ, else CEQ + PSTK, else AT − LT; plus TXDITC; minus PSTKRV, else PSTKL, else PSTK) for fiscal years ending in calendar year y−1 is used from July y over December y−1 market equity summed by PERMCO. BoW vocabulary: linked filings in [t − 365 days, t).
- **Industry codes (D14).** Historical CRSP `siccd` of month t−1 (point in time, monthly) for all SIC-based controls and for the density π. Compustat historical `sich` is the robustness version.
- **Delisting returns (D14: option a).** CIZ `MthRet` includes delisting returns where CRSP has them. The CIZ delisting fields come from one WRDS query (logged in `docs/WRDS_QUERIES.md`); in the delisting month of a performance-related delisting (CIZ `DelActionType` = GDR: dropped by the exchange) whose delisting return is missing, E's monthly return is imputed per SPEC §3 as (1 + MthRet)(1 + δ) − 1, δ = −30% (NYSE/AMEX) or −55% (Nasdaq). A delisting return already present is inside CIZ `MthRet` and is not added again. Missing delisting returns on other delistings (GLI, MER, GEX) are left as CRSP has them and counted (7 E firm-months). Pre-listed sensitivity: δ ∈ {0, −30%, −100%}; the count of imputed firm-months is reported. Needed for E only (C and D use daily data).
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

- **Primary specification (D14).** Annual formations at 1 July, **2014–2025 (12 cross-sections)**: the rolling-beta residuals below exist from January 2011, so the first complete 756-day window ends in June 2014. N = the 500 largest universe firms at t−1 with complete daily returns and complete residuals over the window; of any pair with raw return correlation > 0.95, drop the one with the higher log daily Amihud illiquidity. Window **T = 756** trading days ending on the last trading day before t (primary; T = 1,008 as robustness). Residuals come from the **rolling-beta panel** (SPEC §6.2; `src/c_panel.py`): each month's daily excess returns minus the fit of betas estimated with `tfs_stats.regression.ols_qr` on FF5 + momentum over the 252 trading days before that month (≥ 200 returns), so no beta uses the days it residualises. Residuals are standardised; C = ZᵀZ/T; because no degrees of freedom are used inside the window, **q = N/T**. Noise edge: the empirical edge (95th percentile of the top eigenvalue over 200 independent circular shifts of each series; `tfs_stats.rmt.circular_shift_edge`) is primary; the Marchenko–Pastur edge with σ² = 1 and the iterated σ² (`tfs_stats.rmt.mp_sigma2_iterated`) are reported beside it.
- **Single primary statistic (D14).** For each residual mode k above the empirical edge, the beyond-industry alignment A_k = u_kᵀ G̃ u_k, with G̃ the dense similarity matrix residualised on SIC-3 co-membership (zero diagonal), and its p-value from 1,000 joint row/column relabellings of firms. Statistic: the share of above-edge modes, pooled over the 12 formations, with p < 0.05.
- **Decision rule (D14).** "Residual modes carry text structure beyond industry" if that share exceeds 5% with a one-sided binomial p < 0.05. Reported beside it: the same share with the SIC-3 matrix and with the raw dense matrix; IPR per mode; subspace overlap with the top-K text eigenvectors against the K/N benchmark.

## Element C — Pairwise comovement beyond industry codes (SPEC §7) — confirmatory H1

- **Primary specification.** Each formation month t, Jul 2012 → Mar 2026 (T = 165): the 1,000 largest universe firms at t−1; pairs i < j (499,500 per month).
  - Outcome z_ij,t = atanh of the correlation of daily FF6 residuals within month t, residuals from betas estimated with `tfs_stats.regression.ols_qr` on the 252 trading days ending the day before t; a firm enters month t if it has ≥ 200 of those 252 returns and ≥ 15 residual days in t (D14); the pair correlation uses the days both firms have.
  - Regression each month: z_ij,t = a_t + b_t s̃_ij + φ_t z^lag_ij + Σ_{ℓ=1..4} c_ℓt 1[same SIC-ℓ] + d_tᵀ w_ij + u_ij,t.
  - s̃ = the **dense** similarity (D2), standardised within month.
  - z^lag = Fisher z of the pair's residual correlation over the 12 months before t (same residual construction, month by month, pooled); it needs ≥ 126 common residual days (D14).
  - w_ij = Antón–Polk percentile-rank distances in size, book-to-market and momentum R(t−12, t−2); |Δβ̂_k| for each of the six factors; the rank distance in log daily Amihud illiquidity over the 12 months before t (D12; zero-volume days skipped; the monthly proxy is used only if the daily files are unavailable); same fiscal-year-end month; log length sum and |log length difference|; same primary exchange (`src/formation.py:pair_frame`).
  - Pairs with a missing value in any regressor are dropped from that month's regression (D14; missing B/M is the main case, about 10% of pairs).
  - b̄ = (1/T) Σ_t b_t, estimated from monthly sufficient statistics (`tfs_stats.regression.fm_from_moments`).
- **Single primary statistic.** b̄ with its Newey–West t-statistic, L = ⌊4(T/100)^{2/9}⌋ = 4 (Fama–MacBeth via `tfs_stats.regression.fama_macbeth`). Reported beside it: EWC with ν = ⌊0.4 T^{2/3}⌋ = 12 and t₁₂ critical values; the autocorrelation of b_t; MRQAP-DSP (999 relabellings, annual July–June cross-sections); pooled OLS with dyadic-robust errors.
- **Decision rule (H1).** H1: b̄ > 0. One-sided p from the NW t-statistic; H1 is supported if p is below its Holm threshold within the confirmatory family (below). A positive b̄ that fails Holm is reported with its confidence interval, not as "no effect".
- **Robustness (exploratory, pre-listed):** pairs with missing B/M kept, with a missing-B/M indicator and the B/M rank distance set to the month's median (D14); BoW null and raw BoW in place of dense; density-matched binary text network in place of the continuous s̃; FF6 plus 5 and 10 principal components; 12-month non-overlapping windows; pre/post FY2020 (Item 101 change); Dimson-lagged residuals.

## Element D — Covariance horse race (SPEC §8) — exploratory (deferred; H2 left the confirmatory family, D14)

- **Specification if D is built (D14).** N = 500 largest universe firms at each rebalance with a complete past window; estimation window T = 252 trading days (D5); rebalance every 21 trading days. Development period Jul 2012 – Nov 2018, **test period Dec 2018 – Mar 2026** (the same split as E). Variance model Σ̂ = D̂^{1/2} R̂ D̂^{1/2}. The text estimator is the nested target T(a, b) = a11ᵀ + bG + (1 − a − b)I with G from the **dense** network (D2 names dense for second moments); (a, b) fitted by constrained least squares of off-diagonal residual correlations on g_ij over the window ending before the estimation window; intensity by the Schäfer–Strimmer analytic formula (primary), 63-day validated intensity as robustness. Benchmark: LW analytical nonlinear shrinkage (#7). Unconstrained GMV weights by a linear solve; a delisted position earns the risk-free rate.
- **Single primary statistic.** Δ = log σ̂²_text − log σ̂²_LW-NL of out-of-sample daily GMV returns over the test period, with the prewhitened HAC standard error (Ledoit & Wolf 2011).
- **Decision rule.** Δ < 0, one-sided p from the HAC test, studentised circular block bootstrap beside it. D will not be built before the freeze, so H2 is **not** in the confirmatory family (D14); if D is built later, its result is reported as exploratory.

## Element E — Text-peer momentum, out of sample (SPEC §9) — confirmatory H3

- **Primary specification.**
  - Monthly formation t, peers from the **BoW null-corrected** network (D2, D11) at density π_t, excluding i and same-PERMCO firms.
  - PEERMOM_i,t = equal-weighted mean over peers of each peer's compounded return R_j(t−12, t−1); a peer's R_j(t−12, t−1) needs ≥ 8 of the 12 monthly returns, otherwise that peer is left out of the average (D14).
  - Sample: universe firms at t−1 with price ≥ $1 at t−1 and at least one peer (as HP; about a quarter of universe firms have no text peer at SIC-3 density and are outside E's primary sample, D14).
  - Fama–MacBeth of the excess return in month t on PEERMOM and controls, all right-hand variables winsorised at 1/99 and z-scored each month. Controls: log ME, log B/M, own r_{t−1}, own R(t−12, t−2), value-weighted FF-48 industry momentum R(t−12, t−1), SIC-3 peer momentum (equal-weighted, same construction), and TNIC-3 peer momentum. TNIC-3 ends with FY2023, used through June 2025; for July 2025 – June 2026 the FY2023 network is carried forward and flagged in the results (D14).
  - **Test period Dec 2018 – Jun 2026 (T = 91)**; development period Jul 2012 – Nov 2018 (T = 77) is where the specification was fixed.
- **Single primary statistic.** The test-period FM mean slope on PEERMOM with a Newey–West t-statistic, L = ⌊4(91/100)^{2/9}⌋ = 3 (D14; SPEC §9's NW(4) and EWC(12) are the same formulas at T ≈ 165). Reported beside it: NW(2) for comparability with HP, EWC(8) with t₈ critical values, the Harvey–Liu–Zhu t > 3 hurdle, the pre/post difference against the development period, and the full-sample slope.
- **Decision rule (H3).** H3: slope > 0. One-sided p within the confirmatory family. The power analysis (SPEC §9: t ≈ 1.3 at a McLean–Pontiff-decayed slope, 2.2 at HP's 2008–12 controlled slope) is part of this registration: a non-significant test-period slope is reported with its confidence interval and is not read as evidence that the effect is gone.
- **Pre-listed exploratory:** a nearest-5 peer set (each firm's 5 most similar firms on the same BoW null-corrected similarity, so firms without a peer at SIC-3 density are included; D14); delisting sensitivity δ ∈ {0, −30%, −100%}; similarity-weighted peers; horizon splits (t−6..t−1 vs t−12..t−7; Grundy–Martin; t−24..t−13 placebo); idiosyncratic peer returns; visibility splits (TEXT-only, SIC-only, both, DENSE-only); quintile and decile portfolios with FF3, FF3+UMD, FF5+UMD, +STR alphas (NYSE breakpoints, EW/VW, price ≥ $1 and ≥ $5); permutation nulls (stratified substitution, matched random peers, stale y−3 network); the HP replication with TNIC-3 on the common sample; the post-Sep-2023 subsample for the encoder.

## Confirmatory family and multiple testing (SPEC §10.2)

- Family: **{H1, H3}** (D14: D is not built before the freeze, so H2 is out). Holm at 5%: thresholds 0.025 for the smaller p-value and 0.05 for the larger. Both one-sided, direction as stated.
- H3 is also reported against the Harvey–Liu–Zhu t > 3 hurdle.
- Everything else is exploratory: Benjamini–Hochberg at q = 0.10 across the exploratory log, Benjamini–Yekutieli as a check, Romano–Wolf stepdown (block bootstrap of months) across FM slope series.

## Resolved 29 Sep (D14)

The delisting-returns question (option a), every item previously marked [PROPOSED] and the six flags raised on 28 Sep were accepted as recommended (Abhi, 29 Sep; SPEC §13, D14). They are written into the specifications above: B's 2014 start, rolling-beta residuals and q = N/T; C's ≥ 200/252 and ≥ 15-day entry rules, z_lag's ≥ 126 common days and dropping missing-B/M pairs (kept as robustness); E's ≥ 8/12 peer-return rule, the ≥ 1-peer filter with a nearest-5 exploratory variant, the TNIC carry-forward and NW(3)/EWC(8) at T = 91; CRSP `siccd` as primary industry codes; D out of the confirmatory family.

## Before the freeze (checklist)

- [x] Abhi decides every [PROPOSED] item; [OPEN] delisting returns resolved (D14, 29 Sep).
- [x] `tfs_stats` on standard libraries (D13) with tests green: 30 pass (28 Sep).
- [x] D12 daily price/volume converted and merged; daily Amihud coverage 99.8% of C's top 1,000 (27 Sep).
- [x] `specs.yaml` registry (45 specs: 2 confirmatory, 1 primary, 38 exploratory, 4 diagnostic) and `src/runner.py`, which rejects unregistered specs, refuses confirmatory and primary specs before the freeze or if edited after it, and appends every attempt to `runs.log` (SPEC §10.1; 29 Sep).
- [x] SPEC §3 industry-code row aligned with the choice above (29 Sep).
- [x] Delisting fields pulled from WRDS and SPEC §3's imputation implemented in E's returns (30 Sep; 13 E firm-months touched).
- [x] Record the freeze commit hash and date above; remove the DRAFT box (30 Sep 2026, 20:03 ET).

## Exploratory specifications run

Count and list here as they are run (SPEC §10.3).

**m = 44** (1–8 Oct 2026; `python src/runner.py count`): every registered exploratory spec, all through `src/runner.py`. 38 were in the frozen registry; 6 were added after the freeze (\*: 2 on 1 Oct, 4 on 8 Oct; change log below).
- **B (6):** `B_x_sic3_share`, `B_x_raw_dense_share`, `B_x_subspace_overlap`, `B_x_T1008`, `B_x_nested_sic`\*, `B_x_ff48_share`\*.
- **C (14):**
  - variants: `C_x_bow_null`, `C_x_bow_raw`, `C_x_binary_network`, `C_x_missing_bm_indicator`, `C_x_pc5`, `C_x_pc10`, `C_x_dimson`, `C_x_sich`;
  - sample splits: `C_x_12m_windows`, `C_x_pre_fy2020`, `C_x_post_fy2020`, `C_x_post_sep2023`\*;
  - inference: `C_x_mrqap`, `C_x_dyadic`.
- **D (3):** `D_x_text_vs_lwnl`, `D_x_text_vs_constcorr`\*, `D_x_text_vs_placebo`\*.
- **E (21):**
  - delisting and peer sets: `E_x_delist_0`, `E_x_delist_m100`, `E_x_nearest5`, `E_x_sim_weighted`;
  - horizons: `E_x_h_6_1`, `E_x_h_12_7`, `E_x_grundy_martin`, `E_x_placebo_24_13`, `E_x_idiosyncratic`;
  - visibility splits: `E_x_text_only`, `E_x_sic_only`, `E_x_both`, `E_x_dense_only`;
  - portfolios and replication: `E_x_portfolios`, `E_x_hp_replication`;
  - permutation nulls: `E_x_perm_matched`, `E_x_perm_stratified`, `E_x_stale_y3`;
  - subsamples and codes: `E_x_post_sep2023`, `E_x_sich`, `E_x_nyse20`\*.

**Results.**
- **BH (q = 0.10)** rejects 34 of 44; **BY** rejects 32. Not rejected: the three D tests, and E's R(t−12, t−7), Grundy–Martin peer 12–2, the t−24..t−13 placebo (two-sided), text-only, SIC-only, dense-only and the matched-peer null. BY also drops `E_x_idiosyncratic` and `E_x_nyse20`. Table: `analysis/output/exploratory/README.md`.
- **Romano–Wolf** (`Exploratory_family_romano_wolf`, studentised per D28, block 12): all 8 of C's full-period slope series survive, and 8 of E's 15 test-period series. Simulated FWER at block 12 is 14% (C) and 18% (E), so it is liberal at these sizes. The first, raw-slope run gave E 1 of 15. Output: `analysis/output/exploratory/romano_wolf.md`. Output: `analysis/output/exploratory/romano_wolf.md`.

Results are in `docs/RESULTS.md`. No registered spec remains unrun.

## Change log (after freeze only)

- 1 Oct 2026, before any registered run (46f1f40): `src/runner.py` compares each guarded spec with its frozen copy in every field except `entry`, which was frozen as `pending` because the code could only be written after the freeze; guarded runs also require a fully committed tree. No specification changed.
- 1 Oct 2026: registry addition `Confirmatory_family_holm` (diagnostic: applies the Holm rule above to the logged H1 and H3 p-values; no new test).
- 1 Oct 2026: two exploratory B specs added after the freeze (not pre-listed; counted in the exploratory BH family): `B_x_nested_sic` (dense similarity residualised on nested SIC-1..4 co-membership, the "beyond industry" version of B's share) and `B_x_ff48_share` (residualised on Fama–French 48 industry). The primary B statistic is unchanged and still reads "beyond SIC-3 co-membership".
- 1 Oct 2026: registry addition `Exploratory_family_bh` (diagnostic: applies BH at q = 0.10 and BY to the logged one-sided p-values of the exploratory specs run, m from `python src/runner.py count`; no new test).
- 8 Oct 2026, reopening (SPEC D19). The 2 Oct hard stop was lifted on 7 Oct. All 21 remaining pre-listed exploratory specs are run as registered (entries filled; no other field changed), Element D is built, and everything below is added after the freeze. No confirmatory or primary specification changes.
- 8 Oct 2026: exploratory specs added after the freeze and counted in BH (D21, D24):
  - `C_x_post_sep2023`: H1 on Oct 2023 – Mar 2026, the dense encoder's look-ahead check.
  - `E_x_nyse20`: H3 without firms below the NYSE 20th market-cap percentile.
  - `D_x_text_vs_constcorr`: dense target vs constant correlation, i.e. H0: b = 0.
  - `D_x_text_vs_placebo`: dense target vs the same target with relabelled firms.
  - BH m becomes 44.
- 8 Oct 2026: diagnostics added (no p-values in BH): `C_shape_r2`, `E_event_time`, `D_horse_race_table`, `Exploratory_family_romano_wolf`.
- 8 Oct 2026: readings of Element D where the paragraph above is silent (D20).
  - **(a, b).** The "off-diagonal residual correlations" are the off-diagonal sample correlations of daily returns over the 252 trading days before the estimation window, using pairs with ≥ 200 common days. They are fitted by least squares subject to a, b ≥ 0 and a + b ≤ 0.999.
  - **Intensity.** Schäfer–Strimmer eq. 8 on standardised returns. The constant-correlation target T(a, 0) uses the same formula, so it differs from the text target only in b.
  - **Validated intensity.** δ on a 0.05 grid, minimising GMV variance over the last 63 days of the window, with R and the target fitted on the first 189.
  - **Variance model.** Every estimator enters through Σ̂ = D̂^{1/2} R̂ D̂^{1/2}. LW nonlinear shrinkage is applied to standardised returns and renormalised to unit diagonal.
  - **Clipping.** With N > T it uses the q > 1 Marchenko–Pastur edge.
  - **Protocol.**
    - Rebalance every 21 trading days from the first trading day of July 2012.
    - Universe: the 500 largest firms at t−1 with all 252 past returns. Weights are held for 21 days, and a missing return earns the risk-free rate.
    - Out-of-sample days before 2018-12-01 are development; the rest are test.
  - **Test.** The LW (2011) delta method on (r_A, r_B, r_A², r_B²), with VAR(1)-prewhitened Quadratic-Spectral HAC and automatic bandwidth (`arch`), giving a one-sided normal p. Beside it, a studentised circular block bootstrap (block 21, 2,000 draws, seed 2026).
  - **Robustness.** N = 1,000, and T = 504.
- 8 Oct 2026: BH rule for specs with `predicted_sign: none` (only `E_x_placebo_24_13`). Such a spec has no registered direction, so it enters BH and BY with its two-sided p; the table names which p each spec used.
- 8 Oct 2026: re-runs for Romano–Wolf (D25). The nine FM specs run on 1–2 Oct are re-run once so they save their monthly slope series. Each re-run must reproduce its logged estimate and t to 1e-10, and the BH table uses the latest record.
- 8 Oct 2026, D28: implementation correction to the Romano–Wolf diagnostic (no specification changes). arch's StepM does not studentise, so each slope series is studentised by its own full-sample Newey–West SE (each spec's lags), held fixed across draws. The block length is the smallest of 4, 8, 12 with simulated FWER ≤ 6% at the family's observed autocorrelation and shape. Exploratory_family_romano_wolf is re-run.
- 8 Oct 2026, D29: exploratory spec added after the freeze, `D_x_ff6text_vs_ff6cc`, and estimator `ff6_cc` (FF6 + residual correlation shrunk to the constant-correlation target, otherwise identical to `ff6_text`). It tests whether the text target adds value in the FF6 residuals. Counted in BH: m = 45.
