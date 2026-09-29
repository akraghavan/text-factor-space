# Reproducing the data


> **WRDS access rules for this project.** Scripted web queries are allowed under the rules in project rule 0 (one at a time, no resubmitting loops), per the WRDS director's guidance to Abhi on 27 Sep 2026; log each one in `docs/WRDS_QUERIES.md`. Use with AI tools is covered by CMU's enterprise no-training agreement (confirmed by CMU's WRDS representative, 27 Sep 2026).

Nothing under `data/` is in this repository. CRSP and Compustat are licensed through WRDS (here via Carnegie Mellon's subscription) and may not be redistributed; everything else is public. This page lists every query and download needed to rebuild `data/`, then the order in which the pipeline turns them into the analysis files. Rules and rationale are in `docs/SPEC.md` §3–§4.

```
data/raw/        WRDS extracts, SEC submissions.zip, Fama-French zips, Hoberg-Phillips tnic3_data.zip
data/interim/    tenk_index, tenk_linked, item1/ (Item 1 text shards), emb/ (embeddings), bow/ (P6 v1), tfidf/ (P6 v0)
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

### Converting the WRDS CSVs to parquet (P0)

`build_filing_index.py`, `build_links.py` and `build_panel.py` read parquet, not the CSVs. `python src/convert_wrds.py` writes:

| Output | From | Schema |
|---|---|---|
| `data/raw/crsp_msf.parquet` | `crsp_msf.csv.gz` | all columns, lower-case names; `mthcaldt` datetime; returns, price, cap, volume numeric; `siccd` nullable integer |
| `data/raw/crsp_dsf_<range>.parquet` | each `crsp_dsf_<range>.csv.gz` | `permno` (int32), `date`, `cap` (DlyCap, $000s), `ret` (DlyRet, float32) |
| `data/raw/ccm_funda.parquet` | `ccm_funda.csv.gz` | all columns, lower-case; `datadate` datetime |
| `data/raw/crsp_dsf_pv_<range>.parquet` (D12) | `crsp_dsf_pv_<range>.csv.gz` (WRDS queries 11716335, 11716454: `permno, dlycaldt, dlyprc, dlyvol`) | `permno` (int32), `date`, `prc` = abs(DlyPrc) (float32), `vol` = DlyVol (float32); duplicate permno-dates dropped; keys checked against the return file. P4 merges them into `crsp_daily` for the daily Amihud measure (`formation.amihud_daily`) |

`ccm_link.csv.gz` is read directly. The script skips outputs newer than their source (`--force` rebuilds) and prints only shapes and date ranges.

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

**Universe.** US-incorporated common stock on NYSE, NYSE American or Nasdaq, from the CRSP monthly file: `sharetype = 'NS'`, `securitytype = 'EQTY'`, `securitysubtype = 'COM'`, `usincflg = 'Y'`, `issuertype ∈ {ACOR, CORP}`, `conditionaltype ∈ {RW, NW}`, `primaryexch ∈ {N, A, Q}` (`src/universe.py`). This is the CIZ counterpart of the legacy `SHRCD ∈ {10, 11}` filter; `issuertype` drops REITs (legacy 18), which v0 included.

**10-K index (P1).** Forms `10-K`, `10-K405`, `10-KT` filed on or after 2011-06-01, for every CIK with a CCM link to a universe PERMNO that is active on or after 2011-01-01. Duplicate accession numbers are dropped.

**Links (P3).** CIK → gvkey → PERMNO through the CCM link table:
- keep links with `LINKPRIM ∈ {P, C}` and `LINKTYPE ∈ {LC, LU}` (the latter set by the query), PERMNO in the universe;
- the link must be valid on the filing date: `linkdt ≤ filing_date ≤ linkenddt`, with an open end (`E`) read as 2099-12-31;
- if several PERMNOs qualify, keep the one with the largest market cap in the filing month;
- keep one 10-K per PERMNO per report year (the latest filing).

Compustat stores only each company's *current* CIK, so firms whose CIK changed are dropped rather than mislinked. With the v1 universe, 54,602 of 61,589 indexed 10-Ks map (88.7%) and 54,254 firm-years remain after one per PERMNO per report year (3,378–4,046 per filing year 2012–2026). The index is a superset built with the v0 universe, so its REIT filings now simply fail to map; v0 mapped 92.3% (56,495 firm-years).

**Point in time.** A 10-K's text is usable from the trading day after its filing date and for at most 15 months; Compustat fundamentals 6 months after fiscal year end; industry from CRSP `siccd` as of the month (GICS is a current snapshot, robustness only); universe membership and size from the prior month-end.

## 4. Pipeline order

Run from the repo root with the venv active (`make setup && source .venv/bin/activate`).

| Stage | Command | Reads | Writes |
|---|---|---|---|
| P0 | `python src/convert_wrds.py` | WRDS CSVs | `data/raw/{crsp_msf,crsp_dsf_*,ccm_funda}.parquet` |
| P1 | `python src/build_filing_index.py` | `crsp_msf.parquet`, `ccm_link.csv.gz`, `submissions.zip` | `data/interim/tenk_index.parquet` (61,589 10-Ks) |
| P2 (historical) | `python src/scrape_item1.py > data/interim/scrape.log 2>&1` | `tenk_index.parquet`, EDGAR (≤ 8 requests/s) | `data/interim/item1/shard_*.parquet`; resumable, retries failed downloads |
| P2b (historical) | `python src/rescue_item1.py` | shards with < 300 words, EDGAR (≤ 8 requests/s) | re-extracts with the line-aware v2 extractor and patches the shards in place (column `extractor`; originals in `data/interim/item1_v1/`); then rerun P5 and P6 |
| **P2′ (canonical, text-layer-v1)** | `python src/refetch_html.py >> data/interim/refetch.log 2>&1` | `tenk_index.parquet`, EDGAR (≤ 8 requests/s; `SEC_USER_AGENT`) | `data/raw/edgar_html/<accession>.html.gz` (raw bytes, 61,589, ~13 GB) + `_manifest.parquet`; resumable, ~2.2 h |
| **P2″** | `python src/canon_item1.py`, then `mv data/interim/item1_canon data/interim/item1` | stored HTML | canonical Item 1 shards: v1 and v2 extractors, structural validity checks, rule validated on 100 hand-checked disagreements (`analysis/output/d10/handcheck.md`); ~10 min |
| P3 | `python src/build_links.py` | `tenk_index.parquet`, `crsp_msf.parquet`, `ccm_link.csv.gz` | `data/interim/tenk_linked.parquet` (54,254 firm-years) |
| P4 | `python src/build_panel.py` | `crsp_msf.parquet`, `crsp_dsf_*.parquet`, French zips | `data/processed/{crsp_monthly,crsp_daily,ff_daily,ff_monthly}.parquet` |
| P4b | `python src/universe.py` | `tenk_linked`, `crsp_monthly`, Item 1 shards | D8 SPAC flags: `data/interim/spac_filings.parquet`, `data/processed/spac_months.parquet` (excluded via `universe.exclude_spacs`) |
| P4c | `python src/mask_names.py` | `tenk_linked`, `crsp_monthly`, Item 1 shards | `data/interim/name_masks.parquet` (own name/ticker patterns applied by P5) |
| P7 (C, B) | `python src/c_panel.py --build` | `crsp_daily`, `ff_daily` | out-of-sample FF6 residual panel: `data/processed/ff6_resid_daily.npy` (+ index, permnos), `ff6_betas.parquet`; betas on the 252 trading days before each month (≥ 200 obs), applied to the month's days; 7 s |
| P5 | `python src/embed_item1.py` (needs `pip install -r requirements-nlp.txt`; `--follow` to run alongside P2) | `item1/` shards | `data/interim/emb/shard_*.parquet` (384-d unit vectors) |
| P6 | `python src/bow.py` | `item1/` shards, `tenk_index.parquet`, `tenk_linked.parquet` (summary), WordNet | `data/interim/bow/{n_total,n_title,n_lower}.npz`, `rows.parquet`, `vocab.parquet` |
| P6 v0 | `python src/tfidf.py` (superseded: calendar-year vocabulary, look-ahead) | `tenk_linked.parquet`, `item1/` shards | `data/interim/tfidf/{X,rows,vocab}_<year>.*` |

Notes:
- P4 market cap is in **dollars**: `crsp_monthly.me` = CIZ `MthCap` × 1000 and `crsp_daily.cap` = `DlyCap` × 1000 (CRSP reports both in $000s; the `*.parquet` files in `data/raw/` keep CRSP's units). `me_lag` is the prior month's `me`.
- The text layer is frozen at git tag `text-layer-v1` (27 Sep 2026): P2′/P2″ canonical Item 1 → P4b SPAC flags → P4c name masks → P5 (masked) → P6. P2/P2b are kept only to document how the first extraction was made.
- P5 embeds every Item 1 shard not yet embedded and exits. With `--follow` it keeps polling for new shards until `data/interim/scrape.log` contains `DONE`, so it can run alongside P2 (whose log must then go to that file).
- P5 downloads `BAAI/bge-small-en-v1.5` from Hugging Face on first use. Device from `TFS_DEVICE`, else MPS > CUDA > CPU (MPS and CPU embeddings agree to ~1e-7); batch from `TFS_BATCH` (64 on GPU, 32 on CPU).
- P6 needs P2 finished (it reads all shards). It stores word counts per filing once; the vocabulary is applied per formation date by `bow.formation_vectors(B, t, docs, pool, variant)` from filings in the pool filed in [t − 365 days, t): words in ≥ 5 and ≤ 25% of those filings, stop words and geographic terms (`src/geo_terms.py`) dropped; `variant='nouns'` keeps WordNet nouns plus proper nouns (Title-case in ≥ 90% of occurrences in the window).
- WordNet for the nouns variant: `python -c "import nltk; nltk.download('wordnet', download_dir='data/raw/nltk_data')"` (Princeton WordNet 3.0 via nltk; stands in for HP's Webster's noun list).
- Checks per stage (row counts, extraction rate, norms) are listed in SPEC §4.
