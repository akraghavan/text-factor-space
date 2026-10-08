# Status

_Last updated: Thu 8 Oct 2026, early morning ET_

## Done
- Spec v1 (`docs/SPEC.md`): every element checked against primary sources by five research dossiers and a critic pass.
- SEC: bulk submissions → 61,589 10-K/10-KT indexed (Jun 2011–Sep 2026).
- WRDS pulls (Sat night): CRSP v2 monthly and daily (2010-01-04 → 2026-03-31), CCM link table, CCM Fundamentals Annual. Fama–French factors and Hoberg–Phillips TNIC-3 downloaded.
- **D0 resolved (27 Sep):** CMU's WRDS representative confirmed the AI plan is an enterprise no-training instance; scripted WRDS queries allowed under the cap in project rule 0.
- Repo scaffold: bootstrap script, project settings, CI, tests (12, skipped until implemented), DATA/PREREG docs, MIT licence.
- **Ingestion moved to the Mac (M4 Pro, 24 GB) and finished, 27 Sep:**
  - P0 `src/convert_wrds.py`: WRDS csv.gz → parquet (row counts match `docs/WRDS_QUERIES.md`), 19 s.
  - Universe fix applied (`src/universe.py`, adds IssuerType ∈ {ACOR, CORP}, ConditionalType ∈ {RW, NW}): 8,401 PERMNOs, 3,747–4,598 per year (v0 8,652; in this pull the fix only removes REITs).
  - P3 rebuilt: 54,602 of 61,589 10-Ks map (88.7%), 54,254 firm-years (v0 56,495), 3,378–4,046 per filing year 2012–2026, 6,789 PERMNOs.
  - P4 rebuilt: monthly 805,020 rows (2009-01 → 2026-06); daily 16.09M rows, 8,016 PERMNOs; FF5 + Mom daily/monthly to 2026-08.
  - P2 complete: last 15,597 filings scraped here in 34.5 min (7.6 req/s); all 61,589 have a result, 0 failed downloads.
  - P2b Item 1 v2 fallback (`src/rescue_item1.py`): v1 left 2,254 zero-word extracts, concentrated in SIC 29/10/13/49 ("Items 1 and 2" headings), not EX-13 incorporation (0/60 sampled). The line-aware v2 recovers 1,836; **99.2% of filings now > 300 words** (was 95.5%), 309 still empty. v1 vs v2 on filings where v1 works: Jaccard median 1.00; ~7% of v1 spans look wrong (truncated by a cross-reference or running into Risk Factors).
  - P5 on MPS (re-run after P2b, 21 min): 61,144 filings embedded, unit norm; **99.3% of linked firm-years** have an embedding.
  - P6 v1 (`src/bow.py`): point-in-time vocabulary (filings in [t − 365 d, t)), nouns + proper-nouns variant (WordNet + HP capitalisation rule); 61,144 × 137,961 counts, vocab 25–30k words (nouns 16–18k) per formation; pair similarities correlate 0.95–0.99 with v0 (calendar-year vocab, kept for comparison). Tests: 3 pass.
  - Market cap in dollars in the panels (`me`, `cap` = CRSP × 1000).
- **Element A validated (`analysis/a_text_layer.py`, `analysis/output/a_text_layer/`):** 1 July formations 2012–2026, 3,222–3,870 firms. Same-SIC-3 AUC: dense 0.864, BoW nouns 0.861, BoW 0.853 (0.873/0.870/0.862 excluding SIC 6799 blank-check firms). At SIC-3 density, 31–38% of text edges are same-SIC-3 pairs. TNIC-3 agreement (edge Jaccard): BoW nouns 0.616, BoW 0.606, dense 0.339, SIC-3 0.276; AUC for TNIC pairs 0.94–0.97. Same-firm year-on-year similarity median 0.90–0.93. π rises 2.1% → 3.3% (biotech growth). BoW has a strong length/hub effect (corr of log length with mean similarity +0.93); dense −0.23.

## Running
- Nothing. **No open items.** The project is complete; every registered spec has been run.

