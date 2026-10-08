# Romano–Wolf stepdown across Fama–MacBeth slope series (D25; standardised, D28; size-calibrated, D30)

arch `StepM` on standardised series x_t = b_t / (√T · SE_NW), SE from each spec's own Newey–West lags on the full sample and held fixed across draws (Hansen 2005's SPA convention; arch 8.0.0 does not studentise itself); superior = mean > 0; stationary bootstrap; 10,000 replications; seed 2026. Calibration (D30): block = the lowest simulated FWER at nominal 5% among 4, 8, 12; nominal size = the largest of 0.05 … 0.005 whose simulated FWER ≤ 5% at that block (independent AR(1) series at the family's mean lag-1 autocorrelation and shape; 2,000 draws).

## C (full period, 165 months)

Mean lag-1 autocorrelation 0.361; NW lags 4.
Simulated FWER at nominal 5%, blocks 4 / 8 / 12: 0.145 / 0.138 / 0.143 → block 8.
At block 8, simulated FWER by nominal size 0.05: 0.138, 0.04: 0.113, 0.03: 0.092, 0.02: 0.065, 0.015: 0.051, 0.01: 0.036, 0.005: 0.021 → **size 0.01** (simulated FWER 0.036).

**8 of 8 mean slopes significantly positive at simulated FWER ≤ 5%.** Context: at nominal 5% and block 12 (the D28 run; liberal, simulated FWER 0.143), 8 of 8.

| spec | t (NW) | superior (calibrated) | superior (nominal 5%, block 12) |
|---|---|---|---|
| `C_x_bow_null` | 24.65 | yes | yes |
| `C_x_bow_raw` | 24.46 | yes | yes |
| `C_x_binary_network` | 38.96 | yes | yes |
| `C_x_missing_bm_indicator` | 25.40 | yes | yes |
| `C_x_pc5` | 24.13 | yes | yes |
| `C_x_pc10` | 19.58 | yes | yes |
| `C_x_dimson` | 24.21 | yes | yes |
| `C_x_sich` | 24.15 | yes | yes |

## E (test period, 91 months)

Mean lag-1 autocorrelation 0.059; NW lags 3.
Simulated FWER at nominal 5%, blocks 4 / 8 / 12: 0.114 / 0.154 / 0.177 → block 4.
At block 4, simulated FWER by nominal size 0.05: 0.114, 0.04: 0.096, 0.03: 0.075, 0.02: 0.057, 0.015: 0.045, 0.01: 0.036, 0.005: 0.022 → **size 0.015** (simulated FWER 0.045).

**3 of 15 mean slopes significantly positive at simulated FWER ≤ 5%.** Context: at nominal 5% and block 12 (the D28 run; liberal, simulated FWER 0.177), 8 of 15.

| spec | t (NW) | superior (calibrated) | superior (nominal 5%, block 12) |
|---|---|---|---|
| `E_x_nearest5` | 4.00 | yes | yes |
| `E_x_delist_0` | 2.81 | no | yes |
| `E_x_delist_m100` | 2.81 | no | yes |
| `E_x_sim_weighted` | 3.00 | yes | yes |
| `E_x_h_6_1` | 2.32 | no | yes |
| `E_x_h_12_7` | -0.12 | no | no |
| `E_x_grundy_martin` | 0.73 | no | no |
| `E_x_idiosyncratic` | 1.81 | no | no |
| `E_x_text_only` | 1.12 | no | no |
| `E_x_sic_only` | 0.02 | no | no |
| `E_x_both` | 2.78 | no | yes |
| `E_x_dense_only` | 1.23 | no | no |
| `E_x_stale_y3` | 2.24 | no | yes |
| `E_x_sich` | 5.07 | yes | yes |
| `E_x_nyse20` | 1.79 | no | no |

