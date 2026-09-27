# WRDS query log

Cap (CLAUDE.md rule 0): at most 10 web-query submissions per calendar day and 30 per calendar month, one running at a time, status checks at most once a minute, no resubmitting loops. Every submission is logged here.

| Date (ET) | Query id | Product | Content | Range | Result | Note |
|---|---|---|---|---|---|---|
| 2026-09-26 | 11713723 | crsp_q_ccm | Linking table (+ CIK, SIC, GICS, busdesc) | all | 32,948 rows | |
| 2026-09-26 | 11713725 | crsp_q_stock | Monthly stock file (CIZ) | 2009-01 – 2026-06 | 1,690,904 rows | |
| 2026-09-26 | 11713727 | crsp_q_stock | Daily stock file | 2010-01-01 – 2017-12-31 | 14,059,016 rows | took 58 min |
| 2026-09-26 | 11713729 | crsp_q_stock | Daily stock file | 2018-01-01 – 2026-03-31 | 18,279,205 rows | |
| 2026-09-26 | 11713731 | crsp_q_ccm | Fundamentals Annual | 2009-01 – 2026-09 | 95,382 rows | |
| 2026-09-26 | 11713797 | crsp_q_stock | Daily stock file | 2010-01-01 – 2013-12-31 | not downloaded | re-submit while 11713727 looked stalled; redundant |
| 2026-09-26 | 11713798 | crsp_q_stock | Daily stock file | 2014-01-01 – 2017-12-31 | not downloaded | redundant, same reason |
| 2026-09-27 | 11716335 | crsp_q_stock | Daily stock file: price/volume (dlyprc, dlyvol) for D12 daily Amihud | 2010-01-01 – 2017-12-31 | 14,059,016 rows | 18:20–18:34 ET; = row count of 11713727; saved as data/raw/crsp_dsf_pv_2010_2017.csv.gz |
| 2026-09-27 | 11716454 | crsp_q_stock | Daily stock file: price/volume (dlyprc, dlyvol) for D12 daily Amihud | 2018-01-01 – 2026-03-31 | 18,279,205 rows | 19:07–19:37 ET; = row count of 11713729; saved as data/raw/crsp_dsf_pv_2018_2026.csv.gz |

26 Sep total: 7 submissions (within the daily cap of 10).
27 Sep total: 2 submissions. September: 9 of 30.
