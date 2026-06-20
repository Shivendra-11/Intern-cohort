#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
DEST_DIR="$ROOT/api/data/RepoBuilder"

# Prefer fresh local analyze output; fall back to bundled api/data copy.
if [[ -f "$ROOT/workspace/RepoBuilder/dashboard_data.json" ]]; then
  SRC="$ROOT/workspace/RepoBuilder/dashboard_data.json"
elif [[ -f "$ROOT/deploy-data/workspace/RepoBuilder/dashboard_data.json" ]]; then
  SRC="$ROOT/deploy-data/workspace/RepoBuilder/dashboard_data.json"
elif [[ -f "$ROOT/api/data/RepoBuilder/dashboard_data.json" ]]; then
  SRC="$ROOT/api/data/RepoBuilder/dashboard_data.json"
else
  echo "error: no dashboard_data.json found (run analyze or add deploy-data bundle)" >&2
  exit 1
fi

mkdir -p "$DEST_DIR"
DEST_FILE="$DEST_DIR/dashboard_data.json"
if [[ "$SRC" != "$DEST_FILE" ]]; then
  cp "$SRC" "$DEST_FILE"
fi

cd "$ROOT/dashboard"
npm run build
