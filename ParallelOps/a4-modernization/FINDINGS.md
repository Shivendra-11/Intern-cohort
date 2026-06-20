# A4 Modernization Findings — textkit

**Target repo:** `a4-modernization/target-repo/`  
**Baseline commit:** `eb834b8` (`chore: import legacy baseline`)

---

## Evidence-Backed Findings

### F1 — Legacy `setup.py` packaging (no PEP 621)

- **What:** Project uses deprecated `setup.py`-only setuptools layout.
- **Evidence:** `setup.py:1-12` — `from setuptools import setup, find_packages` with inline metadata; no `pyproject.toml` present (`ls -la` shows only `setup.py`).
- **Impact:** Non-standard install path (`python setup.py install`), harder reproducible builds, blocks modern tool configuration in one file.
- **Action:** Migrate to PEP 621 `pyproject.toml` with `[build-system]` and `[project]`.

### F2 — Unpinned dependencies

- **What:** Dev dependencies listed without version pins.
- **Evidence:** `requirements.txt:1-2` — bare `pytest` and `ruff` with no `==` pins.
- **Impact:** Different machines get different tool versions; CI and local dev can diverge silently.
- **Action:** Pin versions in `[project.optional-dependencies] dev`.

### F3 — Stale Python version classifiers

- **What:** Metadata claims support for EOL Python versions.
- **Evidence:** `setup.py:9-10` — `"Programming Language :: Python :: 2.7"` and `"Programming Language :: Python :: 3.5"`.
- **Impact:** Misleading compatibility signals; may hide real minimum version needs.
- **Action:** Update classifiers to Python 3.10+ in `pyproject.toml`.

### F4 — No linter/formatter configuration

- **What:** Ruff is listed as a dependency but no `[tool.ruff]` config exists.
- **Evidence:** `requirements.txt:2` lists `ruff`; `ls -la` shows no `pyproject.toml` or `ruff.toml`; `ruff check .` on baseline reports 6 F401 errors with no project rules.
- **Impact:** Lint behavior is ad hoc; re-exports in `textkit/__init__.py` flagged inconsistently.
- **Action:** Add `[tool.ruff]` section with per-file ignores for intentional re-exports.

### F5 — Missing `.gitignore`

- **What:** No ignore rules for virtualenvs, caches, or build artifacts.
- **Evidence:** `ls -la` — no `.gitignore` file in repo root.
- **Impact:** Risk of committing `.venv/`, `__pycache__/`, `*.egg-info/` accidentally.
- **Action:** Add standard Python `.gitignore` (deferred).

### F6 — No CI workflow

- **What:** No automated test/lint gate on push/PR.
- **Evidence:** `ls -la` — no `.github/` directory.
- **Impact:** Regressions only caught manually.
- **Action:** Add GitHub Actions workflow running `pytest` + `ruff check` (deferred).

### F7 — Legacy idioms in application code

- **What:** `read_lines` uses `os.path`, `%` formatting, bare `open()` without context manager, debug `print`.
- **Evidence:** `textkit/core.py:25-31` — `os.path.join`, `print("reading %s" % full)`, `f = open(full)` without `with`.
- **Impact:** Resource leaks possible; harder to maintain; not pathlib/modern style.
- **Action:** Refactor `read_lines` to `pathlib` + context manager (deferred — touches runtime behavior).

### F8 — No type hints

- **What:** All functions untyped.
- **Evidence:** `textkit/core.py:4-31` — `def slugify(text, sep="-"):` etc. with no annotations.
- **Impact:** No static analysis for API contracts.
- **Action:** Add type hints + optional mypy (deferred).

### F9 — Outdated README install instructions

- **What:** README documents legacy install path.
- **Evidence:** `README.md:7` — `python setup.py install`.
- **Impact:** New contributors follow deprecated workflow.
- **Action:** Update to `pip install -e ".[dev]"` as part of packaging migration.

---

## Prioritized Plan (Value ÷ Risk)

| # | Opportunity | Value (1–5) | Risk (1–5) | Score (V÷R) | Evidence | Rationale |
|---|-------------|-------------|------------|-------------|----------|-----------|
| 1 | Add CI workflow (pytest + ruff) | 4 | 1 | **4.00** | F6 — no `.github/` | Purely additive; zero runtime change; easy revert (delete workflow file). |
| 2 | Add `.gitignore` | 3 | 1 | **3.00** | F5 — missing file | Prevents accidental artifact commits; no behavior change. |
| 3 | Pin deps in `requirements.txt` only | 3 | 1 | **3.00** | F2 — unpinned lines | Improves reproducibility but keeps legacy layout. |
| 4 | **Migrate to `pyproject.toml` (PEP 621) + pinned dev deps + ruff config** | **5** | **2** | **2.50** | F1, F2, F3, F4, F9 | Highest structural value: modern packaging, pinned tools, lint config, updated README — metadata only, app code untouched. |
| 5 | Update README install line alone | 2 | 1 | 2.00 | F9 — `README.md:7` | Low value without packaging migration behind it. |
| 6 | Add type hints to `core.py` | 4 | 2 | 2.00 | F8 — untyped defs | Useful but touches public API surface. |
| 7 | Refactor `read_lines` (pathlib + context manager) | 3 | 3 | 1.00 | F7 — `core.py:25-31` | Alters runtime I/O path — not low-risk. |
| 8 | Remove debug `print` in `read_lines` | 2 | 3 | 0.67 | F7 — `core.py:27` | Changes observable stdout behavior. |

Sorted by **Score** descending. Among **low-risk** items (Risk ≤ 2), **#4 has the highest Value (5)** even though #1 has a higher Score.

---

## Selected First Step

**Implementing:** #4 — Migrate `setup.py` + `requirements.txt` → PEP 621 `pyproject.toml` with pinned dev dependencies and `[tool.ruff]` configuration; update README install instructions.

**Why highest-value AND low-risk:**
- **Value 5** — unlocks reproducible `pip install -e ".[dev]"`, modern metadata, pinned pytest/ruff, and project-level lint rules in one coherent change.
- **Risk 2** — packaging and tooling config only; `textkit/core.py` and tests unchanged; fully reversible via `git checkout main` or `git revert 2003708`.
- Chosen over #1 (CI, Score 4.0) because packaging migration is a prerequisite for a meaningful CI install step and delivers more foundational modernization in a single reversible commit.

**Deliberately deferred:** CI workflow (#1), `.gitignore` (#2), and `read_lines` refactor (#7) — follow-up steps after packaging baseline is in place.