## Finished 7–8 Oct 2026 (hard stop lifted; `notes/finish_plan.md`, decisions D19–D27)
- **Phase 0 (e7dd82c).**
  - SPEC §13 D19–D27 added, plus the §1 scope line and the §12 time row.
  - PREREG change log: 8 Oct entries.
  - specs.yaml: 21 entries filled and 8 specs added (44 exploratory, 11 diagnostic, 0 pending).
  - BH rule: two-sided p for specs with no predicted sign (with a test).
  - Every FM entry saves its monthly slope series; `arch` added to the requirements.
- **Phase 1.** The nine FM specs re-run for Romano–Wolf reproduce their logged estimate and t exactly (difference 0.0).
- **Estimator layer (eec8d8f, 1a4d2e8).**
  - `tfs_stats/covariance.py`:
    - LW (2020) analytical nonlinear shrinkage, which matches the `nonlinshrink` port of the authors' code to 1e-8;
    - text, industry and constant-correlation targets;
    - Schäfer–Strimmer intensity;
    - preconditioning;
    - factor models.
  - `tfs_stats/varcompare.py`: the LW (2011) test with prewhitened QS HAC and an Andrews bandwidth, plus a block bootstrap.
  - `multitest.romano_wolf` (arch StepM) and clipping for q > 1.
  - 75 tests pass; the guide cards are in.
- **Phase 2 (B, C).** All positive and significant:
  - `B_x_T1008`: 92.8% of modes aligned.
  - C variants, b̄ 0.0078–0.0194, t 8.8–39: raw BoW, binary links, 12-month windows, pre/post FY2020, Dimson, sich, post-Sep-2023.
  - `C_shape_r2`: incremental R² 0.0018 in sample, 0.0016 out of sample.
- **Phase 3 (E).**
  - **Stratified-substitution null p = 0.001**: the text link itself carries the effect.
  - The effect sits in the peers' last month (Grundy–Martin: peer r(t−1) t 4.16; peer 12–2 t 0.73).
  - Visibility splits: only peers in both text and SIC-3 are significant.
  - `sich` gives t 5.07; above the NYSE 20th percentile, t 1.79.
  - Event time: break-even round-trip cost 2.0% of value traded; months 13–24 reverse (−10%).
- **Phase 4 (D).**
  - The dense text target **loses** to LW-NL: Δ log variance +0.251 (t 6.93; 13.89% vs 12.25% annualised SD).
  - It is slightly worse than constant correlation (+0.039, t 2.48) and than the placebo (+0.039).
  - FF6 with text-shrunk residual correlations edges LW-NL (12.12%, t −1.69, not significant after Holm).
  - The development sanity check passed (LW-NL 7.79%, text 8.70%, 1/N 13.11%).
  - The N = 500, T = 504 configuration hits LW-NL's p ≈ n degeneracy, so it is uninformative for LW-NL; this is documented.
