# Romano–Wolf stepdown across Fama–MacBeth slope series (D25)

arch `StepM`, losses −b_t vs 0 (superior = mean slope > 0), stationary bootstrap (mean block 4), 10,000 replications, seed 2026, FWER 5%. In arch 8.0.0 the studentise flag does not studentise, so this is the non-studentised stepdown; simulated FWER ≈ 6.5% (iid) to 8.5–11% (AR(1) 0.2) at these shapes (STATS_GUIDE #fn-romano_wolf).

## C (full period, 165 months)

8 of 8 mean slopes significantly positive at FWER 5%.

| spec | mean slope | superior |
|---|---|---|
| `C_x_bow_null` | 0.01785 | yes |
| `C_x_bow_raw` | 0.01935 | yes |
| `C_x_binary_network` | 0.08292 | yes |
| `C_x_missing_bm_indicator` | 0.01185 | yes |
| `C_x_pc5` | 0.00957 | yes |
| `C_x_pc10` | 0.00780 | yes |
| `C_x_dimson` | 0.01156 | yes |
| `C_x_sich` | 0.01104 | yes |

## E (test period, 91 months)

1 of 15 mean slopes significantly positive at FWER 5%.

| spec | mean slope | superior |
|---|---|---|
| `E_x_nearest5` | 0.00338 | no |
| `E_x_delist_0` | 0.00261 | no |
| `E_x_delist_m100` | 0.00262 | no |
| `E_x_sim_weighted` | 0.00250 | no |
| `E_x_h_6_1` | 0.00282 | no |
| `E_x_h_12_7` | -0.00017 | no |
| `E_x_grundy_martin` | 0.00074 | no |
| `E_x_idiosyncratic` | 0.00163 | no |
| `E_x_text_only` | 0.00105 | no |
| `E_x_sic_only` | 0.00005 | no |
| `E_x_both` | 0.00251 | no |
| `E_x_dense_only` | 0.00146 | no |
| `E_x_stale_y3` | 0.00208 | no |
| `E_x_sich` | 0.00540 | yes |
| `E_x_nyse20` | 0.00185 | no |

