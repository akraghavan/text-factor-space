# Quantifying How 10-K Business Similarity Explains Factor-Adjusted Return Comovement: Results

Do 10-K business descriptions define economic neighbours that industry codes miss, and what are those neighbours worth for returns and risk?

_Abhinav Raghavan, 8 Oct 2026._ The pre-registration was frozen at `01cb5cc` (30 Sep) before any registered statistic was computed. Every number below is a `src/runner.py` record in `runs.log`, tied to a commit. Full tables are in `analysis/output/`; the exploratory family is in `analysis/output/exploratory/README.md` and the horse race in `analysis/output/d_horse_race/README.md`.

## Question, data and sample

Firms that describe similar businesses in Item 1 of their 10-K should share shocks that industry codes only partly capture. The project asks three questions:
- **Q1:** Does text similarity explain the return comovement left after the Fama–French five factors plus momentum (FF6), beyond SIC? (Elements B, C.)
- **Q2:** Does a covariance matrix built on text give lower-risk portfolios? (D.)
- **Q3:** Do a firm's text peers' past returns predict its next-month return after Hoberg & Phillips (2018, HP) published the effect? (E.)

**Data.** 61,589 10-Ks, Jun 2011 – Sep 2026, from EDGAR (Item 1 over 300 words for 99.2%; 97 of 100 hand-checked spans correct); CRSP CIZ monthly and daily returns with delistings; Compustat book equity via CCM; Fama–French factors; HP's TNIC-3 (to FY2023). **Universe**, each month: US common stocks on NYSE/AMEX/Nasdaq, one security per company, SPACs excluded, with a 10-K filed in the prior 15 months (3,200–3,900 firms). **Point in time**: a 10-K counts from the month after filing, book equity from the July after the fiscal year, size and price from t−1.

## Method (details: `docs/SPEC.md`, `docs/PREREG.md`)

**A.** Two similarity measures: *dense* (cosine of name-masked bge-small-en-v1.5 embeddings of Item 1) and *BoW* (HP's binary noun vectors, corrected for document length). Peers are pairs above the cut that matches SIC-3's density (2–3% of pairs). Both separate same-SIC-3 pairs (AUC 0.88, 0.91), yet most links cross SIC-3 (66%, 57%).

**B.** Each July 2014–2025, the 500 largest firms' daily FF6 residuals over three years (betas from earlier data). The 267 residual-correlation eigenvectors above a circular-shift noise edge are tested for alignment u′G̃u with the dense similarity net of same-SIC-3 (1,000 firm relabellings); statistic: the share with p < 0.05.

**C (H1).** Each month Jul 2012 – Mar 2026 (165), the 1,000 largest firms' 499,500 pairs: the Fisher z of their within-month daily FF6-residual correlation (out-of-sample betas) on standardised dense similarity and 19 controls (same SIC-1..4, last year's correlation, rank distances in size, B/M, momentum and illiquidity, six beta differences, fiscal year-end, exchange, length). Fama–MacBeth b̄, Newey–West(4) t.

**D.** Fifteen correlation estimators each feed an unconstrained minimum-variance (GMV) portfolio of the 500 largest firms (252-day windows, rebalanced every 21 trading days from July 2012; 3,456 out-of-sample days). The text estimator shrinks the sample correlation towards T(a, b) = a·11ᵀ + b·G + (1−a−b)·I with G the dense similarity ((a, b) fitted on the prior year, Schäfer–Strimmer intensity); b = 0 is the constant-correlation target. Benchmark: Ledoit–Wolf (2020) analytical nonlinear shrinkage (LW-NL). Test: Δ = log variance difference over Dec 2018 – Mar 2026, Ledoit–Wolf (2011) prewhitened-HAC standard error, block bootstrap beside it.

**E (H3).** PEERMOM = equal-weighted 12-month return of a firm's BoW peers. Fama–MacBeth of next-month excess returns on PEERMOM and controls (size, B/M, r₋₁, own 12–2 momentum, FF-48, SIC-3 and TNIC-3 peer momentum), winsorised and z-scored monthly; price ≥ $1, complete cases. Tuned on Jul 2012 – Nov 2018; **test period Dec 2018 – Jun 2026** (91 months, after HP's publication), untouched until the freeze.

## Registered results

