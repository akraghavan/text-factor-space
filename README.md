# Quantifying How 10-K Business Similarity Explains Factor-Adjusted Return Comovement

Every US public company describes its products and markets in Item 1 of its annual 10-K. Firms that describe similar products compete for the same customers and face the same demand shocks, so the text should define an economic neighbourhood that fixed, coarse industry codes capture only partly. This project measures that neighbourhood from about 56,000 firm-year 10-Ks (2011–2026) and tests what it is worth for returns. It replicates the text-based industries and text-based industry momentum of Hoberg and Phillips and extends them in three ways: dense sentence embeddings compared head to head with their bag-of-words vectors, an out-of-sample test of text-peer momentum after its 2018 publication, and text similarity used as a structured prior for covariance estimation.

## Questions

| # | Question | Elements |
|---|---|---|
| Q1 | After the Fama–French five factors and momentum, does text similarity explain residual return comovement beyond SIC industry? | B, C |
| Q2 | Does a covariance matrix built on the text structure beat purely statistical estimators out of sample? | D |
| Q3 | Do a firm's text peers' returns predict its next-month return, and did that survive publication? | E |

Element A builds and validates the text representations used by all three. The full design, including inference and pitfalls, is in [`docs/SPEC.md`](docs/SPEC.md).

## Data

| Source | Content | Coverage |
|---|---|---|
| SEC EDGAR bulk `submissions.zip` | filing index, filing dates, primary documents | all filers |
| SEC EDGAR 10-K primary documents | Item 1 (Business) text | 61,589 10-Ks filed Jun 2011 – Sep 2026 |
| CRSP Stock v2 (CIZ), monthly and daily | returns (delisting returns included), market cap, SIC, exchange, share type | monthly 2009-01 – 2026-06; daily 2010-01 – 2026-03 |
| CRSP/Compustat Merged | gvkey–PERMNO links, CIK, GICS; annual fundamentals | full link history; FY2008 – FY2026 |
| Ken French data library | FF5 and momentum factors, daily and monthly | 1963 – 2026-08 |
| Hoberg–Phillips data library | TNIC-3 text-similarity network (benchmark) | 1988 – 2023 |

**Data are not included in this repository and are licensed separately.** CRSP and Compustat come from WRDS under an institutional licence and may not be redistributed; the EDGAR, Ken French and Hoberg–Phillips files are public and belong to their providers. [`docs/DATA.md`](docs/DATA.md) lists every WRDS query and download needed to rebuild `data/`.

**Universe.** US-incorporated operating common stock (`ShareType = NS`, `SecuritySubType = COM`, `USIncFlg = Y`, `IssuerType ∈ {ACOR, CORP}`, `ConditionalType ∈ {RW, NW}`; the CIZ equivalent of legacy share codes 10/11) on NYSE, NYSE American or Nasdaq: about 3,750–4,600 firms per year. Each 10-K is mapped CIK → gvkey → PERMNO using the primary CCM link valid on the filing date. Compustat keeps only a firm's current CIK, so firms whose CIK changed are dropped rather than mislinked (88.7% of 10-Ks map: 54,602 of 61,589; an earlier 92.3% was the pre-REIT-fix v0 universe).

## Methods

- **A. Text layer.** Hoberg–Phillips-style binary bag-of-words vectors and centred `bge-small-en-v1.5` embeddings; every network calibrated to the pair density of 3-digit SIC; validated against historical SIC and TNIC-3.
- **B. Factor space.** Eigenvalues of the FF5 + momentum residual correlation matrix (rolling betas) against the Marchenko–Pastur edge and a circular-shift null; inverse participation ratios; alignment of each mode with the text network under a label-permutation null.
- **C. Pair test.** Monthly Fama–MacBeth regressions of next-period Fisher-z residual correlation on text similarity, controlling for lagged correlation, historical SIC and Antón–Polk pair characteristics; MRQAP and dyadic-robust inference, since pairs sharing a firm are not independent.
- **D. Covariance horse race.** Fifteen correlation estimators, each turned into an unconstrained minimum-variance portfolio of the 500 largest firms, re-estimated on 252 days and rebalanced every 21 trading days from July 2012 (1,000 firms and 504-day windows as robustness):
  - baselines: 1/N, Ledoit–Wolf (identity), constant correlation, RMT clipping, and Ledoit–Wolf (2020) analytical nonlinear shrinkage, the benchmark;
  - factor models: FF6 and 5-factor PCA;
  - targets a·11ᵀ + b·G + (1−a−b)·I with G from SIC-3 industry, raw bag-of-words or dense text, so text adds value only if b ≠ 0; plus a validated-intensity version, text-preconditioned nonlinear shrinkage, FF6 with text-shrunk residual correlations, and a same-spectrum placebo with relabelled firms.

  Each is scored by out-of-sample volatility with the Ledoit–Wolf (2011) prewhitened-HAC test and a circular block bootstrap.
