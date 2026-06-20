# PROOF.md — A4 Repository Modernization Work Log

All output below was captured from commands executed on 2026-06-17.

---

## 1. Tool Versions

```
$ /opt/homebrew/bin/python3.12 --version
Python 3.12.13

$ git --version
git version 2.50.1 (Apple Git-155)
```

---

## 2. Repo Inventory + Legacy Evidence

```
$ cd a4-modernization/target-repo
$ find . -type f -not -path './.git/*' | sort
./README.md
./requirements.txt
./setup.py
./tests/test_core.py
./textkit/__init__.py
./textkit/core.py

$ cat setup.py
from setuptools import setup, find_packages

setup(
    name="textkit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.5",
    ],
)

$ cat requirements.txt
pytest
ruff

$ sed -n '1,40p' textkit/core.py
import os


def slugify(text, sep="-"):
    out = ""
    for ch in text.lower():
        if ch.isalnum():
            out = out + ch
        elif ch == " ":
            out = out + sep
    return out


def word_count(text):
    return len(text.split())


def truncate(text, length=10, suffix="..."):
    if len(text) <= length:
        return text
    return text[:length] + suffix


def read_lines(path):
    full = os.path.join(os.getcwd(), path)
    print("reading %s" % full)
    f = open(full)
    data = f.readlines()
    f.close()
    return data

$ ls -la
total 24
drwxr-xr-x@  8 shivendrakeshari  staff  256 Jun 17 16:06 .
drwxr-xr-x@  6 shivendrakeshari  staff  192 Jun 17 16:06 ..
drwxr-xr-x@ 12 shivendrakeshari  staff  384 Jun 17 16:06 .git
-rw-r--r--@  1 shivendrakeshari  staff  107 Jun 17 16:06 README.md
-rw-r--r--@  1 shivendrakeshari  staff   12 Jun 17 16:06 requirements.txt
-rw-r--r--@  1 shivendrakeshari  staff  273 Jun 17 16:06 setup.py
drwxr-xr-x@  3 shivendrakeshari  staff   96 Jun 17 16:06 tests
drwxr-xr-x@  4 shivendrakeshari  staff  128 Jun 17 16:06 textkit
```

Missing (confirmed by `ls -la`): `.gitignore`, `pyproject.toml`, `.github/`.

---

## 3. Baseline Commit

```
$ cd a4-modernization/target-repo
$ git init -q && git add -A && git commit -q -m "chore: import legacy baseline"
$ git branch -M main
$ git log --oneline
eb834b8 chore: import legacy baseline
```

---

## 4. Prioritized Plan + Chosen Step

Full ranked table: see `FINDINGS.md` § Prioritized Plan.

**Chosen first step:** Migrate `setup.py` + `requirements.txt` → PEP 621 `pyproject.toml` with pinned dev deps (`pytest==9.1.0`, `ruff==0.15.17`), `[tool.ruff]` config, README update. Commit `2003708` on branch `modernize/first-step`.

**Rationale:** Highest Value (5) among low-risk items (Risk ≤ 2). CI and `.gitignore` deferred.

---

## 5. First-Step Diff (`git diff main..modernize/first-step`)

