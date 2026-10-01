# Exploratory family: Benjamini–Hochberg and Benjamini–Yekutieli at q = 0.1

m = 13 exploratory specs run (`python src/runner.py count`). One-sided p-values from the latest `ok` runner record of each (`runs.log`; nothing re-estimated); q-values from `tfs_stats.multitest.bh` / `.by`. BY is valid under any dependence; BH assumes independence or positive dependence, which overlapping variants of the same test roughly satisfy.

| Spec | Element | Estimate | t | one-sided p | BH q | BH reject | BY q | BY reject | commit |
|---|---|---|---|---|---|---|---|---|---|
| `B_x_ff48_share` | B | aligned share 0.906 |  | 3.7e-281 | 1.6e-280 | yes | 5.1e-280 | yes | 7a2237b |
| `B_x_nested_sic` | B | aligned share 0.903 |  | 6.5e-279 | 2.1e-278 | yes | 6.7e-278 | yes | 7a2237b |
| `B_x_raw_dense_share` | B | aligned share 1 |  | 0 | 0 | yes | 0 | yes | 7a2237b |
| `B_x_sic3_share` | B | aligned share 0.993 |  | 0 | 0 | yes | 0 | yes | 7a2237b |
| `B_x_subspace_overlap` | B | overlap / random 6.15 |  | 3.6e-23 | 5.2e-23 | yes | 1.7e-22 | yes | 7a2237b |
| `C_x_bow_null` | C | b̄ 0.0179 | 24.6 | 2e-134 | 4.3e-134 | yes | 1.4e-133 | yes | b61d251 |
| `C_x_missing_bm_indicator` | C | b̄ 0.0119 | 25.4 | 1.2e-142 | 3.1e-142 | yes | 1e-141 | yes | b61d251 |
| `C_x_pc10` | C | b̄ 0.0078 | 19.6 | 1.2e-85 | 2e-85 | yes | 6.4e-85 | yes | b61d251 |
| `C_x_pc5` | C | b̄ 0.00957 | 24.1 | 5.9e-129 | 1.1e-128 | yes | 3.5e-128 | yes | b61d251 |
| `E_x_delist_0` | E | slope 0.00261 | 2.81 | 0.0025 | 0.0027 | yes | 0.0086 | yes | 1fa1d1a |
| `E_x_delist_m100` | E | slope 0.00262 | 2.81 | 0.0025 | 0.0027 | yes | 0.0086 | yes | 1fa1d1a |
| `E_x_nearest5` | E | slope 0.00338 | 4 | 3.1e-05 | 4.1e-05 | yes | 0.00013 | yes | 1fa1d1a |
| `E_x_stale_y3` | E | slope 0.00208 | 2.24 | 0.013 | 0.013 | yes | 0.04 | yes | 1fa1d1a |

Rejected at q = 0.1: BH 13 of 13, BY 13 of 13.