- **Phase 5.** m = 44: BH rejects 34, BY 32. Romano–Wolf, raw slopes: C 8/8, E 1/15.
- **D28 (8 Oct, Abhi's go).** Romano–Wolf studentised by each spec's NW SE. No block reaches simulated FWER ≤ 6% (C 14%, E 18% at block 12; about 5% at T = 1,000), so block 12 is used and reported as liberal. Survivors: C 8/8, E 8/15 (every E series with t ≥ 2.24).
- **Phase 6.** Updated: RESULTS rewritten for Q1–Q3; README (mapping 88.7%, D methods, results pointer); PREREG run log; STATS_GUIDE cards (D estimators, the variance test, Romano–Wolf, the stratified null, clipping for q > 1, the BH sign rule); DATA.md (sich); project rules layout; the private PITCH (left for Abhi to review).
- **Deviations from the plan** (all in the closing the cloud session entry):
  1. arch 8.0.0's StepM does not studentise despite the flag. It is kept as D25 says, with its simulated FWER documented.
  2. The Andrews bandwidth is computed here because arch's automatic one is Newey–West (1994).
  3. LW-NL's zero-eigenvalue guard was relaxed to 1e-12 so T = 504 could run. That configuration then proved degenerate for LW-NL and is reported as such.
  4. The post-FY2020 months start in Dec 2021 rather than the Mar 2022 the plan guessed (52 months).
  5. The T = 504 configuration starts in Feb 2013, not about July 2013.
  6. LW identity now goes through `tfs_stats` (project rule 3).


## Registered results (1 Oct 2026; PREREG frozen at d1df5c7; all run through `src/runner.py`, logged in `runs.log`)
- **H1 (C, `C_H1_dense_bbar`): supported.** b̄ = 0.0119 per SD of dense similarity (Fisher-z units), NW(4) t = 24.66, one-sided p = 1.5e-134; EWC(12) t = 21.74; lag-1 autocorrelation of b_t 0.29. 165 months, median 442,270 pairs a month (88.4% of pairs). For scale: same SIC-4 adds 0.064, z_lag slope 0.42. `analysis/output/c_h1/`.
- **H3 (E, `E_H3_bow_peermom_test`): supported.** Test period Dec 2018 – Jun 2026 (T = 91): PEERMOM 0.262%/month per SD, NW(3) t = 2.81, one-sided p = 0.0025; NW(2) t 2.78; EWC(8) t 2.98; below the Harvey–Liu–Zhu t > 3 hurdle. Development 0.175 (t 3.22), full sample 0.222 (t 4.00); test − dev +0.087 (t 0.80): no decay. TNIC momentum 0.297 (t 2.51) alongside. `analysis/output/e_h3/`.
- **Holm {H1, H3} at 5%: both nulls rejected** (thresholds 0.025, 0.05). `analysis/output/confirmatory/`.
- **B primary (`B_primary_alignment_share`): text structure beyond industry.** 255 of 267 above-edge residual modes (95.5%) align with dense similarity residualised on SIC-3 at p < 0.05 (1,000 relabellings); binomial p < 1e-300 (overlapping windows: optimistic). Caveat: "beyond industry" = beyond SIC-3 only. `analysis/output/b_primary/`.

## Write-up (2 Oct 2026)
- **`docs/RESULTS.md`** (about 2 pages): question and data; one method paragraph each for A, B, C and E; the registered table (H1, H3, Holm, B primary); the exploratory table with BH and BY q-values (m = 19) and the 21 specs not run; the caveats Abhi listed plus two from tier 2 (E lives in small stocks; the matched-peer null does not reject); and what the results mean.
- PREREG "Exploratory specifications run" log filled (m = 19). the reviewer's 16:37 entry is marked done.
- `docs/private/PITCH.md` written (private; résumé bullet plus a 313-word spoken pitch).
- Hard stop on new project work (2 Oct); lifted 7 Oct (D19), see above.

## Exploratory results, tier 2 (2 Oct 2026; Abhi's go; all through `src/runner.py`) and the final BH/BY
- **C, the two H1 "reported beside" items** (code 42f90a5; new `tfs_stats/pairs.py`, guide card `#fn-pairs`, tests 3):
  - `C_x_mrqap` (MRQAP-DSP; annual Jul–Jun cross-sections 2012/13–2024/25; 999 relabellings): every year's text t (26–106) exceeds the largest relabelled t in any year (4.6), so the pooled p sits at its 1/1000 floor.
  - `C_x_dyadic` (pooled OLS with month FE, dyadic-robust SE, 2,161 firm clusters, 72.8M pair-months): b = 0.0122, t = 37.6. This is larger than the FM t of 24.7, because dyadic SEs ignore month-to-month variation in the slope; FM is the binding test.
- **E** (code fa5af5f; `analysis/output/e_explore2/`):
  - `E_x_portfolios`: quintile EW, price ≥ $1, FF5+UMD alpha 1.14%/month (t 2.89; UMD loading 0.66); decile EW 1.87% (t 4.14). **Value-weighted alphas are ≈ 0** (|t| < 0.6), and price ≥ $5 weakens the quintile (t 1.53). A small-stock effect.
  - `E_x_idiosyncratic`: 0.163 (t 1.81).
  - `E_x_hp_replication` (full period, common sample): TNIC-3 raw slope 0.0163 (t 4.94) vs HP's 0.008 (t 4.36); quintile EW FF3 alpha 1.42% (t 3.37) vs HP's 1.7% (t 3.30). Ours on the same rows: t 5.13, alpha 1.24% (t 3.52).
  - `E_x_perm_matched`: **p = 0.355**. Random peers drawn from the true peers' past-return deciles predict about as well (mean t 2.70 vs 2.81).
  - ST_Rev factor downloaded (Ken French; `src/ff_extra.py`, DATA.md).
- **Final `Exploratory_family_bh`, m = 19:** BH (q = 0.10) rejects 18 of 19 (not perm_matched); BY rejects 17 of 19 (also not idiosyncratic, q 0.13). `analysis/output/exploratory/README.md`.
- Not run (stay in `specs.yaml` as pending; not in m): the other 21 exploratory specs, D included.

## Exploratory results, tier 1 (1 Oct 2026; all through `src/runner.py`; m = 13 so far)
- **B** (code 7a2237b; `analysis/output/b_explore/`). Aligned share of the 267 above-edge modes, p < 0.05 each:
  - `B_x_nested_sic`: 241/267 = 90.3% (binomial p 6.5e-279). Dense similarity residualised on nested SIC-1..4, so this is the **"beyond industry"** number; the primary 95.5% means "beyond SIC-3".
  - `B_x_ff48_share` 90.6%; `B_x_sic3_share` 99.3%; `B_x_raw_dense_share` 100%.
  - `B_x_subspace_overlap`: mean overlap 0.272 vs K/N 0.0445 (6.2×); 12/12 formations p < 0.05; Fisher p 3.6e-23.
- **C** (code b61d251; `analysis/output/c_explore/`). b̄ per SD of similarity, NW(4) t and EWC(12) t:
  - `C_x_bow_null`: 0.0179 (t 24.6; EWC 20.2).
  - `C_x_missing_bm_indicator`: 0.0119 (t 25.4; 95.6% of pairs used; indicator t 1.09).
  - `C_x_pc5`: 0.0096 (t 24.1).
  - `C_x_pc10`: 0.0078 (t 19.6).
  - About 35% of the dense effect is absorbed by 10 statistical factors; the rest is not unmodelled macro betas.
  - PC residuals: new `tfs_stats.rmt.pca_factors` (guide card `#fn-pca_factors`), loadings from the 252-day window only, built to `data/processed/ff6pc{5,10}_*` in about 30 s each.
- **E** (code 1fa1d1a; `analysis/output/e_explore/`). Test-period slope (%/month per SD), NW(3) t:
  - `E_x_delist_0`: 0.261 (t 2.81). `E_x_delist_m100`: 0.262 (t 2.81). Imputation touches only 4 test firm-months (3 in the regression sample).
  - `E_x_nearest5`: 0.338 (t 4.00; 239,942 firm-months).
  - `E_x_stale_y3`: 0.208 (t 2.24).
- E README now carries the test-period counts: 214,916 before → 185,920 after the complete-case drop. log B/M is the main loss (19,472); then TNIC momentum (13,242).
- **Interim BH/BY** (`Exploratory_family_bh`, a diagnostic added after the freeze and noted in the PREREG change log; `analysis/output/exploratory/`): 13/13 rejected at q = 0.10 under both BH and BY. Re-run after tier 2.
- Tier 2: see above (run 2 Oct).

## PREREG frozen (30 Sep 2026, 20:03 ET, Abhi's go)
- **Runner guard fixed after the freeze (1 Oct, before any registered run):** the guard compared the whole spec with its frozen copy, but the confirmatory entries were frozen as `entry: pending` (the code could only be written afterwards), so H1/H3 could never run. It now compares every field except `entry` (hypothesis, statistic, sign, period, network, family, element stay locked) and additionally refuses guarded runs from a tree with any uncommitted tracked change, so every registered result is tied to a code commit. No specification changed. Tests: 8 runner tests.
- `docs/PREREG.md` frozen at commit `d1df5c795b83d7e1f3d04a23a31fe0174b6aa047`; tag `prereg-v1` marks the freeze-record commit. Primary specifications no longer change; new variants are exploratory (change log). Confirmatory family {H1 (C, dense b̄, NW(4)), H3 (E, BoW-null PEERMOM test period, NW(3))}, Holm 0.025 / 0.05. `python src/runner.py check` reports frozen = True.
- Last pre-freeze change (d1df5c7): the delisting line names performance-related = CIZ GDR, the (1 + MthRet)(1 + δ) − 1 form, no re-adding of present DelRets, and the 7 non-performance E firm-months left as is.

## Done 30 Sep: SPEC §3 delisting imputation (PREREG D14 item 1) and a panel fix it exposed
- **Delisting file** (WRDS query 11726815): 9,146 PERMNOs; DelRet missing for 298 (DelRetMissType DG/DM/DP), 212 of them performance-related (action GDR).
- **No double counting, checked on this data:** when DelRet is present, CIZ puts it on the single daily row after DelistingDt (equal to DelRet in 91.5%) and the DelistingDt month's MthRet = (1 + return through the last trade)(1 + DelRet) − 1 (91.5%; most of the rest have DelRet = 0). So a present DelRet is already in MthRet and is never added. When DelRet is missing, MthRet is only the trading return through the last trade (95.1%).
- **Rule (`src/delisting.py`):** performance-related (GDR) delistings with a missing DelRet: r = (1 + MthRet)(1 + δ) − 1, δ = −30% (N/A) or −55% (Q) by exchange at delisting; sensitivity δ ∈ {0, −30%, −100%}. Non-performance missing DelRets (GLI, MER, GEX) stay as CRSP has them. Tests: 3.
- **E firm-months touched: 13** (dev 9, test 4; 8 Nasdaq, 5 NYSE American), out of 159 performance-related missing-DelRet delistings in Jul 2012 – Jun 2026 (90 not in the universe at t−1, 32 without a text vintage, 15 below $1, 9 with no text peer). Another 7 E firm-months have a missing DelRet on a non-performance delisting (left as is). Registered diagnostic `E_delisting_coverage` (`analysis/output/e_delisting/`), run through the runner; count only.
- **Panel fix (SPEC §3: universe at formation only):** in the delisting month CIZ blanks ShareType/SecurityType/ConditionalType, so `build_panel`'s monthly universe filter was dropping 87% of delisting-month returns (3,146 of 3,620 in 2012–2026), DelRets included: a survivorship bias in E. `build_panel` now keeps each firm's exit month (`universe.add_exit_months`, `in_universe = False`; 4,306 rows); `universe_at`, Element A and B/M use `in_universe` rows only, so universe membership is unchanged. E dev rerun (diagnostic): +671 firm-months with a dependent return (163,941 → 164,612); PEERMOM 0.172 → 0.175 %/month per SD, NW(3) t 3.23 → 3.22.

## Done 29 Sep
- **D14 applied to `docs/PREREG.md` (still DRAFT; fdcdeb9):** every [PROPOSED]/[OPEN] item and the six 28 Sep flags written into the specs; family {H1, H3} with Holm 0.025 / 0.05; D exploratory; disclosure paragraph updated to list what has been computed since 28 Sep (C construction checks, B spectra, E dev period) and what has not (b̄, alignment share, any test-period return, any D variance). SPEC §3 industry-code row aligned (CRSP `siccd` primary, `sich` robustness).
- **`specs.yaml` + `src/runner.py` (SPEC §10.1; dbca50a):** 45 registered specs (2 confirmatory, 1 primary, 38 exploratory, 4 diagnostic); the runner refuses unregistered ids and guarded specs before the freeze / with uncommitted changes / edited after the freeze, and logs every attempt to `runs.log` (committed). Tests: 36 pass. Confirmatory entries stay `pending` until the freeze.
- Pulled 170fec1 (D14 SPEC rows; D15: no numeric WRDS quota; queries one at a time, each for a stated need, never in a loop, all logged).

## Done 28 Sep (D13: estimators on standard libraries)
- **`tfs_stats/` written on standard libraries** (f3c5fc8, 5065c3a): `ols_qr` (numpy QR + SciPy triangular solve, many series at once, rank check); `vcov` (statsmodels sandwich; unchanged conventions); `fama_macbeth` = per-period `ols_qr` + `fm_inference` (NW × T/(T−1) at every lag, which is linearmodels' FamaMacBeth convention, tested at L = 0 and 3); `fm_from_moments` (per-month X'X, X'y → Cholesky slopes, for C at scale); `ewc` (LLSW 2018; AR(1) T = 165 coverage 94.7% vs NW(4) 89.2%); `rmt`: `mp_edges` (raises for q > 1), `mp_sigma2_iterated` (returns Laloux's one-step value with `converged=False` on a runaway), `circular_shift_edge`, `ipr`, `clip_correlation`, `ledoit_wolf` (sklearn), `min_var_weights`. Tests: **30 pass, 0 skipped**. Guide cards added: `#fn-ewc`, `#fn-fm_moments`, MP-card companions; FM convention marked settled.
- **`practice/`** (326a733): OLS-by-hand stubs (`ols_1d_no_intercept`, `back_substitute`, `ols_qr_by_hand`, `StreamingOLS`, `RLS`) and tests; not collected by CI; tutor only.
- **C panel** (56d8185): `formation.residuals` vectorised (one QR per window); `src/c_panel.py` builds an out-of-sample FF6 residual panel (betas on the 252 days before each month, ≥ 200 obs; 2011-01 → 2026-03 in 7 s) and `c_month(t)` adds z (within-month Fisher z, ≥ 15 days), z_lag (months t−12..t−1, ≥ 126 days) and |Δβ_k|. Checks on 2014-07, 2020-01, 2025-07 (`analysis/output/c_panel/`): SD(ρ) 0.24 (Antón–Polk ~0.25), same-SIC-3 mean z 0.14–0.27 vs ~0.01, corr(z, z_lag) ≈ 0.2, all-column coverage 86–89% of pairs. **No z–text statistic computed (b̄ is primary).**
- **B inputs and spectra** (5065c3a; `analysis/output/b_spectra/`): 1 July 2014–2025, N = 500, T = 756, rolling-beta residuals: empirical edge 3.32–3.35 (MP 3.29); 20–25 residual eigenvalues above it; median IPR × N 3.0–3.7 (random 3); the σ² iteration runs away every year. Top residual modes are long-short sector-like modes, not leaked factor exposure (R² on FF6 0.01–0.15). **No alignment share computed.**
- **E development period only** (ac30f3c; `analysis/output/e_dev/`): CRSP monthly truncated at Nov 2018 before any computation. 77 months, 163,941 firm-months. With all controls incl. TNIC momentum: PEERMOM 0.172%/month per SD, NW(3) t 3.23, EWC(7) t 4.75 (tuning period, not evidence for H3). Runtime 91 s.
- **PREREG draft: 6 review flags** (section "Flags raised while building"): B starts 2014 (not 2013); B uses rolling betas (draft wording said in-window); C pairs with missing B/M ~10%; z_lag ≥ 126 days; peer returns ≥ 8/12 months; ~25% of firms have no text peer at SIC-3 density.

## D12 done (27 Sep, 20:15 ET)
- Both daily price/volume files converted: 2010–2017 14,055,778 and 2018–2026 18,275,590 unique permno-dates (3,238 and 3,615 duplicate keys dropped); keys identical to the daily return files (0 unmatched either way). Merged into `crsp_daily` (16,093,352 rows; prc and vol present on 98.8%).
- Daily Amihud (log mean |r|/(|prc|·vol) over the prior 12 months, ≥ 120 valid days, zero-volume days skipped), 165 formation months 2012-07 → 2026-03: coverage 99.5% of the text universe (min 96.7%), **99.8% of the top 1,000 used in C (min 98.0%)**. Rank correlation with the monthly proxy 0.994 (0.985–0.996); Pearson of logs 0.981. `d_illiq` in the pair frame now uses the daily measure; the monthly proxy stays as fallback.

## Done this evening (27 Sep)
- **Orphaned job killed (19:31 ET):** a validity diagnostic I started at 16:15 ET by piping a script into `python -` with a 10-worker multiprocessing pool. On macOS (spawn) workers cannot re-import a stdin script, so each died at start and the pool respawned them for 3 h 13 min, producing nothing and throttling the Mac. My 16:25 `pkill` hit only the workers, not the parent. Killed parent 88156, resource tracker 88165 and all spawn workers; pgrep confirms none remain. A 4-worker pool cap was added and then reverted at Abhi's request (use full compute). **Verified no effect (20:05 ET):** every file modified since 16:15 traces to a known writer (rebuild chain, the cloud session, my edits); stored HTML untouched since 16:04 (61,589 files, 0/300 gzip errors); item1 61,589 rows; embeddings 61,144, recomputing 64 gives max |diff| 3e-8; BoW counts for a recomputed shard (1,988 filings) identical; SPAC 386, masks 54,254 and Element A AUCs as reported. Rules: no multiprocessing from stdin scripts (use a file with a `__main__` guard); after any kill, check the parent is gone; tell Abhi before starting a heavy job.
- **D11 applied:** `src/networks.py` is the single network builder for B, C, D, E (dense masked; BoW nouns with `CORRECTION = 'null'`; raw BoW for robustness only); `pair_frame` carries s_dense, s_bow, s_bow_raw. No builder passes raw/mult (only the Element A diagnostic compares all corrections). Test: null removes 99.7% of the length term on a random-word fixture, additive 53%.
- **D12 code:** `convert_wrds.convert_pv` (permno int32, date, prc = |DlyPrc| float32, vol float32, key check), `build_panel` merges prc/vol, `formation.amihud_daily` (log mean |r|/(|prc|·vol), prior 12 months, ≥ 120 valid days), `d_illiq` in the pair frame; monthly proxy kept as fallback. Tests on synthetic fixtures pass (6 passed, 12 skipped).
- **PREREG drafted (`docs/PREREG.md`, DRAFT):** all TODOs filled from SPEC and D2–D12; [PROPOSED] items and one [OPEN] item (delisting returns: `MthDelFlg` not in the monthly pull) for Abhi.

## Text layer v1 — frozen (git tag `text-layer-v1`, 27 Sep 17:28 ET; no extractor/vocabulary changes through 8 Oct)
- **D10:** all 61,589 primary documents re-downloaded and stored (13:51–16:04, 0 failures, 13 GB gz). Canonical Item 1 = v1 or v2 by structural validity (start/end not at cross-references, no Item 1A inside, 300–40,000 words; prefer v2 when both valid and J < 0.8): v1 47,662, v2 12,957, invalid-only 661, none 309; 99.2% > 300 words. Hand check of 100 random disagreements: rule picks the better candidate 97/100 (95% CI 91.6–99.0%); span fully correct 90/100. Mojibake: 0 (EDGAR documents are ASCII).
- **D8:** 386 SPAC filings (text rule; SIC rule rejected at precision 0.34); 1.8% of universe firm-months in 2022.
- **Masking:** 93.6% of linked filings get ≥ 1 own-name mask (84.5% in the first 1,000 words). Dense embeddings masked.
- **P5/P6 rebuilt** on the canonical text: 61,144 filings embedded; BoW 61,144 × 144,498.
- **Element A (SPACs excluded), means 2012–2026:** same-SIC-3 AUC dense 0.882, BoW nouns 0.882, BoW nouns null-corrected 0.905. TNIC-3 edge Jaccard: BoW nouns 0.644 (null 0.647), dense 0.361, SIC-3 0.277; Spearman with TNIC score 0.91 (was 0.71 on the P2 text). Length correlation: raw BoW +0.93, null +0.55, dense −0.29.

## Done today (27 Sep, afternoon)
- D8 SPAC rule, D9 diagnostics (null-mean correction recommended → D11), name masking (`src/mask_names.py`), B/C plumbing (`src/formation.py`, monthly Amihud proxy for D12), D10 re-download + canonical extraction + hand check.

## Blocked
- Nothing.

## Next
- Assistant: exploratory specs by priority (C: BoW null/raw, missing-B/M kept, PC5/PC10; E: nearest-5, delisting delta 0/-100%; B: SIC-3 and raw-dense shares), each through the runner for the BH count; then `docs/RESULTS.md` (2 pages), résumé bullet and 2-minute pitch from these numbers. Hard stop on new project work Fri 2 Oct.
- Abhi: practice/ OLS by hand.

## Requests
_(add requests here)_
