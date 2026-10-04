# Results: do 10-K business descriptions define economic neighbours?

_Abhinav Raghavan, 2 Oct 2026. Pre-registration frozen at `d1df5c7` (30 Sep) before any registered statistic was computed; every number is a `src/runner.py` record in `runs.log`, tied to a commit. Tables: `analysis/output/`._

## Question, data and sample

Firms that describe similar businesses in Item 1 of their 10-K should share shocks that industry codes only partly capture. **Q1:** does text similarity explain return comovement left after Fama–French five factors plus momentum (FF6), beyond SIC (Elements B, C)? **Q3:** do text peers' past returns predict a firm's next-month return after Hoberg & Phillips (2018, HP) published it (Element E)? Q2, text-based covariance estimation (D), was not built.

**Data.** 61,589 10-Ks, Jun 2011 – Sep 2026 (EDGAR; Item 1 over 300 words for 99.2%, 97/100 hand-checked spans correct); CRSP CIZ monthly and daily returns with delistings, Compustat book equity via CCM; Fama–French factors; HP's TNIC-3 (to FY2023). **Universe** each month: US common stocks on NYSE/AMEX/Nasdaq, one security per company, SPACs excluded, with a 10-K filed in the prior 15 months (3,200–3,900 firms). Point in time: a 10-K counts from the month after filing, book equity from the July after the fiscal year, size and price from t−1.

## Method

**A (text networks).** *Dense*: cosine similarity of sentence embeddings (bge-small-en-v1.5) of Item 1, own name masked. *BoW*: HP's binary noun vectors, corrected for the mechanical effect of document length. Peers = pairs above the cut-off that matches SIC-3's density (2–3% of pairs). Both separate same-SIC-3 pairs (AUC 0.88, 0.91), yet most peer links cross SIC-3 (66%, 57%); BoW peers overlap TNIC-3 (Jaccard 0.65).

**B (residual factor space).** Each July 2014–2025, the 500 largest firms' daily FF6 residuals over three years (betas always from earlier data). Residual-correlation eigenvectors above a circular-shift noise edge: 267 modes. Alignment u′G̃u with G̃ = dense similarity net of same-SIC-3, p from 1,000 firm relabellings; statistic: share of modes with p < 0.05, binomial test against 5%.

**C (pairwise comovement; H1).** Each month Jul 2012 – Mar 2026 (165), the 1,000 largest firms' 499,500 pairs: Fisher z of the within-month correlation of daily FF6 residuals (out-of-sample betas), regressed on standardised dense similarity and 19 controls (same SIC-1..4, last year's correlation, rank distances in size, B/M, momentum, illiquidity, six beta differences, fiscal year-end, exchange, length). Statistic: Fama–MacBeth b̄, Newey–West(4) t.

**E (text-peer momentum; H3).** PEERMOM = equal-weighted 12-month return of a firm's BoW peers. Fama–MacBeth of next-month excess returns on PEERMOM and controls (size, B/M, r₋₁, own 12–2 momentum, FF-48, SIC-3 and TNIC-3 peer momentum), winsorised and z-scored monthly; price ≥ $1, complete cases, missing performance-delisting returns imputed. Tuned on Jul 2012 – Nov 2018; **test period Dec 2018 – Jun 2026** (91 months, post-publication), untouched until the freeze. Statistic: test-period slope, NW(3) t.

## Registered results

| | Statistic | Estimate | t | one-sided p | Decision |
|---|---|---|---|---|---|
| **H1** (C) | b̄ per SD of dense similarity (Fisher z) | 0.0119 | 24.7 (EWC 21.7) | 1.5e-134 | supported; Holm threshold 0.025 |
| **H3** (E) | PEERMOM slope, test period (%/month per SD) | 0.262 | 2.81 (EWC 2.98) | 0.0025 | supported; Holm threshold 0.05 |
| Holm {H1, H3} at 5% | | | | | both nulls rejected |
| **B primary** | share of 267 modes aligned beyond SIC-3 | 95.5% (255) | | < 1e-300 | text structure beyond SIC-3 |

H3's development period: 0.175 (t 3.22); test minus development +0.087 (t 0.80), so no decay; TNIC-3 momentum 0.297 (t 2.51) alongside. Scale for H1: same SIC-4 vs no shared SIC digit adds 0.118 in total.

## Exploratory results (m = 19; BH at q = 0.10, BY beside it)

One-sided p of each spec's registered statistic; q = BH / BY adjusted p. \* added after the freeze (PREREG change log). Full table: `analysis/output/exploratory/`.

