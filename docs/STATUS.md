# Status

_Last updated: Sun 27 Sep 2026, 04:15 ET_

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
- Nothing.

## Blocked
- Nothing.

## Next
- Abhi: implement `ols_qr`, `vcov`, then `fama_macbeth` (critical path for Elements C and E); answer D2–D6 (SPEC §13).
- Abhi decisions raised by Element A: (1) exclude SIC 6799 blank-check companies (SPACs, 468 in the June 2022 universe) from the universe? (2) BoW length/hub effect: HP-style median-similarity adjustment or length controls only in C? (3) a best-of-v1/v2 Item 1 pass over all 61,589 filings (~2.1 h re-download) to fix the ~7% of v1 spans that look wrong?
- Assistant: Element B/C prerequisites that do not need `tfs_stats` (rolling FF6 betas and daily residuals, pair panels); name-masking pass before embedding (SPEC §5 pitfalls).

## Requests
_(add requests here)_
