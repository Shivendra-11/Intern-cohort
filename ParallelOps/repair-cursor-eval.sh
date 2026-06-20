#!/usr/bin/env bash
# Copy correct /parallelops-eval rule + skill into a target repo (fixes old 14-question flow).
#
# Usage:
#   ./repair-cursor-eval.sh /path/to/your-repo
#   ./repair-cursor-eval.sh .                 # current directory
#   ./repair-cursor-eval.sh /path/to/repo --global
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE="$SCRIPT_DIR"
GLOBAL=0
TARGET=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --global) GLOBAL=1; shift ;;
    -h|--help)
      echo "Usage: $0 /path/to/repo [--global]"
      exit 0
      ;;
    *)
      if [[ -z "$TARGET" ]]; then TARGET="$1"; else echo "Unexpected: $1" >&2; exit 1; fi
      shift
      ;;
  esac
done

if [[ -z "$TARGET" ]]; then
  echo "Error: pass target repo path (not /path/to/your-repo placeholder)" >&2
  echo "  $0 /Users/you/Desktop/Devliker_fullstack" >&2
  exit 1
fi

TARGET="$(cd "$TARGET" && pwd)"
RULE_SRC="$SOURCE/.cursor/rules/parallelops-eval.mdc"
SKILL_SRC="$SOURCE/.cursor/skills/parallelops-eval"

if [[ ! -f "$RULE_SRC" ]]; then
  echo "Error: missing $RULE_SRC" >&2
  exit 1
fi

mkdir -p "$TARGET/.cursor/rules" "$TARGET/.cursor/skills/parallelops-eval"
cp "$RULE_SRC" "$TARGET/.cursor/rules/parallelops-eval.mdc"
rsync -a "$SKILL_SRC/" "$TARGET/.cursor/skills/parallelops-eval/"

echo "✅ Installed parallelops-eval rule + skill → $TARGET/.cursor/"
echo ""
echo "Verify (must NOT say '14 discovery questions' as default):"
head -3 "$TARGET/.cursor/rules/parallelops-eval.mdc"
echo "..."
grep -n "dashboard" "$TARGET/.cursor/rules/parallelops-eval.mdc" | head -3

if [[ "$GLOBAL" -eq 1 ]]; then
  mkdir -p "$HOME/.cursor/rules" "$HOME/.cursor/skills/parallelops-eval"
  cp "$RULE_SRC" "$HOME/.cursor/rules/parallelops-eval.mdc"
  rsync -a "$SKILL_SRC/" "$HOME/.cursor/skills/parallelops-eval/"
  echo "✅ Also updated ~/.cursor/rules/ and ~/.cursor/skills/"
fi

echo ""
echo "Next: open $TARGET in Cursor → NEW chat → /parallelops-eval"
echo "  One combined picker: A1–A6 + All + Dashboard UI + Dashboard-from-MD + Custom"
