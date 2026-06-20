# A4 first step — pointer

The implemented modernization first step lives on branch **`modernize/first-step`**
inside **`target-repo/`**, not in this folder.

| Artifact | Path |
|----------|------|
| Findings + priority matrix | [../FINDINGS.md](../FINDINGS.md) |
| Command log + before/after proof | [../PROOF.md](../PROOF.md) |
| Rollback steps | [../ROLLBACK.md](../ROLLBACK.md) |
| Standalone patch | [../first-step.patch](../first-step.patch) |
| Modernized repo | [../target-repo/](../target-repo/) (branch `modernize/first-step`) |

**First step implemented:** migrate legacy `setup.py` → PEP 621 `pyproject.toml` with
pinned dev deps and Ruff config; README install line updated.