- **E. Signal.** Hoberg–Phillips text-peer 12-month momentum on a sample that starts where theirs ended; Fama–MacBeth with Newey–West and EWC errors, quintile/decile portfolios with FF5 + momentum + reversal alphas, a stratified peer-substitution null, and a pre/post-publication split with a power analysis stated in advance.

Every estimator and inference step used by the analysis lives in `tfs_stats/`, built on statsmodels, linearmodels and scikit-learn where standard implementations exist, and tested against them (or against simulations with known answers where no library version exists). Primary specifications are pre-registered in [`docs/PREREG.md`](docs/PREREG.md) before the out-of-sample tests are run.

## Results

Q1: text similarity explains residual comovement well beyond SIC (Fama–MacBeth t 24.7; holds under MRQAP, dyadic-robust errors and every robustness check). Q2: a text-based correlation target does not beat Ledoit–Wolf nonlinear shrinkage (its minimum-variance portfolio is 13% more volatile). Q3: Hoberg–Phillips text-peer momentum survives its publication (t 2.81). It works through peers that are both text- and SIC-3-linked: text picks the right neighbours within industries (a stratified FF-48 × size null rejects at p = 0.001), rather than finding links SIC misses. It sits in small stocks and the most recent month. Details, caveats and every exploratory result: [`docs/RESULTS.md`](docs/RESULTS.md).

## Repository layout

```
src/          data pipeline P1–P6 (paths in src/paths.py; TFS_ROOT overrides the root)
tfs_stats/    regression, standard errors, Fama–MacBeth, random-matrix tools, Ledoit–Wolf
tests/        tests for tfs_stats against statsmodels / scikit-learn
analysis/     element scripts producing tables and figures
notebooks/    exploration only
docs/         SPEC (design), DATA (reproduction), PREREG, STATUS, RESULTS
data/         not in the repo: raw/, interim/, processed/
```

## Reproducing

Requires Python 3.10 or later.

```
make setup          # .venv with the core requirements (no torch)
make test           # tfs_stats tests; functions not yet written are reported as skipped
```

Rebuilding the data needs WRDS access for the CRSP/Compustat pulls in `docs/DATA.md`; then, with `.venv` active:

```
python src/convert_wrds.py                                     # P0 WRDS csv.gz -> parquet
python src/build_filing_index.py                               # P1 10-K index
python src/scrape_item1.py > data/interim/scrape.log 2>&1      # P2 Item 1 text (SEC fair-access rate)
python src/build_links.py                                      # P3 filing -> PERMNO
python src/build_panel.py                                      # P4 CRSP panels, factors
pip install -r requirements-nlp.txt && python src/embed_item1.py   # P5 embeddings
python src/bow.py                                              # P6 bag-of-words counts (point-in-time vocabulary)
```

## Acknowledgement

Wharton Research Data Services (WRDS) was used in preparing this project. This service and the data available thereon constitute valuable intellectual property and trade secrets of WRDS and/or its third-party suppliers.

## Status

Complete (8 Oct 2026): every pre-registered and exploratory specification has been run through `src/runner.py`. History and decisions: [`docs/STATUS.md`](docs/STATUS.md), [`docs/SPEC.md`](docs/SPEC.md) §13.

## Licence and author

Code is released under the MIT licence ([`LICENSE`](LICENSE)); it covers the code only, not any data.

Abhinav Raghavan, Carnegie Mellon University (Physics; Computational Finance).