| | Statistic | Estimate | t | one-sided p | Decision |
|---|---|---|---|---|---|
| **H1** (C) | b̄ per SD of dense similarity (Fisher z) | 0.0119 | 24.7 (EWC 21.7) | 1.5e-134 | supported; Holm threshold 0.025 |
| **H3** (E) | PEERMOM slope, test period (%/month per SD) | 0.262 | 2.81 (EWC 2.98) | 0.0025 | supported; Holm threshold 0.05 |
| Holm {H1, H3} at 5% | | | | | both nulls rejected |
| **B primary** | share of 267 modes aligned beyond SIC-3 | 95.5% (255) | | < 1e-300 | text structure beyond SIC-3 |

H3 beside it: the development period gives 0.175 (t 3.22), and test minus development is +0.087 (t 0.80), so there is no decay. For scale, H1's same-SIC-4 pair (versus no shared SIC digit) adds 0.118 in z.

## Q2: the covariance horse race (D, exploratory; test period, 1,840 days)

| Test (\* = added after the freeze) | Δ log variance | 95% CI | t | one-sided p (Δ < 0) | bootstrap p |
|---|---|---|---|---|---|
| `D_x_text_vs_lwnl`: dense text target vs LW-NL | **+0.251** | [+0.180, +0.322] | 6.93 | ≈ 1 | 1.00 |
| `D_x_text_vs_constcorr`\*: b > 0 vs b = 0 | +0.039 | [+0.008, +0.070] | 2.48 | 0.99 | 1.00 |
| `D_x_text_vs_placebo`\*: real G vs relabelled G | +0.039 | [+0.008, +0.070] | 2.49 | 0.99 | 1.00 |
| `D_x_ff6text_vs_ff6cc`\*: FF6 residuals shrunk to text vs to constant correlation | +0.001 | [−0.023, +0.025] | 0.09 | 0.54 | 0.56 |

Annualised out-of-sample SD of each GMV portfolio, test period. The t is against LW-NL; † marks estimators not significantly different from LW-NL after Holm.

| | 1/N | LW identity | const. corr. | RMT clip | **LW-NL** | SIC-3 target | **dense text** | raw-BoW text | text, validated δ | text-preconditioned NL | FF6 | FF6 + text residuals | FF6 + const.-corr. residuals | PCA-5 | placebo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| N = 500 | 20.9% | 13.3% | 13.6% | 13.0% | **12.25%** | 13.8% | **13.9%** | 13.6% | 13.4% | 13.3% | 14.7% | 12.12%† (t −1.7) | 12.12%† (t −1.5) | 12.9%† | 13.6% |
| N = 1,000 | 22.9% | 11.0%† | 11.8% | 11.1%† | **10.76%** | 11.8% | **11.8%** | 11.9% | 11.8% | 11.6% | 13.3% | 10.47%† (t −1.5) | 10.50%† (t −1.1) | 11.5%† | 11.8% |

The fitted text loading b̂ is positive at every rebalance (median 0.27, intensity δ ≈ 0.20). Even so, the GMV portfolio built on it is 13% more volatile than LW-NL's, and 2% more than the constant-correlation target's. The development period (Jul 2012 – Nov 2018) gives the same ranking: LW-NL 7.8%, text 8.7%. The only estimators below LW-NL are FF6 with a shrunk residual correlation, and the target doesn't matter. Text-shrunk and constant-correlation-shrunk residuals give 12.12% each (D29: Δ +0.001, 95% CI ±0.024, t 0.09), against 14.7% with diagonal residuals. The gain over LW-NL (significant in development, t −3.3 and −4.6; not in test, t −1.7 and −1.5) comes from the factors plus shrinking the residual correlations, not from text.

## Exploratory results: m = 45; BH (q = 0.10) rejects 34, BY 32

Each spec contributes the one-sided p in its registered direction; the placebo, with no predicted sign, contributes its two-sided p. 38 specs were in the frozen registry; 7 were added after the freeze, 2 on 1 Oct and 5 on 8 Oct (PREREG change log).

- **B (6 of 6 rejected).**
  - Aligned share: SIC-3 itself 99.3%; raw dense 100%; dense net of SIC-3 with T = 1,008, 92.8%.
  - **Dense net of nested SIC-1..4: 90.3%**, and of FF-48: 90.6%.
  - The residual modes overlap the top text eigenvectors 6.2 times more than random.
