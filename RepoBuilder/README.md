# repo-builder

## Live dashboard

A hosted copy of the dashboard is available at **[https://repobuilder-dash.vercel.app](https://repobuilder-dash.vercel.app)** — no local setup required. It serves the bundled RepoBuilder analysis via `/api` on the same origin (replacing `localhost:3000` + `localhost:8000`).

| Local | Live |
|-------|------|
| `http://localhost:3000` | [https://repobuilder-dash.vercel.app](https://repobuilder-dash.vercel.app) |
| `http://localhost:8000` | [https://repobuilder-dash.vercel.app/api](https://repobuilder-dash.vercel.app/api) |

To refresh the live site after re-analyzing a repo:

```bash
repo-intelligence analyze <repo>
cp workspace/<repo-name>/dashboard_data.json api/data/RepoBuilder/dashboard_data.json
npx vercel --prod --scope shivendra-11s-projects
```

---

A **reusable, repo-independent Claude Code agent** that reads any repository and
scaffolds runnable greenfield services. It packages the B1–B6 capabilities:

| Task | Capability                                   | Powered by                         |
|------|----------------------------------------------|------------------------------------|
| B1   | Artifact inventory                           | `scripts/inventory.py`             |
| B2   | API + frontend route map                     | `scripts/endpoints.py`             |
| B3   | Test framework discovery + execution         | `scripts/tests_detect.py` (`--run`) |
| B1–B3 | **Full markdown report** (preferred)        | `scripts/report.py`                |
| B4   | FastAPI greenfield service                   | `templates/fastapi-service`        |
| B5   | Node/Express greenfield API                  | `templates/node-api`               |
| B6   | Rust greenfield CLI                          | `templates/rust-cli`               |

The agent is a Claude Code **subagent** installed globally, so it's available in
*every* repo with no per-repo setup. The repo-reading half is backed by
deterministic, stdlib-only Python scanners (no dependencies); the building half is
backed by proven templates + a generator, so scaffolds run on the first try.

## Why an agent (not just scripts)

`RepoBuilder/` is the source of truth. `install.sh` symlinks the agent definition
into `~/.claude/agents/` and its assets into `~/.claude/repo-builder/`. The agent's
system prompt calls those assets by absolute path — which is exactly why it works
regardless of which repo you happen to be in.

## Install CLI

```bash
pip install -e .                    # or: ./scripts/repo-intelligence
repo-intelligence --help
```

## Repo Intelligence CLI

One command to analyze a repo, generate B1–B6 outputs, build `dashboard_data.json`, and serve the dashboard locally at **http://localhost:3000** (or use the [live dashboard](https://repobuilder-dash.vercel.app) above).

### Execution flow

```
repo-intelligence analyze <repo>
        │
        ├─ B1  inventory_agent     → workspace/{repo}/B1_inventory/
        ├─ B2  route_agent         → workspace/{repo}/B2_routes/
        ├─ B3  test_agent          → workspace/{repo}/B3_tests/
        ├─     graph_engine        → workspace/{repo}/graphs/graph_data.json
        ├─ B4  fastapi_builder     → workspace/{repo}/generated_projects/fastapi/
        ├─ B5  node_builder        → workspace/{repo}/generated_projects/node/
        ├─ B6  rust_builder        → workspace/{repo}/generated_projects/rust/
        ├─     dashboard_data_builder → workspace/{repo}/dashboard_data.json
        │
        ├─ API  :8000  (FastAPI — serves dashboard_data.json)
        └─ UI   :3000  (Vite React dashboard)
```

### Commands

```bash
# Full pipeline + start servers (blocks until Ctrl+C)
repo-intelligence analyze ./my-app

# Same + open browser
repo-intelligence analyze ./my-app --open

# Generate only (no servers)
repo-intelligence analyze ./my-app --no-serve

# Re-serve last analyzed repo
repo-intelligence serve
repo-intelligence serve --open

# List workspace repos
repo-intelligence list

# Remove outputs
repo-intelligence clean           # all repos
repo-intelligence clean my-app    # one repo
```

### Multi-repository workspace

Each analyzed repo gets its own isolated workspace folder:

```
workspace/
├── .repo-intelligence/       # CLI state (last repo, server PIDs)
├── kyc-mini/
│   ├── B1_inventory/
│   ├── B2_routes/
│   ├── B3_tests/
│   ├── graphs/graph_data.json
│   ├── generated_projects/
│   └── dashboard_data.json     # SSOT for this repo
├── stocks-mini/
│   └── …
└── payment-service/
    └── …
```

The API serves **all** repos from `workspace/` (`GET /repos`, `GET /overview?repo=kyc-mini`).
The dashboard **repo selector** (header dropdown) switches repos instantly — no server restart.

```bash
# Analyze multiple repos (one at a time)
repo-intelligence analyze /path/to/kyc-mini --no-serve
repo-intelligence analyze /path/to/stocks-mini --no-serve
repo-intelligence analyze /path/to/payment-service --no-serve

repo-intelligence list
repo-intelligence serve --open
# → http://localhost:3000 — use dropdown to switch repos
# Live (no local servers): https://repobuilder-dash.vercel.app
```

### Examples

```bash
repo-intelligence analyze tests/fixtures/py_app --no-serve --skip-tests
repo-intelligence list
repo-intelligence serve --open
# → http://localhost:3000
```

## Install (agent)

```bash
./install.sh            # symlink install (edits here go live immediately)
./install.sh --copy     # portable snapshot, no link back to this checkout
./install.sh --uninstall
```

Then open any repo in Claude Code and invoke the **repo-builder** agent
("analyze this repo", "inventory this repo", "...map the API", "...run the tests",
"...scaffold a FastAPI service"). Onboarding requests write **`REPO-ANALYSIS.md`**
inside the target repo automatically.

## Using the tools directly (no agent needed)

**One command — full report written to a file:**

```bash
python3 ~/.claude/repo-builder/scripts/report.py <repo>
# → writes <repo>/REPO-ANALYSIS.md (inventory + routes + test setup)

python3 ~/.claude/repo-builder/scripts/report.py <repo> --run-tests
python3 ~/.claude/repo-builder/scripts/report.py <repo> --out docs/onboarding.md
```

Individual scanners (terminal or `--json`):

```bash
python3 ~/.claude/repo-builder/scripts/inventory.py    <repo>   # B1   (+ --json)
python3 ~/.claude/repo-builder/scripts/endpoints.py    <repo>   # B2   (+ --json)
python3 ~/.claude/repo-builder/scripts/tests_detect.py <repo>   # B3   (+ --json, --run)

python3 ~/.claude/repo-builder/scaffold/new_project.py --list
python3 ~/.claude/repo-builder/scaffold/new_project.py --template fastapi-service --dest /tmp/ledger
```

## Layout

```
RepoBuilder/
├── core/                      # platform foundation (stack, scan, shell, json, reports)
│   ├── stack_detector.py
│   ├── file_scanner.py
│   ├── inventory_agent.py     # B1 — artifact inventory → workspace/
│   ├── inventory_ast.py       # tree-sitter parsers (+ regex fallback)
│   ├── route_agent.py         # B2 — routes → workspace/
│   ├── route_ast.py           # AST route extraction
│   ├── route_scanners.py      # backend + frontend route scanners
│   ├── test_agent.py          # B3 — discover + run tests → workspace/
│   ├── test_discovery.py      # Jest/Vitest/Mocha/pytest/JUnit/cargo
│   ├── test_interpreter.py    # parse output + interpret failures
│   ├── graph_engine.py        # NetworkX graph models → graph_data.json
│   ├── fastapi_builder.py     # B4 — FastAPI greenfield → generated_projects/
│   ├── node_builder.py        # B5 — Node/Express greenfield → generated_projects/
│   ├── rust_builder.py        # B6 — Rust CLI greenfield → generated_projects/
│   ├── dashboard_data_builder.py  # merge workspace JSON → dashboard_data.json
│   ├── api_server.py              # FastAPI dashboard API (localhost:8000)
│   ├── shell_executor.py
│   ├── json_writer.py
│   └── report_generator.py
├── dashboard/                 # React + Vite UI (localhost:3000 or repobuilder-dash.vercel.app)
│   ├── src/pages/             # Overview, Inventory, Routes, Tests, Projects, Architecture
│   └── docs/screenshots/      # captured UI screenshots
├── api/                       # Vercel serverless API + bundled dashboard_data.json
├── vercel.json                # Vercel deploy config (project: repobuilder-dash)
├── cli/                     # repo-intelligence CLI (analyze, serve, list, clean)
│   ├── main.py
│   ├── analyze.py           # B1–B6 orchestrator
│   └── serve.py             # API :8000 + UI :3000
├── pyproject.toml           # pip install -e .
├── agents/repo-builder.md     # the subagent (frontmatter + B1–B6 playbook)
├── scripts/
│   ├── lib/detect.py          # walk, language detection, ignore rules
│   ├── report.py              # B1+B2+B3 → REPO-ANALYSIS.md
│   ├── inventory.py           # B1
│   ├── endpoints.py           # B2
│   └── tests_detect.py        # B3
├── templates/
│   ├── fastapi-service/       # B4
│   ├── node-api/              # B5
│   └── rust-cli/              # B6
├── scaffold/new_project.py    # copies a template + prints run commands
└── tests/                     # scanner self-tests + fixture mini-repos
```

## Run the self-tests

One command runs the full platform suite (pytest), template tests, and dashboard Vitest:

```bash
make test                 # everything
make test-platform        # pytest tests/
make test-scanners        # B1–B3 scanner self-tests only
make test-templates       # FastAPI + Node + Rust templates
make test-dashboard       # dashboard Vitest suite
```

Or run platform tests directly:

```bash
pip install -e ".[dev]"
pytest                    # or: make test-platform
```

Individual modules (still supported):

```bash
python3 tests/test_scanners.py
python3 tests/test_core_framework.py
python3 tests/test_inventory_agent.py
python3 tests/test_route_agent.py
python3 tests/test_test_agent.py
python3 tests/test_graph_engine.py
python3 tests/test_fastapi_builder.py
python3 tests/test_node_builder.py
python3 tests/test_rust_builder.py
python3 tests/test_dashboard_data_builder.py
python3 tests/test_cli.py
python3 tests/test_api_server.py
python3 -m core.dashboard_data_builder tests/fixtures/py_app
python3 -m core.api_server --dashboard workspace/py_app/dashboard_data.json
cd dashboard && npm install && npm run dev
```

## Scope & honesty

The scanners are **best-effort regex heuristics** covering the common stacks
(Python, JS/TS, Java/Kotlin, Go, Rust; FastAPI/Flask/Django, Express/Nest, Spring;
React/Vue/Next routing). They favour recall and degrade gracefully on unknown
stacks. They can over-count on library repos that define routes/models inside their
own test suites — the agent is instructed to flag and verify suspicious results
rather than trust them blindly.

## Verified

- Scanner + report self-tests: **8/8 pass** (`tests/test_scanners.py`).
- Platform suite: **`make test-platform`** / **`pytest`** (all `tests/test_*.py`).
- Route canonical dedupe: duplicate method+path across frameworks collapsed (`core/route_dedupe.py`).
- B3 `--run`: **`python3 scripts/tests_detect.py <repo> --run`** executes primary tests with interpretation.
- B4 FastAPI template: **3/3 tests pass** (`pytest`).
- B5 Node template: **3/3 tests pass** (`jest` + `supertest`).
- B6 Rust template: builds & tests via `cargo test` (6 tests). Requires the Rust
  toolchain; if `cargo` is absent the agent reports the commands instead of running.
- Dashboard: **Vitest** unit tests (`cd dashboard && npm test`).
