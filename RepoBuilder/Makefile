.PHONY: help install install-dev test test-platform test-scanners test-templates test-dashboard lint

help:
	@echo "Targets:"
	@echo "  make install-dev      Install repo-intelligence with dev deps (pytest)"
	@echo "  make test             Run all platform + template + dashboard tests"
	@echo "  make test-platform    Run platform tests via pytest"
	@echo "  make test-scanners    Run B1-B3 scanner self-tests"
	@echo "  make test-templates   Run FastAPI, Node, and Rust template tests"
	@echo "  make test-dashboard   Run dashboard Vitest suite"

install-dev:
	python3 -m pip install -e ".[dev]"

test: test-platform test-templates test-dashboard

test-platform:
	PYTHONPATH=. python3 -m pytest -q

test-scanners:
	python3 tests/test_scanners.py

test-templates:
	cd templates/fastapi-service && python3 -m pip install -q -r requirements.txt && python3 -m pytest -q
	cd templates/node-api && npm ci --silent && npm test
	cd templates/rust-cli && cargo test --quiet

test-dashboard:
	cd dashboard && npm ci --silent && npm test

lint:
	python3 -m ruff check core cli tests scripts 2>/dev/null || true
