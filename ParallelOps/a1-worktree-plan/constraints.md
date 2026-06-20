# Shared Constraints — Fraud-Score System Extensions

These rules apply to every lane (A, B, C) equally. An agent on any lane must
follow all of them. The merge integrator enforces them before each merge.

---

## 1. Python lint standard

**Tool:** `ruff` (not listed in `requirements.txt` yet — bootstrap once per
worktree before the first lane commit).

**Bootstrap (run once after `pip install -r requirements.txt`):**
```bash
cd a3-polyglot
.venv/bin/pip install 'ruff>=0.4'
```

**Invocation:**
```bash
cd a3-polyglot
.venv/bin/ruff check <file(s)>
```

**Requirement:** `ruff check` must exit 0 on every owned Python file before a
commit is considered clean. No `# noqa` suppressions are permitted unless a
comment explains why the rule cannot be satisfied.

**Scope:** applies to all `.py` files created or modified by the lane. Files
not owned by the lane are not checked by that lane. Do **not** add `ruff` to
`requirements.txt` from a lane branch (see §5).

---

## 2. Commit message convention

Format: `<type>(<scope>): <imperative summary>`

| Lane | Required type | Required scope |
|------|--------------|----------------|
| A    | `feat`       | `export`       |
| B    | `feat`       | `thresholds`   |
| C    | `feat`       | `audit`        |

Rules:
- Summary line <= 72 characters.
- Imperative mood (e.g. "add", "implement", "fix"), not past tense.
- No period at end of summary line.
- If a body is included, separate it from the summary with a blank line.
- Fix commits (if needed) use `fix(<scope>): ...` with the same scope.

---

## 3. No shared-schema edits without cross-lane sign-off

`a3-polyglot/contract.md` is the authoritative data contract for the entire
pipeline. It may not be modified by any lane agent. Changes to `contract.md`
require explicit written sign-off from the repository owner and must land in a
separate commit outside all three feature branches.

Similarly, `a3-polyglot/main.py` is frozen to all lane agents. Additions to
`main.py` (router registrations, import statements) are performed exclusively
by the merge integrator in the merge commit for each lane.

---

## 4. Test gate (must pass before merge is approved)

Each merge is blocked until all of the following commands exit 0:

```bash
# From a3-polyglot/  (repo root is one level up: ParallelOps/)
.venv/bin/python -m pytest -q                 # all Python tests
bash ../shared/lib/verify.sh .                # stack-aware runner (Python + Rust + Node)
```

The Node test suite (`npm test` inside `worker/`) is not required to pass for
lane merges because no lane modifies `worker/`. It must not newly fail as a
side-effect.

A lane is also blocked if `git diff main --name-only` (before merge) shows
modifications to any file the lane does not own.

---

## 5. No new runtime dependencies without approval

No new entries may be added to `a3-polyglot/requirements.txt` or
`a3-polyglot/worker/package.json` or `a3-polyglot/fraud-engine/Cargo.toml`
without explicit approval. All three new features (CSV export, threshold config,
audit log) are implementable with the Python standard library and the packages
already listed in `requirements.txt`.

---

## 6. Test isolation

Every new test must use a temporary directory or monkeypatched path for any
file-system state (queue dirs, config files, audit log). Tests must not
read from or write to the real `a3-polyglot/queue/`, `a3-polyglot/config/`, or
`a3-polyglot/audit/` directories. Use `tmp_path` (pytest) and `monkeypatch`.

---

## 7. Backwards compatibility

No lane may change the HTTP status codes, response shapes, or field names of any
pre-existing endpoint (`POST /transaction`, `GET /transaction/{txn_id}`,
`GET /transactions`, `GET /health`, `GET /run-tests`). All existing tests in
`tests/test_api.py` must continue to pass unchanged after any lane's work is
merged.

---

## 8. File creation hygiene

- Do not commit `.pyc` files, `__pycache__/` directories, or `.pytest_cache/`
  contents (covered by `.gitignore`).
- `audit/log.jsonl` must not be committed with content; only `audit/.gitkeep`
  is committed by Lane C.
- `config/thresholds.json` committed by Lane B must contain only the default
  values (`low_max=30, medium_max=70, high_min=71`).
