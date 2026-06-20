#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
CLAUDE_DIR="$HOME/.claude"

echo "Installing DevOps-Infra Eval..."

# 1. Create task folders
for d in d1-terraform d2-compose-stack d3-ci-pipeline d4-kubernetes d5-dev-env d6-observability; do
  mkdir -p "$ROOT/$d"
done
mkdir -p "$ROOT/shared/lib"

# 2. Install agent definition files
AGENTS_DIR="$CLAUDE_DIR/agents"
mkdir -p "$AGENTS_DIR"
if [ -d "$ROOT/agents" ]; then
  cp "$ROOT/agents/"*.md "$AGENTS_DIR/" 2>/dev/null || true
fi

# 3. Install skill
SKILL_DIR="$CLAUDE_DIR/skills/devopsinfra-eval"
mkdir -p "$SKILL_DIR"
if [ -f "$ROOT/skill/SKILL.md" ]; then
  cp "$ROOT/skill/SKILL.md" "$SKILL_DIR/SKILL.md"
fi

# 4. Install dashboard deps
if [ -d "$ROOT/dashboard" ]; then
  cd "$ROOT/dashboard"
  if [ -f "package.json" ]; then
    npm install
  fi
  mkdir -p "$ROOT/dashboard/public/reports"
  for d in d1-terraform d2-compose-stack d3-ci-pipeline d4-kubernetes d5-dev-env d6-observability; do
    ln -sfn "$ROOT/$d" "$ROOT/dashboard/public/reports/$d"
  done
fi

echo ""
echo "DevOps-Infra Eval installed."
echo "  Type /devopsinfra-eval in Claude Code to start."
echo "  Run ./serve-eval-dashboard.sh to open the dashboard."
