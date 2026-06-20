# Rollback — First Step (pyproject.toml migration)

**Branch:** `modernize/first-step`  
**First-step commit:** `2003708` (`feat: adopt pyproject.toml with pinned dev deps and ruff config`)  
**Baseline commit:** `eb834b8` (`chore: import legacy baseline`)

---

## Not Yet Merged

Discard the branch and return to legacy baseline:

```bash
cd a4-modernization/target-repo
git checkout main
git branch -D modernize/first-step
```

Remove untracked artifacts created during verification (safe to delete):

```bash
rm -rf .venv .pytest_cache .ruff_cache textkit.egg-info build
```

**Expected state after rollback:** `setup.py` and `requirements.txt` present; `pyproject.toml` absent.

---

## Already Merged

If `2003708` was merged to `main`:

```bash
cd a4-modernization/target-repo
git revert 2003708 --no-edit
```

Or hard-reset only if the commit is the tip and unpushed:

```bash
git reset --hard eb834b8   # destructive — only if no later commits must be kept
```

---

## Demonstrated Rollback (2026-06-17)

```bash
git checkout main
ls -la                    # setup.py + requirements.txt back; no pyproject.toml
pytest -q                 # 3 passed — baseline behavior unchanged
git checkout modernize/first-step
```

See `PROOF.md` §7 for pasted terminal output.
