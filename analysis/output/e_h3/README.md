# H3 (Element E): text-peer momentum out of sample — confirmatory

Spec `E_H3_bow_peermom_test`, PREREG frozen at d1df5c7, run through `src/runner.py`.

**Test period (Dec 2018 – Jun 2026, T = 91): PEERMOM slope = 0.262%/month per SD, NW(3) t = 2.81, one-sided p = 0.00248.** Beside it: NW(2) t = 2.78; EWC(8) t = 2.98 (one-sided p from t_8 = 0.00877); Harvey–Liu–Zhu t > 3: no.

Development (Jul 2012 – Nov 2018): 0.175%/month (t = 3.22). Full sample: 0.222%/month (t = 4.00). Test − development: 0.087%/month (t = 0.80).

185,920 test firm-months with every variable; 12 months use the carried-forward FY2023 TNIC network; delisting imputation applied to 107 panel rows (13 E firm-months, PREREG).

## Test-period mean slopes

| | coef (%/month per SD) | NW(3) t | NW(2) t | EWC(8) t |
|---|---|---|---|---|
| const | 0.783 | 1.18 | 1.16 | 1.03 |
| peermom | 0.262 | 2.81 | 2.78 | 2.98 |
| log_me | 0.205 | 1.03 | 1.01 | 0.96 |
| log_bm | 0.286 | 1.47 | 1.5 | 1.23 |
| r_1 | -0.141 | -1.06 | -1.09 | -0.84 |
| r12_2 | 0.097 | 0.86 | 0.76 | 1.14 |
| indmom | 0.238 | 1.86 | 1.81 | 2.23 |
| sic3mom | -0.063 | -0.74 | -0.71 | -0.73 |
| tnicmom | 0.297 | 2.51 | 2.4 | 3.23 |

Runtime 231 s.
