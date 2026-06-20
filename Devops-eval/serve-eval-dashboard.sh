#!/usr/bin/env bash
# serve-eval-dashboard.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
DASH="$ROOT/dashboard"

# Symlink task report folders into public/ (avoid repo-root symlink — breaks Vite build)
mkdir -p "$DASH/public/reports"
for d in d1-terraform d2-compose-stack d3-ci-pipeline d4-kubernetes d5-dev-env d6-observability; do
  ln -sfn "$ROOT/$d" "$DASH/public/reports/$d"
done

cd "$DASH"
if [ ! -d node_modules ]; then
  echo "Installing dashboard dependencies..."
  npm install
fi

echo ""
echo "  DevOps-Infra Eval Dashboard"
echo "  http://localhost:5173"
echo ""
npm run dev
