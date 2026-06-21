# Intern-Cohort — one-command verification across all four eval projects.
# Usage:
#   make help          list targets
#   make install       create a self-contained .venv and install every dependency
#   make test          run every suite (Python + Node + Rust); skips Node/Rust gracefully
#   make test-python   only the Python suites
#   make test-node     only the A3 Node worker suite
#   make test-rust     only the A3 Rust engine suite
#   make clean         remove __pycache__ / .pyc build cache
#   make distclean     also remove the .venv
#
# `make install && make test` is reproducible from a fresh clone: it builds an
# isolated virtualenv so it never depends on (or writes to) the system Python.

# Prefer a 3.10+ interpreter (editable installs need it); fall back to python3.
PYTHON  := $(shell command -v python3.12 || command -v python3.11 || command -v python3.10 || command -v python3)
VENV    := $(CURDIR)/.venv
VPY     := $(VENV)/bin/python
PIP     := $(VPY) -m pip
STAMP   := $(VENV)/.installed

.DEFAULT_GOAL := help
.PHONY: help test test-python test-node test-rust install clean distclean

help:
	@echo "Targets:"
	@echo "  make install      build .venv and install all deps (first time only)"
	@echo "  make test         run all suites (Python + Node + Rust)"
	@echo "  make test-python  RepoBuilder + polyglot + ParallelOps (framework, A3, fraud-system)"
	@echo "  make test-node    A3 Node worker"
	@echo "  make test-rust    A3 Rust fraud-engine"
	@echo "  make clean        delete __pycache__ and *.pyc"
	@echo "  make distclean    also delete the .venv"
	@echo ""
	@echo "Using interpreter: $(PYTHON)"

# Build the virtualenv and install everything the test suites need.
$(STAMP):
	@echo "==> Creating virtualenv at $(VENV) (interpreter: $(PYTHON))"
	$(PYTHON) -m venv $(VENV)
	$(PIP) install --quiet --upgrade pip wheel
	@echo "==> Editable-installing the two Python packages (RepoBuilder with the tree-sitter 'inventory' extra)"
	$(PIP) install --quiet -e "RepoBuilder[inventory]" -e polyglot-builder
	@echo "==> Installing lane dependencies"
	$(PIP) install --quiet \
	  -r ParallelOps/requirements-framework.txt \
	  -r ParallelOps/a3-polyglot/requirements.txt \
	  -r ParallelOps/fraud-system/requirements.txt
	@touch $(STAMP)
	@echo "==> Environment ready."

install: $(STAMP)

test: test-python test-node test-rust
	@echo ""
	@echo "==> All available suites passed."

test-python: $(STAMP)
	@echo "==> RepoBuilder"
	cd RepoBuilder      && $(VPY) -m pytest tests -q
	@echo "==> polyglot-builder"
	cd polyglot-builder && $(VPY) -m pytest tests -q
	@echo "==> ParallelOps (framework)"
	cd ParallelOps      && $(VPY) -m pytest tests -q
	@echo "==> ParallelOps A3 polyglot"
	cd ParallelOps/a3-polyglot && $(VPY) -m pytest tests -q
	@echo "==> ParallelOps fraud-system"
	cd ParallelOps/fraud-system && $(VPY) -m pytest tests -q

test-node:
	@command -v node >/dev/null 2>&1 || { echo "==> node not found — skipping Node suite"; exit 0; }
	@echo "==> A3 Node worker"
	cd ParallelOps/a3-polyglot/worker && node --test

test-rust:
	@command -v cargo >/dev/null 2>&1 || { echo "==> cargo not found — skipping Rust suite"; exit 0; }
	@echo "==> A3 Rust fraud-engine"
	cd ParallelOps/a3-polyglot/fraud-engine && cargo test

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@echo "==> cleaned __pycache__ and *.pyc"

distclean: clean
	rm -rf $(VENV)
	@echo "==> removed $(VENV)"

