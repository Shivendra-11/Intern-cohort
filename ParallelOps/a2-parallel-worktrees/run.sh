#!/usr/bin/env bash
# A2 — Execute Two Parallel Worktrees
# Documented command sequence actually used (2026-06-17).
# Run from: /Users/shivendrakeshari/Desktop/ParallelOps/a2-parallel-worktrees
set -euo pipefail

ROOT="/Users/shivendrakeshari/Desktop/ParallelOps/a2-parallel-worktrees"
SHARED="/Users/shivendrakeshari/Desktop/ParallelOps/shared/lib/verify.sh"
cd "$ROOT"

# ── 1. Seed sample repo ──────────────────────────────────────────────────────
mkdir -p sample-repo/tests
cat > sample-repo/app.py << 'EOF'
"""Sample app for A2 parallel worktrees eval."""
VERSION = "0.1.0"
FEATURES = []


def get_info():
    return {"version": VERSION, "features": FEATURES}
EOF
cat > sample-repo/tests/test_app.py << 'EOF'
from app import FEATURES, VERSION, get_info


def test_version_is_string():
    assert isinstance(VERSION, str)


def test_get_info_shape():
    info = get_info()
    assert info["version"] == VERSION
    assert isinstance(info["features"], list)
EOF
cd sample-repo
git init -b main
git add .
git commit -m "chore: seed sample repo for A2 worktree eval"
cd "$ROOT"

# ── 2. Create parallel worktrees ─────────────────────────────────────────────
cd sample-repo
git worktree add ../wt-lane-a -b feat/lane-a
git worktree add ../wt-lane-b -b feat/lane-b
git worktree list
cd "$ROOT"

# ── 3. Lane A — own files + shared app.py ────────────────────────────────────
cd wt-lane-a
cat > lane_a_module.py << 'EOF'
"""Lane A owned module — CSV export helper."""


def export_rows(rows):
    return ",".join(str(r) for r in rows)
EOF
cat > app.py << 'EOF'
"""Sample app for A2 parallel worktrees eval."""
VERSION = "0.2.0-a"
FEATURES = ["export"]


def get_info():
    return {"version": VERSION, "features": FEATURES}
EOF
cat > tests/test_lane_a.py << 'EOF'
from lane_a_module import export_rows


def test_export_rows():
    assert export_rows([1, 2, 3]) == "1,2,3"
EOF
python3 -m pytest -q
git add lane_a_module.py app.py tests/test_lane_a.py
git commit -m "feat(export): add lane-a module and register export feature"
cd "$ROOT"

# ── 4. Lane B — own files + same shared app.py ───────────────────────────────
cd wt-lane-b
cat > lane_b_module.py << 'EOF'
"""Lane B owned module — threshold config helper."""


def validate_thresholds(low_max, medium_max, high_min):
    return 0 <= low_max < medium_max < high_min <= 100
EOF
cat > app.py << 'EOF'
"""Sample app for A2 parallel worktrees eval."""
VERSION = "0.2.0-b"
FEATURES = ["thresholds"]


def get_info():
    return {"version": VERSION, "features": FEATURES}
EOF
cat > tests/test_lane_b.py << 'EOF'
from lane_b_module import validate_thresholds


def test_validate_thresholds_ok():
    assert validate_thresholds(30, 70, 71) is True


def test_validate_thresholds_bad():
    assert validate_thresholds(70, 30, 71) is False
EOF
python3 -m pytest -q
git add lane_b_module.py app.py tests/test_lane_b.py
git commit -m "feat(thresholds): add lane-b module and register thresholds feature"
cd "$ROOT"

# ── 5. Merge lane-a, then lane-b (conflict on app.py) ────────────────────────
cd sample-repo
git checkout main
git merge --no-ff feat/lane-a -m "feat(export): merge lane-a CSV export feature"
git merge --no-ff feat/lane-b -m "feat(thresholds): merge lane-b threshold feature" || true

# Resolve conflict: combine both lane features
cat > app.py << 'EOF'
"""Sample app for A2 parallel worktrees eval."""
VERSION = "0.2.0"
FEATURES = ["export", "thresholds"]


def get_info():
    return {"version": VERSION, "features": FEATURES}
EOF
git add app.py
git commit -m "feat: resolve app.py conflict by combining lane-a and lane-b features"

# ── 6. Post-merge verify (verify.sh needs root test_*.py + .venv) ─────────────
cat > test_integration.py << 'EOF'
from app import FEATURES, VERSION, get_info
from lane_a_module import export_rows
from lane_b_module import validate_thresholds


def test_merged_features():
    assert VERSION == "0.2.0"
    assert set(FEATURES) == {"export", "thresholds"}


def test_lane_modules():
    assert export_rows(["a", "b"]) == "a,b"
    assert validate_thresholds(30, 70, 71) is True
EOF
python3 -m venv .venv
.venv/bin/pip install -q pytest
git add test_integration.py
git commit -m "test: add root integration tests for verify.sh detection"
cd "$ROOT"
bash "$SHARED" sample-repo

# ── 7. Clean up worktrees ────────────────────────────────────────────────────
cd sample-repo
git worktree remove ../wt-lane-a
git worktree remove ../wt-lane-b
git worktree list

echo "A2 run complete."