- **C (14 of 14).** b̄ ranges over 0.0078–0.0194 per SD, with t 8.8–39.
  - Variants: BoW null-corrected and raw; missing B/M kept; FF6 + 5 or 10 PCs (0.0096, 0.0078); Dimson residuals; Compustat `sich`.
  - The dense *binary* link: linked pairs have z higher by 0.083.
  - Sample splits: 12-month windows; pre- and post-FY2020 (0.0112, 0.0132, difference t 1.8); and post-Sep-2023, after the encoder's release (0.0128, t 8.8).
  - Inference: MRQAP-DSP, where every year's t of 26–106 exceeds the largest relabelled t of 4.6; and dyadic-robust errors (t 37.6, 2,161 firm clusters).
  - Diagnostic: s̃ adds 0.0018 to the in-sample R² and 0.0016 out of sample. The top percentile of similarity averages z 0.25 against 0.005 at the median.
- **D (0 of 4).** See above.
- **E (14 of 21 by BH, 12 by BY).**
  - **Stratified substitution** (each peer replaced by a random firm from its FF-48 industry × NYSE size tercile): **p = 0.001**. No draw reached t = 2.81, against a mean of 0.12. So the chosen peers matter beyond their industry and size composition. The null holds FF-48, which is coarser than SIC-3, so this means text picks the right peers within broad industries; it does not show links that SIC misses (see the visibility splits below).
  - Rejected: similarity weights (0.25, t 3.0), nearest-5 peers (0.34, t 4.0), delisting δ = 0 / −100% (t 2.81), a three-year-old network (t 2.24), peers in both text and SIC-3 (t 2.78), post-Sep-2023 (t 2.40), `sich` (0.54, t 5.07), R(t−6, t−1) (t 2.32), the quintile EW FF5+UMD alpha (1.14%/month, t 2.89), and HP's own TNIC-3 peers on 2012–2026 (raw slope 0.016, t 4.9, against HP's 0.008, t 4.36; quintile FF3 alpha 1.42%/month, t 3.37, against HP's 1.7%, t 3.30).
  - BH only: firms above the NYSE 20th percentile (0.19, t 1.79) and idiosyncratic peer returns (t 1.81).
  - Not rejected: R(t−12, t−7) (t −0.12); the Grundy–Martin peer R(t−12, t−2) (t 0.73, while peer r(t−1) has t 4.16); text-only, SIC-only and dense-only peers (t 1.12, 0.02, 1.23); the R(t−24, t−13) placebo (two-sided p 0.15, as it should be); the past-return-matched null (p 0.36).
- **Romano–Wolf**, size-calibrated so the simulated FWER is ≤ 5% (D30). Each series is standardised by its own NW SE.
  - C (block 8, nominal size 0.01, simulated FWER 3.7%): all 8 slope series survive.
  - E (block 4, size 0.015, simulated FWER 4.6%): 3 of 15 survive, namely nearest-5, similarity weights and `sich` (every E series with t ≥ 3). The headline E spec (t 2.81) and the text-and-SIC-3 split (t 2.78) do not.
  - Context: at nominal 5% (block 12, simulated FWER 18%) E had 8 of 15; with raw slopes, 1 of 15.
- **Event time (diagnostic).** The quintile long-short earns +4.0% over months 1–12 and gives back 10.0% over months 13–24. Turnover is 0.56 a month, the break-even round-trip cost 2.0% of value traded, and the maximum drawdown −30% (April 2020: −19%).

## Caveats

- **B's registered 95.5% means "beyond SIC-3".** The "beyond industry" number is the nested SIC-1..4 version, 90.3%. B's binomial test treats modes from 12 overlapping windows as independent, so quote the share, not the p.
- **H3 misses the Harvey–Liu–Zhu t > 3 hurdle** (t 2.81), though it passes its pre-registered Holm threshold. **E is complete-case**: of 214,916 test firm-months with a PEERMOM, 185,920 have every control. **TNIC-3 stops at FY2023** and is carried forward for Jul 2025 – Jun 2026.
- **E is small-stock, short-horizon and fragile across variants.**
  - Value-weighted alphas are insignificant (|t| < 0.6 with UMD). Above the NYSE 20th percentile the slope falls to 0.19 (t 1.79).
  - The signal sits in the peers' most recent month.
  - **It lives in peers that are both text- and SIC-3-linked** (t 2.78). Text-only peers give t 1.12, SIC-only 0.02, and dense-only (outside SIC-3 and TNIC-3) 1.23. In E, text works as a filter on industry peers, not a source of new links.
  - Under family-wise control E is fragile. In the size-calibrated Romano–Wolf (simulated FWER ≤ 5%), 3 of 15 slope series survive, and the headline is not among them.
