#!/usr/bin/env bash
# install-parallelops.sh — one-command ParallelOps setup for any target repo.
#
# Usage:
#   ./install-parallelops.sh /path/to/target-repo
#   ./install-parallelops.sh /path/to/target-repo --global-skill
#   ./install-parallelops.sh .                    # install into ParallelOps itself (re-run / repair)
#
# Options:
#   --global-skill   Install /parallelops-eval skill + rule to ~/.cursor/ (all repos)
#   --skip-venv      Copy files only; skip venv + pip + init
#   --skip-skill     Skip copying Cursor skill
#   --skip-gitignore Skip appending .gitignore block
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_ROOT="$SCRIPT_DIR"

GLOBAL_SKILL=0
SKIP_VENV=0
SKIP_SKILL=0
SKIP_GITIGNORE=0
TARGET=""

usage() {
  sed -n '2,12p' "$0" | sed 's/^# \?//'
  exit "${1:-0}"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage 0 ;;
    --global-skill) GLOBAL_SKILL=1; shift ;;
    --skip-venv) SKIP_VENV=1; shift ;;
    --skip-skill) SKIP_SKILL=1; shift ;;
    --skip-gitignore) SKIP_GITIGNORE=1; shift ;;
    -*) echo "Unknown option: $1" >&2; usage 1 ;;
    *)
      if [[ -z "$TARGET" ]]; then
        TARGET="$1"
      else
        echo "Unexpected argument: $1" >&2
        usage 1
      fi
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Error: target repo path required." >&2
  echo "" >&2
  usage 1
fi

if [[ ! -d "$SOURCE_ROOT/parallelops" ]]; then
  echo "Error: parallelops/ not found at $SOURCE_ROOT" >&2
  exit 1
fi

TARGET="$(cd "$TARGET" && pwd)"

if [[ "$TARGET" == "$SOURCE_ROOT" ]]; then
  echo "→ Target is ParallelOps source repo (repair / refresh install)"
fi

echo "╔══════════════════════════════════════════════════════════╗"
echo "║  ParallelOps installer                                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo "  Source: $SOURCE_ROOT"
echo "  Target: $TARGET"
echo ""

# ── 1. Copy framework ──────────────────────────────────────────────────────
echo "▸ Copying parallelops/ package..."
rsync -a --delete \
  --exclude '__pycache__' \
  --exclude '*.pyc' \
  "$SOURCE_ROOT/parallelops/" "$TARGET/parallelops/"

echo "▸ Copying requirements-framework.txt..."
if [[ ! -f "$TARGET/requirements-framework.txt" ]] || ! cmp -s "$SOURCE_ROOT/requirements-framework.txt" "$TARGET/requirements-framework.txt"; then
  cp "$SOURCE_ROOT/requirements-framework.txt" "$TARGET/requirements-framework.txt"
fi

# Optional: copy agent definitions for reference
if [[ -d "$SOURCE_ROOT/.claude/agents" ]]; then
  mkdir -p "$TARGET/.claude/agents"
  for agent in a1-planner.md a2-executor.md; do
    if [[ -f "$SOURCE_ROOT/.claude/agents/$agent" ]]; then
      if [[ ! -f "$TARGET/.claude/agents/$agent" ]] || ! cmp -s "$SOURCE_ROOT/.claude/agents/$agent" "$TARGET/.claude/agents/$agent"; then
        cp "$SOURCE_ROOT/.claude/agents/$agent" "$TARGET/.claude/agents/$agent"
      fi
    fi
  done
  echo "▸ Copied .claude/agents/a1-planner.md, a2-executor.md"
fi