```
diff --git a/README.md b/README.md
index c64a315..4c7df94 100644
--- a/README.md
+++ b/README.md
@@ -4,7 +4,7 @@ Small string utilities.
 
 ## Install
 
-    python setup.py install
+    pip install -e ".[dev]"
 
 ## Test
 
diff --git a/pyproject.toml b/pyproject.toml
new file mode 100644
index 0000000..e1506c0
--- /dev/null
+++ b/pyproject.toml
@@ -0,0 +1,36 @@
+[build-system]
+requires = ["setuptools>=69.0.0", "wheel"]
+build-backend = "setuptools.build_meta"
+
+[project]
+name = "textkit"
+version = "0.1.0"
+description = "Small string utilities."
+readme = "README.md"
+requires-python = ">=3.10"
+classifiers = [
+    "Programming Language :: Python :: 3",
+    "Programming Language :: Python :: 3.10",
+    "Programming Language :: Python :: 3.11",
+    "Programming Language :: Python :: 3.12",
+]
+
+[project.optional-dependencies]
+dev = [
+    "pytest==9.1.0",
+    "ruff==0.15.17",
+]
+
+[tool.setuptools.packages.find]
+where = ["."]
+include = ["textkit*"]
+
+[tool.ruff]
+target-version = "py310"
+line-length = 88
+
+[tool.ruff.lint]
+select = ["E", "F"]
+
+[tool.ruff.lint.per-file-ignores]
+"textkit/__init__.py" = ["F401"]
diff --git a/requirements.txt b/requirements.txt
deleted file mode 100644
index 71cc539..0000000
--- a/requirements.txt
+++ /dev/null
@@ -1,2 +0,0 @@
-pytest
-ruff
diff --git a/setup.py b/setup.py
deleted file mode 100644
index 00bd2a4..0000000
--- a/setup.py
+++ /dev/null
@@ -1,12 +0,0 @@
-from setuptools import setup, find_packages
-
-setup(
-    name="textkit",
-    version="0.1.0",
-    packages=find_packages(),
-    install_requires=[],
-    classifiers=[
-        "Programming Language :: Python :: 2.7",
-        "Programming Language :: Python :: 3.5",
-    ],
-)
```

Standalone artifact: `first-step.patch` (81 lines).

---

## 6. Verification

### 6a. BEFORE (on `main`)

```
$ pip install -q -r requirements.txt
$ pip show pytest | grep -E '^(Name|Version):'
Name: pytest
Version: 9.1.0

$ ls pyproject.toml
ls: pyproject.toml: No such file or directory

$ ruff check . 2>&1 | tail -3
help: Use an explicit re-export: `truncate as truncate`

Found 3 errors.

$ pytest -q
...                                                                      [100%]
3 passed in 0.01s
```

**Before pain demonstrated:** unpinned `requirements.txt` (pytest resolved to 9.1.0 without pin guarantee), no `pyproject.toml`, `ruff check` fails with F401 on re-exports and no project config.

### 6b. AFTER (on `modernize/first-step`, fresh venv)

```
$ rm -rf .venv && /opt/homebrew/bin/python3.12 -m venv .venv && . .venv/bin/activate
$ pip install -e ".[dev]"
Obtaining file:///Users/shivendrakeshari/Desktop/ParallelOps/a4-modernization/target-repo
  Installing build dependencies: finished with status 'done'
  ...
Successfully installed iniconfig-2.3.0 packaging-26.2 pluggy-1.6.0 pygments-2.20.0 pytest-9.1.0 ruff-0.15.17 textkit-0.1.0

$ pip show pytest ruff | grep -E '^(Name|Version):'
Name: pytest
Version: 9.1.0
Name: ruff
Version: 0.15.17

$ pytest -q
...                                                                      [100%]
3 passed in 0.01s

$ ruff check .
All checks passed!
```

### 6c. Fix iteration (kept in log)

Initial `ruff check` after first commit failed with I001 import-sort errors because `select` included `"I"`. Fixed by narrowing to `select = ["E", "F"]` in `pyproject.toml` (no application code changes). Re-ran `ruff check .` → `All checks passed!`

---

## 7. Rollback Demonstration

```
$ git checkout main
Switched to branch 'main'

$ ls -la
total 24
...
-rw-r--r--@  1 shivendrakeshari  staff  107 Jun 17 16:08 README.md
-rw-r--r--@  1 shivendrakeshari  staff   12 Jun 17 16:08 requirements.txt
-rw-r--r--@  1 shivendrakeshari  staff  273 Jun 17 16:08 setup.py
...

$ ls setup.py requirements.txt
requirements.txt
setup.py

$ ls pyproject.toml
ls: pyproject.toml: No such file or directory

$ pytest -q
...                                                                      [100%]
3 passed in 0.01s

$ git checkout modernize/first-step
Switched to branch 'modernize/first-step'

$ ls pyproject.toml
pyproject.toml
```

Rollback confirmed: `main` restored legacy `setup.py` + `requirements.txt`; tests still pass; branch restores `pyproject.toml`.

---

## Commit Reference

| Ref | SHA | Message |
|-----|-----|---------|
| baseline | `eb834b8` | chore: import legacy baseline |
| first step | `2003708` | feat: adopt pyproject.toml with pinned dev deps and ruff config |
