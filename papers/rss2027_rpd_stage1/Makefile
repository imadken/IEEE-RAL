SHELL := /bin/bash
PYTHON ?= python3
REPO := ../..

.PHONY: all check clean reproduce figure verify-originals verify-preservation verify-seal verify-prior-seal tests numerics
all: submission/rpd_stage1_anonymous.pdf

submission/rpd_stage1_anonymous.pdf: $(wildcard manuscript/*.tex) manuscript/references.bib manuscript/figures/figure1.pdf template/upstream/IEEEtran.cls tools/workspace.py
	$(PYTHON) tools/workspace.py build

check: all
	$(PYTHON) tools/workspace.py check

reproduce:
	$(PYTHON) tools/workspace.py reproduce

verify-originals:
	$(PYTHON) tools/workspace.py originals

verify-preservation:
	$(PYTHON) tools/workspace.py preservation

verify-seal:
	sha256sum --quiet --check reviews/v21_preliminary/SHA256SUMS

verify-prior-seal:
	$(PYTHON) tools/workspace.py prior-seal

figure:
	MPLCONFIGDIR=/tmp/rss-rpd-mpl UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --project $(REPO) --offline --no-sync python tools/figure1.py --output manuscript/figures

clean:
	$(PYTHON) tools/workspace.py clean

tests:
	UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --project $(REPO) --offline --no-sync python -m unittest discover -s tools -p 'test_*.py' -v

numerics:
	UV_CACHE_DIR=/tmp/rss-rpd-uv uv run --project $(REPO) --offline --no-sync python tools/protocol_math.py --output build/proposed_protocol_and_numerics.json