# ── 2. Cursor skill + rule ─────────────────────────────────────────────────
if [[ "$SKIP_SKILL" -eq 0 ]]; then
  # Prefer .cursor/skills (canonical); fall back to .claude/skills
  if [[ -f "$SOURCE_ROOT/.cursor/skills/parallelops-eval/SKILL.md" ]]; then
    SKILL_SRC="$SOURCE_ROOT/.cursor/skills/parallelops-eval"
  else
    SKILL_SRC="$SOURCE_ROOT/.claude/skills/parallelops-eval"
  fi
  RULE_SRC="$SOURCE_ROOT/.cursor/rules/parallelops-eval.mdc"
  if [[ ! -f "$SKILL_SRC/SKILL.md" ]]; then
    echo "Warning: skill not found at $SKILL_SRC — skipping skill install" >&2
  elif [[ "$GLOBAL_SKILL" -eq 1 ]]; then
    mkdir -p "$HOME/.cursor/skills" "$HOME/.claude/skills"
    rsync -a --delete "$SKILL_SRC/" "$HOME/.cursor/skills/parallelops-eval/"
    rsync -a --delete "$SKILL_SRC/" "$HOME/.claude/skills/parallelops-eval/"
    echo "▸ Installed skill → ~/.cursor/skills/parallelops-eval/  (all repos)"
    echo "▸ Installed skill → ~/.claude/skills/parallelops-eval/"
    if [[ -f "$RULE_SRC" ]]; then
      mkdir -p "$HOME/.cursor/rules"
      cp "$RULE_SRC" "$HOME/.cursor/rules/parallelops-eval.mdc"
      echo "▸ Installed rule  → ~/.cursor/rules/parallelops-eval.mdc  (all repos)"
    fi
  else
    mkdir -p "$TARGET/.cursor/skills" "$TARGET/.cursor/rules"
    rsync -a --delete "$SKILL_SRC/" "$TARGET/.cursor/skills/parallelops-eval/"
    echo "▸ Installed skill → $TARGET/.cursor/skills/parallelops-eval/"
    if [[ -f "$RULE_SRC" ]]; then
      cp "$RULE_SRC" "$TARGET/.cursor/rules/parallelops-eval.mdc"
      echo "▸ Installed rule  → $TARGET/.cursor/rules/parallelops-eval.mdc"
    fi
  fi
fi

# ── 3. .gitignore ──────────────────────────────────────────────────────────
GITIGNORE_BLOCK="# ParallelOps framework (added by install-parallelops.sh)
.venv-framework/
.parallelops/worktrees/*
!.parallelops/worktrees/.gitkeep
.parallelops/logs/*
!.parallelops/logs/.gitkeep
.parallelops/sessions/*
!.parallelops/sessions/.gitkeep
.parallelops/artifacts/a1_execution_plan.yaml
.parallelops/artifacts/user_request.json
.parallelops/artifacts/lane_prompts/*
!.parallelops/artifacts/.gitkeep
!.parallelops/artifacts/lane_prompts/.gitkeep"

if [[ "$SKIP_GITIGNORE" -eq 0 ]]; then
  GI="$TARGET/.gitignore"
  if [[ -f "$GI" ]] && grep -q "ParallelOps framework" "$GI" 2>/dev/null; then
    echo "▸ .gitignore already has ParallelOps block — skipping"
  else
    if [[ -f "$GI" ]]; then
      printf '\n%s\n' "$GITIGNORE_BLOCK" >> "$GI"
    else
      printf '%s\n' "$GITIGNORE_BLOCK" > "$GI"
    fi
    echo "▸ Appended ParallelOps entries to .gitignore"
  fi
fi

# ── 4. Python venv + init ──────────────────────────────────────────────────
if [[ "$SKIP_VENV" -eq 0 ]]; then
  PYTHON="${PYTHON312:-/opt/homebrew/bin/python3.12}"
  if ! command -v "$PYTHON" >/dev/null 2>&1; then
    PYTHON="$(command -v python3.12 || command -v python3)"
  fi
  if ! command -v "$PYTHON" >/dev/null 2>&1; then
    echo "Error: python3.12 or python3 not found. Set PYTHON312=/path/to/python3.12" >&2
    exit 1
  fi

  VENV="$TARGET/.venv-framework"
  echo "▸ Creating venv with $PYTHON ..."
  "$PYTHON" -m venv "$VENV"

  echo "▸ Installing dependencies..."
  "$VENV/bin/pip" install -q --upgrade pip
  "$VENV/bin/pip" install -q -r "$TARGET/requirements-framework.txt"

  echo "▸ Running parallelops.cli init ..."
  (cd "$TARGET" && "$VENV/bin/python" -m parallelops.cli init)
fi

# ── Done ───────────────────────────────────────────────────────────────────
echo ""
echo "✅ ParallelOps installed in: $TARGET"
echo ""
echo "Next steps:"
echo "  1. Open $TARGET in Cursor"
echo "  2. In Agent chat:  /parallelops-eval"
echo "       Q1: pick A1–A6  |  Q2: run selected / All / Dashboard / Custom"
echo "  3. Custom worktree only (terminal):"
echo "       cd $TARGET"
echo "       source .venv-framework/bin/activate"
echo "       python -m parallelops.cli wizard          # 9 questions for custom pipeline"
echo "       python -m parallelops.cli plan --request .parallelops/artifacts/user_request.json"
echo "       python -m parallelops.cli approve --execute"
echo ""
if [[ "$GLOBAL_SKILL" -eq 0 && "$SKIP_SKILL" -eq 0 ]]; then
  echo "Tip: re-run with --global-skill to use /parallelops-eval in any repo:"
  echo "  $0 /path/to/repo --global-skill"
  echo ""
fi