| Spec | What changes | Estimate | t | p | BH q | BY q |
|---|---|---|---|---|---|---|
| `B_x_sic3_share` | G̃ = SIC-3 membership itself | 99.3% aligned | | ≈0 | ≈0 | ≈0 |
| `B_x_raw_dense_share` | G̃ = dense, no industry removed | 100% | | ≈0 | ≈0 | ≈0 |
| `B_x_nested_sic`\* | dense minus SIC-1, -2, -3, -4 | **90.3%** | | 7e-279 | 3e-278 | 1e-277 |
| `B_x_ff48_share`\* | dense minus FF-48 industry | 90.6% | | 4e-281 | 2e-280 | 8e-280 |
| `B_x_subspace_overlap` | modes vs top text eigenvectors | 6.2× random | | 4e-23 | 7e-23 | 2e-22 |
| `C_x_bow_null` | BoW network instead of dense | b̄ 0.0179 | 24.6 | 2e-134 | 5e-134 | 2e-133 |
| `C_x_missing_bm_indicator` | keep pairs with missing B/M | 0.0119 | 25.4 | 1e-142 | 4e-142 | 1e-141 |
| `C_x_pc5` | FF6 + 5 statistical factors | 0.0096 | 24.1 | 6e-129 | 1e-128 | 5e-128 |
| `C_x_pc10` | FF6 + 10 statistical factors | 0.0078 | 19.6 | 1e-85 | 3e-85 | 9e-85 |
| `C_x_mrqap` | MRQAP-DSP, annual, 999 relabellings | mean b 0.0110 | perm. | 0.001 (floor) | 0.0015 | 0.005 |
| `C_x_dyadic` | pooled OLS, dyadic-robust SE | 0.0122 | 37.6 | 1e-238 | 4e-238 | 1e-237 |
| `E_x_delist_0` / `_m100` | delisting δ = 0 / −100% | 0.261 / 0.262 | 2.81 | 0.0025 | 0.003 | 0.011 |
| `E_x_nearest5` | each firm's 5 nearest text peers | 0.338 | 4.00 | 3e-5 | 5e-5 | 2e-4 |
| `E_x_stale_y3` | peers from the network 3 years earlier | 0.208 | 2.24 | 0.013 | 0.014 | 0.050 |
| `E_x_idiosyncratic` | peers' factor-adjusted returns | 0.163 | 1.81 | 0.035 | 0.037 | 0.13 (no) |
| `E_x_portfolios` | quintile EW, ≥ $1, FF5+UMD alpha | 1.14%/mo | 2.89 | 0.0019 | 0.0026 | 0.0094 |
| `E_x_hp_replication` | HP's TNIC-3 peers, full period | 0.354 | 4.34 | 7e-6 | 1e-5 | 4e-5 |
| `E_x_perm_matched` | vs random peers from the true peers' return deciles | t 2.81 vs 2.70 | | **0.355** | 0.355 (no) | 1 (no) |

**BH rejects 18 of 19, BY 17.** MRQAP: each year's text t (26–106) exceeds the largest relabelled t (4.6). Dyadic t exceeds the FM t because it ignores time variation in the slope. Portfolios: decile EW alpha 1.87%/month (t 4.14); value-weighted alphas are insignificant (FF3 t ≤ 1.24; with UMD |t| < 0.6); price ≥ $5 weakens the EW quintile (t 1.53) but not the EW decile (1.35%/month, t 3.14). HP replication: quintile EW FF3 alpha 1.42%/month (t 3.37) vs HP's 1.7% (t 3.30); raw slope 0.0163 (t 4.94) vs HP's 0.008 (t 4.36); our network on the same rows t 5.13.

**Not run** (registered, never executed, not in m; 21): B with T = 1,008; C with raw BoW, binary network, 12-month windows, pre/post FY2020, Dimson, Compustat SIC; E with similarity weights, four horizon and four visibility splits, stratified-substitution permutation, post-Sep-2023, Compustat SIC; D.

## Caveats

- **B's registered 95.5% means "beyond SIC-3".** Sector-level similarity (SIC-2, SIC-1) still counts there. The "beyond industry" number is the nested SIC-1..4 version: 90.3%.
- **B's binomial test is optimistic.** Its 267 modes come from 12 overlapping windows, not independent draws. Quote the share, not the p.
- **H3 misses the Harvey–Liu–Zhu t > 3 hurdle** (t 2.81), though it passes its pre-registered Holm threshold.
- **E is complete-case.** Of 214,916 test firm-months with a PEERMOM, 185,920 (86.5%) have every control; the losses are mostly B/M (19,472) and TNIC-3 (13,242).
- **TNIC-3 stops at FY2023.** It is carried forward for Jul 2025 – Jun 2026 (12 test months).
- **Runner change after the freeze, before any registered run.** The guard compared every field with its frozen copy, including the code entry frozen as "pending", so H1 and H3 could not run. It now skips the entry field and requires a committed tree (PREREG change log; SPEC D16). No specification changed.
- **`dirty` in `runs.log`.** It counts `runs.log` itself and untracked output folders, so it does not mean the code differed. B primary shows `dirty: true` for this reason alone; guarded runs required a clean tracked tree.
- **E lives in small stocks.** Value-weighted alphas are insignificant, while the EW decile survives a $5 price filter (t 3.14). So the effect sits in small, less-watched firms within equal-weighted sorts, not only in penny stocks. That fits slow diffusion, but it limits capacity.
- **The matched-peer null does not reject** (p 0.355). It replaces each peer with a random firm from the same past-return decile. That keeps the decile composition of the true peers' returns, so by construction it keeps most of PEERMOM (correlation 0.53) and does not test whether the link itself matters. Not rejecting means only that which firm sits within a decile doesn't matter beyond the decile. The pre-listed null that does test the link, stratified substitution, was not run: it replaces each peer with a random firm from the same FF-48 industry × NYSE size tercile, keeping industry and size composition and breaking only the tie to the specific text peers.
- **D was not built.** Q2 is unanswered.

## What it means

**Q1: text sees comovement that industry codes miss.**
- Firms whose descriptions are one standard deviation more alike co-move more, by about a tenth of what sharing a four-digit SIC adds. That is net of every SIC level, last year's comovement and style and beta differences.
- It survives Fama–MacBeth, MRQAP relabelling and dyadic-robust errors, and both text networks.
- Ten statistical factors absorb a third of it, so it is mostly not hidden macro exposure.
- Nine in ten of the residual directions that stand out from noise line up with text beyond every SIC level.

**Q3: text-peer momentum survived publication, but it is small and fragile.**
- HP's result replicates on 2012–2026 at about their magnitude, with no decay after their paper.
- It is an equal-weighted, small-stock effect just short of t > 3.
- Its content is the coarse past performance of a firm's true peers.
- Read it as replication and extension, not a deployable signal.

**Q2 (covariance) is open.**
