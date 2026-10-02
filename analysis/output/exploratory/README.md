# Exploratory family: Benjamini–Hochberg and Benjamini–Yekutieli at q = 0.1

m = 19 exploratory specs run (`python src/runner.py count`). One-sided p-values from the latest `ok` runner record of each (`runs.log`; nothing re-estimated); q-values from `tfs_stats.multitest.bh` / `.by`. BY is valid under any dependence; BH assumes independence or positive dependence, which overlapping variants of the same test roughly satisfy.

| Spec | Element | Estimate | t | one-sided p | BH q | BH reject | BY q | BY reject | commit |
|---|---|---|---|---|---|---|---|---|---|
| `B_x_ff48_share` | B | aligned share 0.906 |  | 3.7e-281 | 2.3e-280 | yes | 8.2e-280 | yes | 7a2237b |
| `B_x_nested_sic` | B | aligned share 0.903 |  | 6.5e-279 | 3.1e-278 | yes | 1.1e-277 | yes | 7a2237b |
| `B_x_raw_dense_share` | B | aligned share 1 |  | 0 | 0 | yes | 0 | yes | 7a2237b |
| `B_x_sic3_share` | B | aligned share 0.993 |  | 0 | 0 | yes | 0 | yes | 7a2237b |
| `B_x_subspace_overlap` | B | overlap / random 6.15 |  | 3.6e-23 | 6.9e-23 | yes | 2.4e-22 | yes | 7a2237b |
| `C_x_bow_null` | C | b̄ 0.0179 | 24.6 | 2e-134 | 5.4e-134 | yes | 1.9e-133 | yes | b61d251 |
| `C_x_dyadic` | C | pooled b 0.0122 | 37.6 | 1e-238 | 3.9e-238 | yes | 1.4e-237 | yes | 42f90a5 |
| `C_x_missing_bm_indicator` | C | b̄ 0.0119 | 25.4 | 1.2e-142 | 3.8e-142 | yes | 1.4e-141 | yes | b61d251 |
| `C_x_mrqap` | C | mean annual b 0.011 | 249 | 0.001 | 0.0015 | yes | 0.0052 | yes | 42f90a5 |
| `C_x_pc10` | C | b̄ 0.0078 | 19.6 | 1.2e-85 | 2.6e-85 | yes | 9.3e-85 | yes | b61d251 |
| `C_x_pc5` | C | b̄ 0.00957 | 24.1 | 5.9e-129 | 1.4e-128 | yes | 5e-128 | yes | b61d251 |
| `E_x_delist_0` | E | slope 0.00261 | 2.81 | 0.0025 | 0.003 | yes | 0.011 | yes | 1fa1d1a |
| `E_x_delist_m100` | E | slope 0.00262 | 2.81 | 0.0025 | 0.003 | yes | 0.011 | yes | 1fa1d1a |
| `E_x_hp_replication` | E | slope 0.00354 | 4.34 | 7.2e-06 | 1.2e-05 | yes | 4.4e-05 | yes | fa5af5f |
| `E_x_idiosyncratic` | E | slope 0.00163 | 1.81 | 0.035 | 0.037 | yes | 0.13 | no | fa5af5f |
| `E_x_nearest5` | E | slope 0.00338 | 4 | 3.1e-05 | 5e-05 | yes | 0.00018 | yes | 1fa1d1a |
| `E_x_perm_matched` | E | t (observed) 2.81 |  | 0.35 | 0.35 | no | 1 | no | fa5af5f |
| `E_x_portfolios` | E | alpha 0.0114 | 2.89 | 0.0019 | 0.0026 | yes | 0.0094 | yes | fa5af5f |
| `E_x_stale_y3` | E | slope 0.00208 | 2.24 | 0.013 | 0.014 | yes | 0.05 | yes | 1fa1d1a |

Rejected at q = 0.1: BH 18 of 19, BY 17 of 19.
