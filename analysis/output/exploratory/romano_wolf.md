# Romano–Wolf stepdown across Fama–MacBeth slope series (D25; studentised, D28)

arch `StepM` on studentised series x_t = b_t / (√T · SE_NW), SE from each spec's own Newey–West lags on the full sample and held fixed across draws (arch 8.0.0 does not studentise itself); superior = mean > 0; stationary bootstrap; 10,000 replications; seed 2026; FWER 5%. Block length: the smallest of 4, 8, 12 with simulated FWER ≤ 6% (independent AR(1) series at the family's mean lag-1 autocorrelation and shape; 2,000 draws).

## C (full period, 165 months)

Mean lag-1 autocorrelation 0.361; NW lags 4. Simulated FWER at blocks 4 / 8 / 12: 0.145 / 0.138 / 0.143. Block used: 12 (simulated FWER 0.143; no block reaches 6%, so RW is mildly liberal at this rate).

8 of 8 mean slopes significantly positive at FWER 5%.

| spec | t (NW) | superior |
|---|---|---|
| `C_x_bow_null` | 24.65 | yes |
| `C_x_bow_raw` | 24.46 | yes |
| `C_x_binary_network` | 38.96 | yes |
| `C_x_missing_bm_indicator` | 25.40 | yes |
| `C_x_pc5` | 24.13 | yes |
| `C_x_pc10` | 19.58 | yes |
| `C_x_dimson` | 24.21 | yes |
| `C_x_sich` | 24.15 | yes |

## E (test period, 91 months)

Mean lag-1 autocorrelation 0.059; NW lags 3. Simulated FWER at blocks 4 / 8 / 12: 0.114 / 0.154 / 0.177. Block used: 12 (simulated FWER 0.177; no block reaches 6%, so RW is mildly liberal at this rate).

8 of 15 mean slopes significantly positive at FWER 5%.

| spec | t (NW) | superior |
|---|---|---|
| `E_x_nearest5` | 4.00 | yes |
| `E_x_delist_0` | 2.81 | yes |
| `E_x_delist_m100` | 2.81 | yes |
| `E_x_sim_weighted` | 3.00 | yes |
| `E_x_h_6_1` | 2.32 | yes |
| `E_x_h_12_7` | -0.12 | no |
| `E_x_grundy_martin` | 0.73 | no |
| `E_x_idiosyncratic` | 1.81 | no |
| `E_x_text_only` | 1.12 | no |
| `E_x_sic_only` | 0.02 | no |
| `E_x_both` | 2.78 | yes |
| `E_x_dense_only` | 1.23 | no |
| `E_x_stale_y3` | 2.24 | yes |
| `E_x_sich` | 5.07 | yes |
| `E_x_nyse20` | 1.79 | no |

