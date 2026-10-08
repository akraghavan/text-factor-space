# H1 (Element C): text similarity and residual comovement — confirmatory

Spec `C_H1_dense_bbar`, PREREG frozen at 01cb5cc, run through `src/runner.py`.

**b̄ (dense s̃) = 0.0119** per SD of similarity, NW(4) SE 0.0005, **t = 24.66**, one-sided p = 1.47e-134. Beside it: EWC(12) t = 21.74 (one-sided p from t_12 = 2.63e-11); lag-1 autocorrelation of b_t = 0.29.

165 months (skipped 0); median 442,270 pairs a month in the regression (88.4% of all pairs); max condition number of X'X 1.9e+05.

## All mean slopes (Fama–MacBeth)

| | mean slope | NW(4) t |
|---|---|---|
| const | 0.0395 | 5.189 |
| s_tilde | 0.0119 | 24.6591 |
| z_lag | 0.4212 | 26.6439 |
| same_sic1 | 0.0112 | 8.1973 |
| same_sic2 | 0.0322 | 17.9677 |
| same_sic3 | 0.0114 | 4.8299 |
| same_sic4 | 0.0635 | 24.494 |
| d_me | -0.0047 | -4.3092 |
| d_bm | 0.0019 | 1.8723 |
| d_mom | -0.0159 | -5.8925 |
| db_Mkt_RF | -0.0234 | -8.3291 |
| db_SMB | -0.0038 | -3.9012 |
| db_HML | -0.0035 | -3.377 |
| db_RMW | -0.0046 | -4.2672 |
| db_CMA | -0.0072 | -5.186 |
| db_Mom | -0.0198 | -5.884 |
| d_illiq | -0.0079 | -5.3677 |
| same_fye | 0.0034 | 7.7996 |
| len_sum | 0.0002 | 0.5183 |
| len_diff | -0.0006 | -1.7263 |
| same_exch | 0.0037 | 6.7997 |

Runtime 133 s.
