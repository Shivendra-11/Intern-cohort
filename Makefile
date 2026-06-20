# Intern-Cohort — one-command verification across all four eval projects.
# Usage:
#   make help          list targets
#   make test          run every suite (Python + Node + Rust); skips gracefully
#   make test-python   only the Python suites
#   make test-node     only the A3 Node worker suite
#   make test-rust     only the A3 Rust engine suite
#   make install       editable-install the two Python packages
#   make clean         remove local __pycache__ / .pyc build cache

PY := python3
.DEFAULT_GOAL := help

.PHONY: help test test-python test-node test-rust install clean

help:
	@echo "Targets:"
	@echo "  make test         run all suites (Python + Node + Rust)"
	@echo "  make test-python  RepoBuilder + polyglot + ParallelOps (framework, A3, fraud-system)"
	@echo "  make test-node    A3 Node worker"
	@echo "  make test-rust    A3 Rust fraud-engine"
	@echo "  make install      pip install -e RepoBuilder and polyglot-builder"
	@echo "  make clean        delete __pycache__ and *.pyc"

test: test-python test-node test-rust
	@echo ""
	@echo "==> All available suites passed."

test-python:
	@echo "==> RepoBuilder"
	cd RepoBuilder      && $(PY) -m pytest tests -q
	@echo "==> polyglot-builder"
	cd polyglot-builder && $(PY) -m pytest tests -q
	@echo "==> ParallelOps (framework)"
	cd ParallelOps      && $(PY) -m pytest tests -q
	@echo "==> ParallelOps A3 polyglot"
	cd ParallelOps/a3-polyglot && $(PY) -m pytest tests -q
	@echo "==> ParallelOps fraud-system"
	cd ParallelOps/fraud-system && $(PY) -m pytest tests -q

test-node:
	@command -v node >/dev/null 2>&1 || { echo "==> node not found — skipping Node suite"; exit 0; }
	@echo "==> A3 Node worker"
	cd ParallelOps/a3-polyglot/worker && node --test

test-rust:
	@command -v cargo >/dev/null 2>&1 || { echo "==> cargo not found — skipping Rust suite"; exit 0; }
	@echo "==> A3 Rust fraud-engine"
	cd ParallelOps/a3-polyglot/fraud-engine && cargo test

install:
	$(PY) -m pip install -e RepoBuilder
	$(PY) -m pip install -e polyglot-builder

clean:
	find . -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name '*.pyc' -delete 2>/dev/null || true
	@echo "==> cleaned __pycache__ and *.pyc"
