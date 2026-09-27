# Status

_Last updated: Sun 27 Sep 2026, 01:50 ET_

## Done
- Spec v1 (`docs/SPEC.md`): every element checked against primary sources by five research dossiers and a critic pass.
- SEC: bulk submissions → 61,589 10-K/10-KT indexed (Jun 2011–Sep 2026).
- WRDS pulls (Sat night): CRSP v2 monthly and daily (2010-01-04 → 2026-03-31), CCM link table, CCM Fundamentals Annual. Fama–French factors and Hoberg–Phillips TNIC-3 downloaded.
- Repo scaffold: bootstrap script, project settings, CI, tests (12, skipped until implemented), DATA/PREREG docs, MIT licence.
- Mac (M4 Pro, 24 GB): local session up; `make test` 12 skipped; NLP stack installed in `.venv` (torch 2.14, sentence-transformers 6.1), MPS available. bge-small encodes ~170 chunks/s on MPS vs ~34 on CPU, so P5 could run here in ~15 min once the Item 1 shards are synced (`src/embed_item1.py` currently hardcodes `device='cpu'`).

## Running (cloud workspace, public SEC data only)
- P2 Item 1 extraction: restarted after an out-of-memory kill; ETA ≈ 00:50 ET.
- P5 embeddings (bge-small, first 2×500 tokens): ETA ≈ 05:30 ET.

## Blocked
- **D0 — WRDS data use.** WRDS's AI policy prohibits loading WRDS data into generative-AI tools except protected enterprise instances, and its Terms of Use prohibit scripting web queries. The assistant has stopped processing CRSP/Compustat data until Abhi decides (SPEC §2). The CIK→PERMNO links and CRSP panels already built are paused.
- Universe fix pending D0: add `IssuerType ∈ {ACOR, CORP}` and `ConditionalType ∈ {RW, NW}` (v0 included REITs).

## Next
- Assistant: P6 bag-of-words vectors (trailing-window vocabulary, nouns-only variant) when P2 finishes; Element A validation on public data (similarity distributions, neighbour spot checks).

## Requests
_(add requests here)_
