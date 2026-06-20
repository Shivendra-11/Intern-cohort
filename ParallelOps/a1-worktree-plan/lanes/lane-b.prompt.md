# Lane B Agent Prompt — Threshold Config Endpoint

## Context (read this before writing a single line of code)

You are working on the **A3 fraud-score system** located at
`a3-polyglot/` inside the repository root
(`/Users/shivendrakeshari/Desktop/ParallelOps`). The system is a FastAPI service
(`a3-polyglot/main.py`). The current fraud-score verdict bands are hard-coded in
`contract.md`:

| Score | Verdict |
|-------|---------|
| 0–30 | Low Risk |
| 31–70 | Medium Risk |
| 71–100 | High Risk |

You are working on branch **`feat/lane-b`** in a dedicated git worktree. You
must not touch any files outside your owned set. No other agent exists in your
view — do not leave TODOs for other lanes.

---

## Your goal

Implement two endpoints so operators can inspect and update the verdict-band
boundaries at runtime without restarting the service:

- `GET /config/thresholds` — return current threshold config as JSON.
- `PUT /config/thresholds` — validate and persist new boundaries; return the
  updated config.

### Acceptance criteria

1. `GET /config/thresholds` returns HTTP 200 with a JSON body of the form:
   ```json
   {
     "low_max": 30,
     "medium_max": 70,
     "high_min": 71
   }
   ```
2. `PUT /config/thresholds` accepts a body with the same three integer fields,
   validates that `low_max < medium_max < high_min` and all values are in
   `[0, 100]`, persists the new values, and returns HTTP 200 with the updated
   config.
3. Invalid bodies (e.g. `low_max >= medium_max`) return HTTP 422.
4. Config is persisted to `a3-polyglot/config/thresholds.json`; the file must
   survive a service restart (i.e., GET reads from disk, not from memory alone).
5. Default config on first start (file absent) is `low_max=30, medium_max=70,
   high_min=71` — matching `contract.md`.
6. All existing tests in `tests/test_api.py` continue to pass without
   modification.
7. Your new tests in `tests/test_thresholds.py` all pass.
8. `ruff check a3-polyglot/routers/thresholds.py a3-polyglot/tests/test_thresholds.py`
   exits 0.

---

## Files you OWN (the only files you may create or modify)

| Path (relative to repo root) | Action |
|-------------------------------|--------|
| `a3-polyglot/routers/thresholds.py` | CREATE |
| `a3-polyglot/config/thresholds.json` | CREATE (default seed file) |
| `a3-polyglot/tests/test_thresholds.py` | CREATE |

**That is the complete list.** Do not modify any other file, including
`a3-polyglot/main.py`. The router registration will be added by the merge
integrator after your branch is reviewed.

---

## Files you must NOT touch

- `a3-polyglot/main.py`
- `a3-polyglot/contract.md`
- `a3-polyglot/requirements.txt`
- `a3-polyglot/routers/export.py` (may not exist yet — do not create it)
- `a3-polyglot/routers/audit.py` (may not exist yet — do not create it)
- `a3-polyglot/audit/log.jsonl`
- `a3-polyglot/tests/test_api.py`
- `a3-polyglot/tests/test_export.py` (may not exist yet)
- `a3-polyglot/tests/test_audit.py` (may not exist yet)
- `a3-polyglot/fraud-engine/**`
- `a3-polyglot/worker/**`
- `a3-polyglot/ui/**`

---

## Implementation guidance

### Default seed file

Commit `a3-polyglot/config/thresholds.json` with the default content:

```json
{
  "low_max": 30,
  "medium_max": 70,
  "high_min": 71
}
```

### Router skeleton

```python
# a3-polyglot/routers/thresholds.py  (skeleton — fill in the body)
from __future__ import annotations
import json
from pathlib import Path
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, model_validator

router = APIRouter()
BASE = Path(__file__).resolve().parent.parent
CONFIG_FILE = BASE / "config" / "thresholds.json"

_DEFAULTS = {"low_max": 30, "medium_max": 70, "high_min": 71}


class ThresholdConfig(BaseModel):
    low_max: int
    medium_max: int
    high_min: int

    @model_validator(mode="after")
    def _check_order(self) -> "ThresholdConfig":
        if not (0 <= self.low_max < self.medium_max < self.high_min <= 100):
            raise ValueError(
                "thresholds must satisfy 0 <= low_max < medium_max < high_min <= 100"
            )
        return self


def _load() -> ThresholdConfig:
    if CONFIG_FILE.exists():
        return ThresholdConfig(**json.loads(CONFIG_FILE.read_text()))
    return ThresholdConfig(**_DEFAULTS)


def _save(cfg: ThresholdConfig) -> None:
    CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_FILE.write_text(cfg.model_dump_json(indent=2))


@router.get("/config/thresholds", response_model=ThresholdConfig, tags=["config"])
def get_thresholds() -> ThresholdConfig:
    return _load()


@router.put("/config/thresholds", response_model=ThresholdConfig, tags=["config"])
def put_thresholds(cfg: ThresholdConfig) -> ThresholdConfig:
    _save(cfg)
    return cfg
```

### Test guidance

`tests/test_thresholds.py` must **not** import or reload `main`. Mount
`routers.thresholds.router` on a minimal `FastAPI()` + `TestClient`, and
monkeypatch `routers.thresholds.CONFIG_FILE` to a path under `tmp_path` so tests
are isolated. Cover:

- GET returns defaults when the config file is absent.
- PUT stores new values; subsequent GET returns them.
- PUT with invalid ordering returns 422.
- PUT with out-of-range values returns 422.

---

## Commit convention

All commits on this branch must follow:

```
feat(thresholds): <imperative summary under 72 chars>
```

Example: `feat(thresholds): add GET/PUT /config/thresholds endpoints`

---

## How to run your tests locally

```bash
cd a3-polyglot
.venv/bin/python -m pytest tests/test_thresholds.py -v
# Full suite regression check:
.venv/bin/python -m pytest -q
```

Lint (bootstrap ruff once — see `constraints.md` §1):
```bash
.venv/bin/pip install 'ruff>=0.4'  # once per worktree
.venv/bin/ruff check routers/thresholds.py tests/test_thresholds.py
```

---

## Definition of done (checklist before opening PR)

- [ ] `a3-polyglot/routers/thresholds.py` exists with both GET and PUT routes.
- [ ] `a3-polyglot/config/thresholds.json` committed with default values.
- [ ] `a3-polyglot/tests/test_thresholds.py` exists with at least 4 test functions.
- [ ] `pytest tests/test_thresholds.py` passes (all green).
- [ ] `pytest tests/test_api.py` still passes (no regression).
- [ ] `ruff check` exits 0 on both owned source files.
- [ ] No modifications to any forbidden file (verify with `git diff main --name-only`).
- [ ] Branch is `feat/lane-b`; at least one commit with the correct prefix.
