# D_horse_race_table (diagnostic): every estimator against LW nonlinear shrinkage

Annualised out-of-sample SD of the unconstrained GMV portfolio (21-day rebalancing), and Δ = log variance minus that of LW-NL with the LW (2011) prewhitened-HAC t; Holm at 5% (two-sided) across the estimators of each configuration and period. Development = before 2018-12-01, test = after.

## primary, test (1840 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 20.88% | +1.0661 | 16.03 | reject |
| lw_identity | 13.29% | +0.1634 | 6.02 | reject |
| constcorr | 13.62% | +0.2118 | 6.53 | reject |
| clip | 13.04% | +0.1253 | 3.76 | reject |
| lwnl | 12.25% |  |  |  |
| industry | 13.76% | +0.2319 | 6.95 | reject |
| text | 13.89% | +0.2507 | 6.93 | reject |
| bow_raw | 13.57% | +0.2041 | 4.60 | reject |
| text_val | 13.38% | +0.1762 | 5.62 | reject |
| precond | 13.30% | +0.1640 | 4.26 | reject |
| ff6 | 14.68% | +0.3615 | 6.25 | reject |
| ff6_text | 12.12% | -0.0212 | -1.69 |  |
| pca5 | 12.92% | +0.1057 | 1.41 |  |
| placebo | 13.62% | +0.2118 | 6.53 | reject |

## primary, dev (1616 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 13.11% | +1.0412 | 16.34 | reject |
| lw_identity | 8.49% | +0.1739 | 5.61 | reject |
| constcorr | 8.58% | +0.1933 | 8.27 | reject |
| clip | 8.41% | +0.1543 | 6.49 | reject |
| lwnl | 7.79% |  |  |  |
| industry | 8.59% | +0.1955 | 7.88 | reject |
| text | 8.70% | +0.2219 | 8.62 | reject |
| bow_raw | 8.60% | +0.1993 | 7.73 | reject |
| text_val | 8.38% | +0.1474 | 7.61 | reject |
| precond | 8.33% | +0.1346 | 8.16 | reject |
| ff6 | 9.59% | +0.4157 | 8.87 | reject |
| ff6_text | 7.61% | -0.0456 | -3.27 | reject |
| pca5 | 8.19% | +0.1008 | 2.78 | reject |
| placebo | 8.58% | +0.1933 | 8.26 | reject |

## primary, full (3456 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 17.67% | +1.0594 | 20.47 | reject |
| lw_identity | 11.31% | +0.1665 | 7.69 | reject |
| constcorr | 11.54% | +0.2075 | 8.23 | reject |
| clip | 11.12% | +0.1329 | 5.07 | reject |
| lwnl | 10.40% |  |  |  |
| industry | 11.63% | +0.2230 | 8.71 | reject |
| text | 11.75% | +0.2438 | 8.70 | reject |
| bow_raw | 11.52% | +0.2034 | 5.89 | reject |
| text_val | 11.32% | +0.1688 | 7.02 | reject |
| precond | 11.25% | +0.1565 | 5.35 | reject |
| ff6 | 12.56% | +0.3763 | 8.42 | reject |
| ff6_text | 10.26% | -0.0274 | -2.79 | reject |
| pca5 | 10.96% | +0.1044 | 1.85 |  |
| placebo | 11.54% | +0.2075 | 8.23 | reject |

## n1000, test (1840 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 22.85% | +1.5058 | 8.58 | reject |
| lw_identity | 11.00% | +0.0440 | 1.52 |  |
| constcorr | 11.77% | +0.1792 | 4.00 | reject |
| clip | 11.12% | +0.0649 | 0.62 |  |
| lwnl | 10.76% |  |  |  |
| industry | 11.76% | +0.1777 | 4.69 | reject |
| text | 11.82% | +0.1873 | 3.67 | reject |
| bow_raw | 11.90% | +0.2005 | 4.30 | reject |
| text_val | 11.84% | +0.1903 | 4.23 | reject |
| precond | 11.62% | +0.1536 | 4.39 | reject |
| ff6 | 13.29% | +0.4219 | 2.74 | reject |
| ff6_text | 10.47% | -0.0541 | -1.48 |  |
| pca5 | 11.50% | +0.1320 | 0.86 |  |
| placebo | 11.77% | +0.1792 | 4.00 | reject |

## n1000, dev (1616 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 14.00% | +1.4304 | 21.35 | reject |
| lw_identity | 6.85% | -0.0004 | -0.02 |  |
| constcorr | 7.30% | +0.1265 | 5.99 | reject |
| clip | 7.36% | +0.1443 | 7.96 | reject |
| lwnl | 6.85% |  |  |  |
| industry | 7.26% | +0.1173 | 4.67 | reject |
| text | 7.39% | +0.1511 | 6.06 | reject |
| bow_raw | 7.30% | +0.1263 | 4.59 | reject |
| text_val | 7.37% | +0.1462 | 6.26 | reject |
| precond | 7.35% | +0.1412 | 7.66 | reject |
| ff6 | 9.01% | +0.5482 | 10.45 | reject |
| ff6_text | 6.69% | -0.0475 | -3.44 | reject |
| pca5 | 7.38% | +0.1482 | 4.72 | reject |
| placebo | 7.30% | +0.1264 | 5.99 | reject |

