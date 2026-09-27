# text-factor-space. Run `make help` for targets.

PYTHON ?= python3
VENV   := .venv
# Use the venv's interpreter when it exists, otherwise whatever python3 is on PATH (e.g. CI).
PY     := $(if $(wildcard $(VENV)/bin/python),$(VENV)/bin/python,$(PYTHON))

.DEFAULT_GOAL := help
.PHONY: help setup test hub

help:  ## list targets
	@grep -E '^[a-z-]+:.*## ' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*## "} {printf "  make %-6s %s\n", $$1, $$2}'

setup:  ## create .venv (Python >= 3.10) and install core requirements (no torch)
	@$(PYTHON) -c 'import sys; sys.exit(sys.version_info < (3, 10))' || { echo "Need Python >= 3.10; try: make setup PYTHON=python3.12"; exit 1; }
	test -x $(VENV)/bin/python || $(PYTHON) -m venv $(VENV)
	$(VENV)/bin/python -m pip install --quiet --upgrade pip
	$(VENV)/bin/python -m pip install --quiet -r requirements.txt

test:  ## run the test suite (unimplemented tfs_stats functions show as skipped)
	$(PY) -m pytest -q

hub:  ## rebuild hub/hub.html from docs/SPEC.md
	$(PY) hub/build_hub.py
