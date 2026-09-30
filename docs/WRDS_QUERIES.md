# WRDS query log

Rules (CLAUDE.md rule 0, D15): one query running at a time, no tight status polling, no resubmitting loops; no numeric daily or monthly quota (dropped 29 Sep). Every submission is logged here.

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
| 2026-09-29 | 11726815 | crsp_q_stock | Stock Delisting Information (stkdelists), all 22 variables, all action types, entire database, for the D14 delisting-return imputation | DelistingDt 2009-01-01 – 2026-06-29 | 9,146 rows | 13:53 ET, 2 s; one row per PERMNO; delret missing on 298; saved as data/raw/crsp_delist_2009_2026.csv.gz (sha256 944d1184…) |

26 Sep total: 7 submissions.
27 Sep total: 2 submissions.
29 Sep total: 1 submission. September so far: 10.