## n1000, full (3456 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 19.22% | +1.4864 | 11.41 | reject |
| lw_identity | 9.29% | +0.0325 | 1.40 |  |
| constcorr | 9.93% | +0.1657 | 4.81 | reject |
| clip | 9.55% | +0.0864 | 1.10 |  |
| lwnl | 9.14% |  |  |  |
| industry | 9.92% | +0.1623 | 5.48 | reject |
| text | 9.99% | +0.1781 | 4.61 | reject |
| bow_raw | 10.01% | +0.1818 | 4.95 | reject |
| text_val | 10.00% | +0.1791 | 5.25 | reject |
| precond | 9.86% | +0.1505 | 5.72 | reject |
| ff6 | 11.49% | +0.4572 | 3.98 | reject |
| ff6_text | 8.91% | -0.0522 | -1.90 |  |
| pca5 | 9.79% | +0.1366 | 1.20 |  |
| placebo | 9.93% | +0.1658 | 4.81 | reject |

## t504, test (1840 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 20.81% | +0.0621 | 4.89 | reject |
| sample | 115.88% | +3.4967 | 24.15 | reject |
| lw_identity | 14.16% | -0.7072 | -7.78 | reject |
| constcorr | 13.67% | -0.7786 | -10.07 | reject |
| clip | 13.55% | -0.7951 | -12.55 | reject |
| lwnl | 20.17% |  |  |  |
| industry | 13.89% | -0.7458 | -9.78 | reject |
| text | 13.99% | -0.7321 | -9.25 | reject |
| bow_raw | 13.86% | -0.7498 | -9.70 | reject |
| text_val | 12.85% | -0.9016 | -11.89 | reject |
| precond | 41.12% | +1.4245 | 11.09 | reject |
| ff6 | 16.20% | -0.4381 | -6.72 | reject |
| ff6_text | 12.14% | -1.0150 | -16.64 | reject |
| pca5 | 14.31% | -0.6857 | -8.26 | reject |
| placebo | 13.66% | -0.7787 | -10.08 | reject |

## t504, dev (1469 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 13.17% | +0.0695 | 7.30 | reject |
| sample | 85.68% | +3.8155 | 34.72 | reject |
| lw_identity | 10.39% | -0.4042 | -6.17 | reject |
| constcorr | 9.64% | -0.5544 | -7.99 | reject |
| clip | 9.07% | -0.6746 | -11.16 | reject |
| lwnl | 12.72% |  |  |  |
| industry | 9.74% | -0.5333 | -7.62 | reject |
| text | 9.81% | -0.5182 | -7.69 | reject |
| bow_raw | 9.73% | -0.5359 | -7.90 | reject |
| text_val | 9.01% | -0.6892 | -11.83 | reject |
| precond | 25.56% | +1.3961 | 16.57 | reject |
| ff6 | 10.96% | -0.2963 | -5.01 | reject |
| ff6_text | 8.24% | -0.8669 | -13.99 | reject |
| pca5 | 9.27% | -0.6318 | -11.31 | reject |
| placebo | 9.64% | -0.5543 | -7.99 | reject |

## t504, full (3309 days)

| estimator | ann. SD | Δ vs LW-NL | t | Holm 5% |
|---|---|---|---|---|
| ew | 17.82% | +0.0639 | 6.30 | reject |
| sample | 103.57% | +3.5838 | 30.63 | reject |
| lw_identity | 12.63% | -0.6250 | -8.38 | reject |
| constcorr | 12.05% | -0.7193 | -11.18 | reject |
| clip | 11.78% | -0.7643 | -14.70 | reject |
| lwnl | 17.26% |  |  |  |
| industry | 12.22% | -0.6899 | -10.88 | reject |
| text | 12.31% | -0.6758 | -10.31 | reject |
| bow_raw | 12.20% | -0.6935 | -10.82 | reject |
| text_val | 11.31% | -0.8458 | -13.60 | reject |
| precond | 35.08% | +1.4183 | 13.96 | reject |
| ff6 | 14.12% | -0.4011 | -7.61 | reject |
| ff6_text | 10.59% | -0.9770 | -19.42 | reject |
| pca5 | 12.34% | -0.6717 | -10.25 | reject |
| placebo | 12.05% | -0.7194 | -11.18 | reject |

## Weights and fit (per rebalance means; test period, primary)

| estimator | turnover | gross leverage | max |w| | bias ratio | median a | median b | share b = 0 | median δ |
|---|---|---|---|---|---|---|---|---|
| bow_raw | 3.64 | 6.73 | 0.168 | 13.04 | 0.211 | 0.735 | 0.00 | 0.20 |
| clip | 1.48 | 4.00 | 0.105 | 6.78 |  |  |  |  |
| constcorr | 3.27 | 6.19 | 0.165 | 11.77 | 0.289 | 0.000 | 1.00 | 0.19 |
| ew | 0.05 | 1.00 | 0.002 |  |  |  |  |  |
| ff6 | 0.93 | 2.97 | 0.060 | 16.55 |  |  |  |  |
| ff6_text | 2.16 | 4.81 | 0.121 | 6.73 | 0.018 | 0.207 | 0.00 | 0.45 |
| industry | 3.44 | 6.43 | 0.168 | 12.62 | 0.285 | 0.155 | 0.00 | 0.20 |
| lw_identity | 3.55 | 6.35 | 0.147 | 21.40 |  |  |  |  |
| lwnl | 1.91 | 4.40 | 0.124 | 5.96 |  |  |  |  |
| pca5 | 1.36 | 3.87 | 0.087 | 8.34 |  |  |  |  |
| placebo | 3.27 | 6.19 | 0.165 | 11.77 | 0.289 | 0.000 | 0.59 | 0.19 |
| precond | 2.29 | 5.19 | 0.154 | 6.28 |  |  |  |  |
| text | 3.68 | 6.80 | 0.172 | 14.01 | 0.290 | 0.267 | 0.00 | 0.20 |
| text_val | 2.55 | 4.92 | 0.145 | 7.62 |  |  |  | 0.55 |
