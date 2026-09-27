# Status

_Last updated: Sun 27 Sep 2026, 03:12 ET_

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
  - P2 complete: last 15,597 filings scraped here in 34.5 min (7.6 req/s); all 61,589 have a result, 0 failed downloads. 95.5% extract > 300 words (90.4% in 2011 → 97.1% in 2026), median 6,452 words; 2,254 (3.7%) extract 0 words.
  - P5 complete on MPS: 59,172 filings (≥ 100 words) embedded, unit norm, no NaN, ~21 min total; 96.3% of linked firm-years have an embedding. MPS and CPU embeddings agree to ~1e-7.
  - P6 (v0, calendar-year vocabulary): 52,270 linked filings, 16 yearly matrices, 24–30k words, ~480–634 nonzeros per document, 95 s.

## Running
- Nothing.

## Blocked
- Nothing.

## Next
- Abhi: implement `ols_qr`, `vcov`, then `fama_macbeth` (critical path for Elements C and E); answer D2–D6 (SPEC §13).
- Assistant: P6 with a trailing-12-month vocabulary (the calendar-year version has look-ahead, SPEC §3) and a nouns-only variant; diagnose the 3.7% zero-word extracts (EX-13 / incorporation by reference); Element A validation (similarity distributions, AUC vs SIC-3, neighbour spot checks, TNIC agreement).

## Requests
_(add requests here)_
