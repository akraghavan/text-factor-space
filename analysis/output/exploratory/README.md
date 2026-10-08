# Exploratory family: Benjamini–Hochberg and Benjamini–Yekutieli at q = 0.1

m = 45 exploratory specs run (`python src/runner.py count`). p-values from the latest `ok` runner record of each (`runs.log`; nothing re-estimated): one-sided in the registered direction, two-sided for the one spec with no predicted sign; q-values from `tfs_stats.multitest.bh` / `.by`. BY is valid under any dependence; BH assumes independence or positive dependence, which overlapping variants of the same test roughly satisfy.

| Spec | Element | Estimate | t | p | p used | BH q | BH reject | BY q | BY reject | commit |
|---|---|---|---|---|---|---|---|---|---|---|
| `B_x_T1008` | B | aligned share 0.928 |  | 0 | one-sided (+) | 0 | yes | 0 | yes | 2f695d1 |
| `B_x_ff48_share` | B | aligned share 0.906 |  | 3.7e-281 | one-sided (+) | 3.3e-280 | yes | 1.5e-279 | yes | 8003fe6 |
| `B_x_nested_sic` | B | aligned share 0.903 |  | 6.5e-279 | one-sided (+) | 4.9e-278 | yes | 2.1e-277 | yes | 8003fe6 |
| `B_x_raw_dense_share` | B | aligned share 1 |  | 0 | one-sided (+) | 0 | yes | 0 | yes | 8003fe6 |
| `B_x_sic3_share` | B | aligned share 0.993 |  | 0 | one-sided (+) | 0 | yes | 0 | yes | 8003fe6 |
| `B_x_subspace_overlap` | B | overlap / random 6.15 |  | 3.6e-23 | one-sided (+) | 9.6e-23 | yes | 4.2e-22 | yes | 8003fe6 |
| `C_x_12m_windows` | C | b̄ 0.011 | 17.6 | 3.1e-10 | one-sided (+) | 7.2e-10 | yes | 3.2e-09 | yes | 2f695d1 |
| `C_x_binary_network` | C | b̄ 0.0829 | 39 | 0 | one-sided (+) | 0 | yes | 0 | yes | 2f695d1 |
| `C_x_bow_null` | C | b̄ 0.0179 | 24.6 | 2e-134 | one-sided (+) | 1e-133 | yes | 4.4e-133 | yes | c53c620 |
| `C_x_bow_raw` | C | b̄ 0.0193 | 24.5 | 1.8e-132 | one-sided (+) | 8e-132 | yes | 3.5e-131 | yes | 2f695d1 |
| `C_x_dimson` | C | b̄ 0.0116 | 24.2 | 8.2e-130 | one-sided (+) | 3.4e-129 | yes | 1.5e-128 | yes | b97b0e3 |
| `C_x_dyadic` | C | pooled b 0.0122 | 37.6 | 1e-238 | one-sided (+) | 6.7e-238 | yes | 2.9e-237 | yes | 656569c |
| `C_x_missing_bm_indicator` | C | b̄ 0.0119 | 25.4 | 1.2e-142 | one-sided (+) | 6.8e-142 | yes | 3e-141 | yes | c53c620 |
| `C_x_mrqap` | C | mean annual b 0.011 | 249 | 0.001 | one-sided (+) | 0.0019 | yes | 0.0082 | yes | 656569c |
| `C_x_pc10` | C | b̄ 0.0078 | 19.6 | 1.2e-85 | one-sided (+) | 3.7e-85 | yes | 1.6e-84 | yes | c53c620 |
| `C_x_pc5` | C | b̄ 0.00957 | 24.1 | 5.9e-129 | one-sided (+) | 2.1e-128 | yes | 9e-128 | yes | c53c620 |
| `C_x_post_fy2020` | C | b̄ 0.0132 | 14.1 | 1.2e-45 | one-sided (+) | 3.5e-45 | yes | 1.5e-44 | yes | b97b0e3 |
| `C_x_post_sep2023` | C | b̄ 0.0128 | 8.76 | 9.9e-19 | one-sided (+) | 2.5e-18 | yes | 1.1e-17 | yes | b97b0e3 |
| `C_x_pre_fy2020` | C | b̄ 0.0112 | 20.2 | 9.7e-91 | one-sided (+) | 3.1e-90 | yes | 1.4e-89 | yes | 2f695d1 |
| `C_x_sich` | C | b̄ 0.011 | 24.2 | 3.4e-129 | one-sided (+) | 1.3e-128 | yes | 5.6e-128 | yes | b97b0e3 |
| `D_x_ff6text_vs_ff6cc` | D | Δ log var 0.00115 | 0.0933 | 0.54 | one-sided (-) | 0.59 | no | 1 | no | 13d859f |
| `D_x_text_vs_constcorr` | D | Δ log var 0.0389 | 2.48 | 0.99 | one-sided (-) | 1 | no | 1 | no | 5900cd7 |
| `D_x_text_vs_lwnl` | D | Δ log var 0.251 | 6.93 | 1 | one-sided (-) | 1 | no | 1 | no | 5900cd7 |
| `D_x_text_vs_placebo` | D | Δ log var 0.039 | 2.49 | 0.99 | one-sided (-) | 1 | no | 1 | no | 5900cd7 |
| `E_x_both` | E | slope 0.00251 | 2.78 | 0.0028 | one-sided (+) | 0.0043 | yes | 0.019 | yes | 4830b9d |
| `E_x_delist_0` | E | slope 0.00261 | 2.81 | 0.0025 | one-sided (+) | 0.004 | yes | 0.018 | yes | c53c620 |
| `E_x_delist_m100` | E | slope 0.00262 | 2.81 | 0.0025 | one-sided (+) | 0.004 | yes | 0.018 | yes | c53c620 |
| `E_x_dense_only` | E | slope 0.00146 | 1.23 | 0.11 | one-sided (+) | 0.14 | no | 0.62 | no | 4830b9d |
| `E_x_grundy_martin` | E | slope 0.000737 | 0.731 | 0.23 | one-sided (+) | 0.28 | no | 1 | no | 4830b9d |
| `E_x_h_12_7` | E | slope -0.000169 | -0.121 | 0.55 | one-sided (+) | 0.59 | no | 1 | no | 4830b9d |
| `E_x_h_6_1` | E | slope 0.00282 | 2.32 | 0.01 | one-sided (+) | 0.015 | yes | 0.065 | yes | 4830b9d |
| `E_x_hp_replication` | E | slope 0.00354 | 4.34 | 7.2e-06 | one-sided (+) | 1.5e-05 | yes | 6.8e-05 | yes | 6a3abf9 |
| `E_x_idiosyncratic` | E | slope 0.00163 | 1.81 | 0.035 | one-sided (+) | 0.048 | yes | 0.21 | no | c53c620 |
| `E_x_nearest5` | E | slope 0.00338 | 4 | 3.1e-05 | one-sided (+) | 6.4e-05 | yes | 0.00028 | yes | c53c620 |
| `E_x_nyse20` | E | slope 0.00185 | 1.79 | 0.037 | one-sided (+) | 0.048 | yes | 0.21 | no | 4830b9d |
| `E_x_perm_matched` | E | t (observed) 2.81 |  | 0.35 | one-sided (+) | 0.41 | no | 1 | no | 6a3abf9 |
| `E_x_perm_stratified` | E | t (observed) 2.81 |  | 0.001 | one-sided (+) | 0.0019 | yes | 0.0082 | yes | b5e3b9c |
| `E_x_placebo_24_13` | E | slope -0.00209 | -1.45 | 0.15 | two-sided | 0.18 | no | 0.78 | no | 4830b9d |
| `E_x_portfolios` | E | alpha 0.0114 | 2.89 | 0.0019 | one-sided (+) | 0.0034 | yes | 0.015 | yes | 6a3abf9 |
| `E_x_post_sep2023` | E | slope 0.00271 | 2.4 | 0.0083 | one-sided (+) | 0.012 | yes | 0.055 | yes | 4830b9d |
| `E_x_sic_only` | E | slope 5.15e-05 | 0.0245 | 0.49 | one-sided (+) | 0.55 | no | 1 | no | 4830b9d |
| `E_x_sich` | E | slope 0.0054 | 5.07 | 2e-07 | one-sided (+) | 4.5e-07 | yes | 2e-06 | yes | 4830b9d |
| `E_x_sim_weighted` | E | slope 0.0025 | 3 | 0.0014 | one-sided (+) | 0.0025 | yes | 0.011 | yes | 4830b9d |
| `E_x_stale_y3` | E | slope 0.00208 | 2.24 | 0.013 | one-sided (+) | 0.018 | yes | 0.078 | yes | c53c620 |
| `E_x_text_only` | E | slope 0.00105 | 1.12 | 0.13 | one-sided (+) | 0.16 | no | 0.72 | no | 4830b9d |

Rejected at q = 0.1: BH 34 of 45, BY 32 of 45.
