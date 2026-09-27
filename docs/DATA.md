# Reproducing the data


> **WRDS access rules for this project.** Scripted web queries are allowed within the cap in project rule 0 (≤10 submissions/day, ≤30/month, one at a time), per the WRDS director's guidance to Abhi on 27 Sep 2026; log each one in `docs/WRDS_QUERIES.md`. Use with AI tools is covered by CMU's enterprise no-training agreement (confirmed by CMU's WRDS representative, 27 Sep 2026).

Nothing under `data/` is in this repository. CRSP and Compustat are licensed through WRDS (here via Carnegie Mellon's subscription) and may not be redistributed; everything else is public. This page lists every query and download needed to rebuild `data/`, then the order in which the pipeline turns them into the analysis files. Rules and rationale are in `docs/SPEC.md` §3–§4.

```
data/raw/        WRDS extracts, SEC submissions.zip, Fama-French zips, Hoberg-Phillips tnic3_data.zip
data/interim/    tenk_index, tenk_linked, item1/ (Item 1 text shards), emb/ (embeddings), tfidf/
data/processed/  crsp_monthly, crsp_daily, ff_daily, ff_monthly
```

All scripts resolve paths through `src/paths.py`; set `TFS_ROOT` to use a different root and `SEC_USER_AGENT` to your own "Name email" contact string.

## 1. WRDS web queries

Common output settings for all four: output format **comma-delimited text (.csv)**, compression **gzip (.csv.gz)**; everything else at the form's defaults. Save the download under the file name given.

### (a) CRSP monthly stock file → `data/raw/crsp_msf.csv.gz`

| Setting | Value |
|---|---|
| Product | CRSP → Stock – Version 2 (CIZ), Quarterly Update (library `crsp_q_stock`) |
| Dataset | Monthly Stock File |
| Date range | 2009-01-01 to 2026-06-30 |
| Search | Search the entire database |
| Variables | `permno, permco, hdrcusip, primaryexch, conditionaltype, tradingstatusflg, usincflg, issuertype, securitytype, securitysubtype, sharetype, ticker, siccd, naics, issuernm, mthcaldt, mthret, mthretx, mthretflg, mthcap, mthprc, mthvol, shrout, vwretd` |
| Result | 1,690,904 rows. CIZ `mthret` already includes delisting returns. |

### (b) CRSP daily stock file → `data/raw/crsp_dsf_<start>_<end>.csv.gz`

| Setting | Value |
|---|---|
| Product | CRSP → Stock – Version 2 (CIZ), Quarterly Update (`crsp_q_stock`) |
| Dataset | Daily Stock File |
| Date range | 2010-01-01 to 2026-03-31, **pulled in date chunks** (a single full-range query stalls) |
| Search | Search the entire database |
| Variables | `permno, dlycaldt, dlyret, dlycap`, plus the form's defaults `HdrCUSIP, Ticker, PERMCO` |
| Files | one per chunk, named by year range, e.g. `crsp_dsf_2018_2026.csv.gz` (2018-01-01 to 2026-03-31, 18.3M rows) |

### (c) CCM link table → `data/raw/ccm_link.csv.gz`

| Setting | Value |
|---|---|
| Product | CRSP/Compustat Merged, Quarterly Update (library `crsp_q_ccm`) |
| Dataset | Linking Table |
| Date range / search | Entire database (full link history) |
| Link types | `LC`, `LU` |
| Link primacy | not recorded for the original pull; the code applies `LINKPRIM ∈ {P, C}` where it matters (P3) |
| Variables | `gvkey, liid, linkdt, linkenddt, linkprim, linktype, lpermco, lpermno, conm, tic, cusip, cik, sic, naics, gsector, gind, gsubind, ipodate, dldte, dlrsn, busdesc` |
| Result | 32,948 link rows |

### (d) CCM Fundamentals Annual → `data/raw/ccm_funda.csv.gz`

| Setting | Value |
|---|---|
| Product | CRSP/Compustat Merged, Quarterly Update (`crsp_q_ccm`) |
| Dataset | Fundamentals Annual |
| Date range | 2009-01 to 2026-09 (data date) |
| Search | Search the entire database |
| Screens | consolidation `C`, industry format `INDL`, data format `STD`, population source `D`; currency USD and CAD; company status active and inactive |
| Link types | `LC`, `LU` |
| Variables | `gvkey, lpermno, lpermco, linkprim, linktype, liid, datadate, fyear, cik, conm, tic, exchg, fyr, sich, naicsh, at, ceq, seq, pstk, pstkl, pstkrv, txditc, csho, prcc_f, sale, revt, ni, ib, lt, oancf, xrd, capx, emp, cogs, xsga, dvc` |
| Result | 95,382 rows (FY2008 → FY2026) |

### Converting the WRDS CSVs to parquet

`build_filing_index.py`, `build_links.py` and `build_panel.py` read `crsp_msf.parquet` and `crsp_dsf_*.parquet`, not the CSVs. No script in `src/` does this step yet; the conversion below reproduces the schemas of the existing files (lower-case column names; daily columns renamed to `permno, date, cap, ret`).

```python
import glob, pandas as pd
m = pd.read_csv("data/raw/crsp_msf.csv.gz", low_memory=False)
m.columns = m.columns.str.lower()
m.to_parquet("data/raw/crsp_msf.parquet")

for f in sorted(glob.glob("data/raw/crsp_dsf_*.csv.gz")):
    d = pd.read_csv(f, low_memory=False)
    d.columns = d.columns.str.lower()
    d = d.rename(columns={"dlycaldt": "date", "dlycap": "cap", "dlyret": "ret"})[["permno", "date", "cap", "ret"]]
    d["permno"] = d["permno"].astype("int32")
    d["date"] = pd.to_datetime(d["date"])
    d["ret"] = pd.to_numeric(d["ret"], errors="coerce").astype("float32")
    d.to_parquet(f.replace(".csv.gz", ".parquet"))

f = pd.read_csv("data/raw/ccm_funda.csv.gz", low_memory=False)
f.columns = f.columns.str.lower()
f.to_parquet("data/raw/ccm_funda.parquet")
```

## 2. Public sources

| File in `data/raw/` | Source | Notes |
|---|---|---|
| `submissions.zip` | https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip | ~1.6 GB, regenerated nightly. SEC rejects requests without a descriptive `User-Agent` ("Name email"); stay under 10 requests/s. |
| `F-F_Research_Data_5_Factors_2x3_daily_CSV.zip`, `F-F_Research_Data_5_Factors_2x3_CSV.zip`, `F-F_Momentum_Factor_daily_CSV.zip`, `F-F_Momentum_Factor_CSV.zip` | `https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/<file>` | Ken French data library, 1963-07 → 2026-08 at download. The library is revised periodically. |
| `tnic3_data.zip` | https://hobergphillips.tuck.dartmouth.edu/idata/tnic3_data.zip | Hoberg–Phillips TNIC-3 network, 1988 → 2023 (~150 MB). |

```bash
UA="${SEC_USER_AGENT:?set SEC_USER_AGENT to 'Your Name you@example.com'}"
curl -fL -A "$UA" -o data/raw/submissions.zip https://www.sec.gov/Archives/edgar/daily-index/bulkdata/submissions.zip
for f in F-F_Research_Data_5_Factors_2x3_daily_CSV F-F_Research_Data_5_Factors_2x3_CSV F-F_Momentum_Factor_daily_CSV F-F_Momentum_Factor_CSV; do
  curl -fL -o "data/raw/$f.zip" "https://mba.tuck.dartmouth.edu/pages/faculty/ken.french/ftp/$f.zip"
done
curl -fL -o data/raw/tnic3_data.zip https://hobergphillips.tuck.dartmouth.edu/idata/tnic3_data.zip
```

Byte-for-byte reproduction of the public files needs the same download date (Sep 2026): EDGAR's bulk file grows nightly and the French library is revised.

## 3. Universe and linking rules (SPEC §3)

**Universe.** US-incorporated common stock on NYSE, NYSE American or Nasdaq, from the CRSP monthly file: `sharetype = 'NS'`, `securitytype = 'EQTY'`, `securitysubtype = 'COM'`, `usincflg = 'Y'`, `primaryexch ∈ {N, A, Q}`. This is the CIZ counterpart of the legacy `SHRCD ∈ {10, 11}` filter (exact mapping, including REIT treatment, still being verified). Result: 8,401 PERMNOs, 3,750–4,600 per year.

**10-K index (P1).** Forms `10-K`, `10-K405`, `10-KT` filed on or after 2011-06-01, for every CIK with a CCM link to a universe PERMNO that is active on or after 2011-01-01. Duplicate accession numbers are dropped.

**Links (P3).** CIK → gvkey → PERMNO through the CCM link table:
- keep links with `LINKPRIM ∈ {P, C}` and `LINKTYPE ∈ {LC, LU}` (the latter set by the query), PERMNO in the universe;
- the link must be valid on the filing date: `linkdt ≤ filing_date ≤ linkenddt`, with an open end (`E`) read as 2099-12-31;
- if several PERMNOs qualify, keep the one with the largest market cap in the filing month;
- keep one 10-K per PERMNO per report year (the latest filing).

Compustat stores only each company's *current* CIK, so firms whose CIK changed are dropped rather than mislinked: 56,495 firm-year 10-Ks map (92.3% of 61,589).

**Point in time.** A 10-K's text is usable from the trading day after its filing date and for at most 15 months; Compustat fundamentals 6 months after fiscal year end; industry from CRSP `siccd` as of the month (GICS is a current snapshot, robustness only); universe membership and size from the prior month-end.

## 4. Pipeline order

Run from the repo root with the venv active (`make setup && source .venv/bin/activate`).

| Stage | Command | Reads | Writes |
|---|---|---|---|
| P0 | the conversion snippet above | WRDS CSVs | `data/raw/*.parquet` |
| P1 | `python src/build_filing_index.py` | `crsp_msf.parquet`, `ccm_link.csv.gz`, `submissions.zip` | `data/interim/tenk_index.parquet` (61,589 10-Ks) |
| P2 | `python src/scrape_item1.py > data/interim/scrape.log 2>&1` | `tenk_index.parquet`, EDGAR (≤ 8 requests/s) | `data/interim/item1/shard_*.parquet`; resumable |
| P3 | `python src/build_links.py` | `tenk_index.parquet`, `crsp_msf.parquet`, `ccm_link.csv.gz` | `data/interim/tenk_linked.parquet` (56,495 firm-years) |
| P4 | `python src/build_panel.py` | `crsp_msf.parquet`, `crsp_dsf_*.parquet`, French zips | `data/processed/{crsp_monthly,crsp_daily,ff_daily,ff_monthly}.parquet` |
| P5 | `python src/embed_item1.py` (needs `pip install -r requirements-nlp.txt`) | `item1/` shards | `data/interim/emb/shard_*.parquet` (384-d unit vectors) |
| P6 | `python src/tfidf.py` | `tenk_linked.parquet`, `item1/` shards | `data/interim/tfidf/{X,rows,vocab}_<year>.*` |

Notes:
- P2's log must go to `data/interim/scrape.log`: P5 processes shards as they appear and stops only once that log contains `DONE`, so P5 can run alongside P2.
- P5 downloads `BAAI/bge-small-en-v1.5` from Hugging Face on first use and runs on CPU.
- P6 needs P2 finished (it reads all shards).
- Checks per stage (row counts, extraction rate, norms) are listed in SPEC §4.
