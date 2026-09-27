# CLAUDE.md — text-factor-space

Context for any Claude Code session working in this repo. Read `docs/SPEC.md` (the full plan) and `docs/STATUS.md` (where things stand) before doing anything.

## What this project is

A research project by Abhinav (Abhi) Raghavan, CMU Physics + Computational Finance, built as preparation for quant research interviews (details in the private plan, `docs/private/PLAN.md`, which exists only on the Mac and is gitignored). It tests whether 10-K business descriptions (Item 1) define economic neighbours that (1) explain residual return comovement beyond SIC, (2) improve covariance estimation, and (3) predict returns (text-peer momentum). Elements A–E are specified in `docs/SPEC.md` §5–§9; compliance rules are in §2.

Live hub (status board + rendered spec): https://claude.ai/artifact/XgCPW4gmqsF8xjCAT4p1pf

## Hard rules

0. **WRDS data (CRSP, Compustat, CCM) — cleared for use, under two conditions.** On 27 Sep 2026 CMU's WRDS representative confirmed to Abhi by email that his Claude plan is an enterprise instance with a no-training agreement, which is the exception in WRDS's AI policy; so you may read and process WRDS data. On scripted access, the WRDS director said automation is fine with a definitive cap (the ToU clause targets continuous scraping). The cap for this project: **at most 10 WRDS web-query submissions per calendar day and 30 per calendar month, one query running at a time, status checks no more than once a minute, never in a loop that resubmits.** Log every submission in `docs/WRDS_QUERIES.md` (date, product, range, query id) before counting it done. Licensing still applies in full: see rule 1.
1. **Never commit data.** CRSP/Compustat come from WRDS under CMU's licence and may not be redistributed; the repo is public. `data/` is gitignored. Do not add parquet/csv/zip/npz files, do not print raw CRSP/Compustat rows into docs, notebooks outputs or commit messages. Aggregate results (coefficients, tables of statistics, figures) are fine.
2. **Do not implement the functions in `tfs_stats/`.** Abhi writes these by hand as interview preparation (they are exactly what quant coding and statistics rounds test). You may explain the math, point out a bug, review his code, or add tests. If asked for a hint, give the next step, not the finished function.
3. **Every estimator and inference step used in `analysis/` must come from `tfs_stats/`,** not from statsmodels/scikit-learn (those are only for tests).
4. **Point-in-time discipline** (`docs/SPEC.md` §3): a 10-K is usable from the trading day after its filing date; Compustat fundamentals 6 months after fiscal year end; universe and size from the prior month. Flag any look-ahead you notice.
5. **Pre-registration:** once `docs/PREREG.md` is frozen, do not change primary specifications; new variants are "exploratory".
6. Update `docs/STATUS.md` at the end of each work session (what changed, what's next, blockers). The Cowork session mirrors it to the live hub.

## Layout

```
src/         data pipeline P1–P6 (paths via src/paths.py; override root with TFS_ROOT)
tfs_stats/   regression.py, rmt.py — Abhi writes these
tests/       pytest; checked against statsmodels / scikit-learn
analysis/    element scripts producing tables/figures (to be created)
docs/        SPEC, STATUS, DATA (reproduction), PREREG (draft until frozen), RESULTS
hub/         builds the hub page from docs/SPEC.md
scripts/     bootstrap_mac.sh (one-time Mac setup: GitHub repo, .venv, tests)
.claude/     settings.json (model, effort, permission allow/deny lists)
data/        gitignored: raw/ interim/ processed/
```

## Environment

```
make setup                             # .venv (Python >= 3.10) + requirements.txt (core, no torch)
source .venv/bin/activate
make test                              # = python -m pytest -q; unimplemented tfs_stats functions are SKIPPED, not failed
pip install -r requirements-nlp.txt    # sentence-transformers + torch, only for src/embed_item1.py
```

`tests/conftest.py` turns a `NotImplementedError` raised inside `tfs_stats/` into a skip; any other failure still fails. CI (`.github/workflows/ci.yml`) runs the same tests on every push without data. Data reproduction steps are in `docs/DATA.md`.

Heavy ingestion (EDGAR scraping, embeddings) runs in the Claude Cowork cloud workspace or on this Mac; WRDS extracts live in `data/raw/` here (`crsp_msf`, `crsp_dsf_2010_2017`, `crsp_dsf_2018_2026`, `ccm_link`, `ccm_funda`, all `.csv.gz`). The SEC scraper needs `SEC_USER_AGENT` set (SEC fair-access rules require a contact); Abhi sets it, never hardcode it. If a file under `data/` is missing, say so rather than regenerating it silently.

## How Abhi likes to work

Casual and direct; technically dense; explicit derivations over asserted results; honest trade-offs over affirmation. He pushes back on over-complication and on re-litigating settled decisions. When he has edited a file, edit his live version, not a copy.

## Syncing with the Cowork cloud session

- The Cowork session (https://claude.ai/code/session_01RmzHHcXZgHJw8QQFom79S8) runs heavy ingestion in the cloud and writes files into this folder. It may make commits prefixed `[cowork]`.
- This local Claude Code session owns `git pull --rebase` and `git push`.
- Start of every local session: `git pull --rebase`. End of every session: update `docs/STATUS.md`, commit, push.
- Git is set up never to prompt for credentials (`scripts/bootstrap_mac.sh` ran `gh auth setup-git`). If a pull or push fails on authentication, stop and tell Abhi exactly what to run; never ask for, store or print a token.
- To send a message back to the cloud session (if the account supports it): `claude -p "<message>" --cloud session_01RmzHHcXZgHJw8QQFom79S8`. If that is rejected, write the request into `docs/STATUS.md` under a "Requests for Cowork" heading instead.
