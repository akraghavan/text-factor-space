# Status

_Last updated: Mon 28 Sep 2026, 13:14 ET (local Claude Code session)_

## Done
- Spec v1 (`docs/SPEC.md`): every element checked against primary sources by five research dossiers and a critic pass.
- SEC: bulk submissions → 61,589 10-K/10-KT indexed (Jun 2011–Sep 2026).
- WRDS pulls (Sat night): CRSP v2 monthly and daily (2010-01-04 → 2026-03-31), CCM link table, CCM Fundamentals Annual. Fama–French factors and Hoberg–Phillips TNIC-3 downloaded.
- **D0 resolved (27 Sep):** CMU's WRDS representative confirmed the Claude plan is an enterprise no-training instance; scripted WRDS queries allowed under the cap in `CLAUDE.md` rule 0.
- **D7 done (27 Sep, Abhi's approval):** SPEC §1/§2/§11/§12/§13 rewritten for the WRDS clearance (§13 now splits open and resolved decisions); `.claude/settings.json` no longer denies reads of the WRDS-derived files (credential and force-push denials kept).
- Repo scaffold: bootstrap script, Claude Code project settings (Opus 5.5, effort high), CI, tests (12, skipped until implemented), DATA/PREREG docs, MIT licence.
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
- Nothing.

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
- **Orphaned job killed (19:31 ET):** a validity diagnostic I started at 16:15 ET by piping a script into `python -` with a 10-worker multiprocessing pool. On macOS (spawn) workers cannot re-import a stdin script, so each died at start and the pool respawned them for 3 h 13 min, producing nothing and throttling the Mac. My 16:25 `pkill` hit only the workers, not the parent. Killed parent 88156, resource tracker 88165 and all spawn workers; pgrep confirms none remain. A 4-worker pool cap was added and then reverted at Abhi's request (use full compute). **Verified no effect (20:05 ET):** every file modified since 16:15 traces to a known writer (rebuild chain, Cowork, my edits); stored HTML untouched since 16:04 (61,589 files, 0/300 gzip errors); item1 61,589 rows; embeddings 61,144, recomputing 64 gives max |diff| 3e-8; BoW counts for a recomputed shard (1,988 filings) identical; SPAC 386, masks 54,254 and Element A AUCs as reported. Rules: no multiprocessing from stdin scripts (use a file with a `__main__` guard); after any kill, check the parent is gone; tell Abhi before starting a heavy job.
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
- Abhi: review the PREREG draft ([PROPOSED], [OPEN] delisting returns, the 6 flags) for the Thu 1 Oct freeze; practice/ OLS by hand.
- Claude: `specs.yaml` + runner (SPEC §10.1); C monthly sufficient statistics for all 165 months (ready to run the moment PREREG is frozen); MRQAP / dyadic-robust after Fall Break per plan; D if it stays in.

## Requests for Cowork
_(local Claude Code sessions add requests here)_
