# Status

_Last updated: Sun 27 Sep 2026, 19:35 ET (local Claude Code session)_

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
- **D12 WRDS daily price/volume:** file 1 (2010–2017, query 11716335) landed and converted: 14,055,778 unique permno-dates, keys identical to the daily return file; 2,946 zero prices, 354,648 zero-volume days (skipped in Amihud). File 2 (2018–2026, query 11716454, submitted 19:07) pending; when it lands: `python src/convert_wrds.py && python src/build_panel.py`, then daily Amihud coverage and its correlation with the monthly proxy.

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
- Abhi: review `docs/PREREG.md` ([PROPOSED] items; [OPEN] delisting returns) for the Thu 1 Oct freeze; `ols_qr`, `vcov`, `fama_macbeth` (critical path for B, C, E).
- Claude: convert D12 file 2 and merge (as soon as it lands); `specs.yaml` + runner (SPEC §10.1) before the freeze; FF-48 industry map and E signal construction (no returns looked at in the test period).

## Requests for Cowork
_(local Claude Code sessions add requests here)_