- **The two permutation nulls answer different questions.**
  - The matched null (p 0.36) keeps each peer's past-return decile, so by construction it keeps most of PEERMOM (correlation 0.53). It shows that which firm sits within a decile does not matter.
  - The stratified null (p 0.001) keeps FF-48 industry and size and breaks the link. It shows the chosen peers matter within broad industries. FF-48 is coarser than SIC-3, and the signal sits in text-and-SIC-3 peers, so it is not evidence of links that SIC misses.
- **Romano–Wolf.**
  - `arch`'s StepM does not studentise in arch 8.0.0, so the series are divided by their own Newey–West SEs before it (D28), with the SE fixed across draws as in Hansen's (2005) SPA.
  - At nominal 5% that is liberal at our sizes (simulated FWER 14% for C, 18% for E; about 5% at T = 1,000).
  - So the nominal size is calibrated down to a simulated FWER ≤ 5% (D30: C 0.01, E 0.015). The simulation uses independent series, which is conservative for our correlated variants.
- **D.**
  - The T = 504 robustness configuration has p/n = 0.994, where LW (2020) nonlinear shrinkage degenerates (simulated GMV variance 12 times the oracle), so its LW-NL rows are uninformative. The primary (p/n ≈ 2) and N = 1,000 (≈ 4) configurations are unaffected.
  - Mean bias ratios are dominated by March 2020; the medians are 3.0 for LW-NL and 6.9 for text, the usual GMV optimisation bias.
  - Not built (D20): a single-index target (FF6 subsumes it), RIE (same class as LW-NL), a TNIC target (not PSD; ends FY2023), a GICS/Barra model (no point-in-time GICS), long-only GMV, and factor-neutral or random-portfolio bias tests.
- **Process.** The runner's guard was changed after the freeze, before any registered run (it skips the `entry` field and requires a committed tree); no specification changed. `runs.log`'s `dirty` flag counts `runs.log` and untracked outputs, so it does not mean the code differed from the commit. Seven exploratory specs added after the freeze are counted in m. The nine FM specs re-run for Romano–Wolf reproduced their logged numbers exactly.
- **Not done (D27):** input–output customer/supplier momentum (no data), analyst co-coverage (no I/B/E/S), and net-of-cost alphas with real spreads (a break-even cost is given instead).

## What it means

**Q1: yes, robustly.**
- Firms whose business descriptions are more alike co-move more after FF6. One SD of similarity adds about a tenth of what sharing a four-digit SIC adds, net of every SIC level, last year's comovement and style and beta differences.
- It holds under every inference method (Fama–MacBeth, MRQAP relabelling, dyadic-robust errors), every network, every subperiod, and the encoder's own post-release window.
- Ten statistical factors absorb a third of it.
- Nine in ten of the residual directions that stand out from noise line up with text beyond every SIC level.

**Q2: no, at least not as a correlation target.**
- Text knows who co-moves (Q1), but shrinking towards it makes the minimum-variance portfolio about 13% *more* volatile than nonlinear shrinkage (95% CI +9% to +17% in volatility), and slightly worse than a constant correlation.
- LW-NL already captures the large eigen-directions. A target that redistributes correlation towards text pairs adds estimation noise that the GMV weights amplify.
- It doesn't help in the factor residuals either: FF6 residual correlations shrunk to text and to a constant correlation give the same volatility (12.12% each, t 0.09).

**Q3: yes, after publication, as text picking the right peers within industries.**
- HP's text-peer momentum replicates on 2012–2026 at about their magnitude, and its post-publication slope is no smaller.
- The stratified null shows the chosen peers matter beyond their FF-48 industry and size. But the signal lives in peers that are both text- and SIC-3-linked (t 2.78; text-only 1.12, SIC-only 0.02, dense-only 1.23).
- So in E, text selects the right neighbours within industries rather than finding links that SIC misses. That contrasts with Q1, where text explains comovement well beyond every SIC level.
- But it is concentrated in small firms and in the peers' last month, short of t > 3, and fragile across variants under family-wise control.
- Read it as a replication and extension of a diffusion effect, not a deployable signal.
