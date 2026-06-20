#!/usr/bin/env bash
# Public link — no domain needed. Uses free random trycloudflare.com URL.
# Usage: ./share-ui.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load-env.sh"
load_root_env "$ROOT"
PIDS_DIR="$ROOT/.devopsinfra/pids"
LOG="$ROOT/.devopsinfra/tunnel.log"
LINK_FILE="$ROOT/.devopsinfra/LIVE-LINK.txt"
PORT="${PORT:-5173}"

mkdir -p "$PIDS_DIR"

if ! curl -sf "http://127.0.0.1:${PORT}/" >/dev/null 2>&1; then
  echo "Dashboard not running. Start it first:"
  echo "  ./run-all-ui.sh"
  exit 1
fi

if ! command -v cloudflared >/dev/null 2>&1; then
  echo "Installing cloudflared (one-time)..."
  brew install cloudflared
fi

# Stop old tunnel if any
if [ -f "$PIDS_DIR/tunnel.pid" ]; then
  kill "$(cat "$PIDS_DIR/tunnel.pid")" 2>/dev/null || true
  rm -f "$PIDS_DIR/tunnel.pid"
fi

echo "Creating public link (no domain required)..."
: > "$LOG"
cloudflared tunnel --url "http://127.0.0.1:${PORT}" >>"$LOG" 2>&1 &
echo $! > "$PIDS_DIR/tunnel.pid"

PUBLIC_URL=""
for _ in $(seq 1 45); do
  PUBLIC_URL=$(grep -oE 'https://[a-z0-9-]+\.trycloudflare\.com' "$LOG" 2>/dev/null | head -1 || true)
  [ -n "$PUBLIC_URL" ] && break
  sleep 1
done

if [ -z "$PUBLIC_URL" ]; then
  echo "Could not get public URL. Check: $LOG"
  exit 1
fi

HUB="${PUBLIC_URL}/hub"
{
  echo "PUBLIC_LINK=${HUB}"
  echo "DASHBOARD=${PUBLIC_URL}/"
  echo "CREATED=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
} > "$LINK_FILE"

echo ""
echo "══════════════════════════════════════════════════════════"
echo "  SHARE THIS LINK (anyone can open it):"
echo ""
echo "  ${HUB}"
echo ""
echo "  Main UI:  ${PUBLIC_URL}/"
echo "══════════════════════════════════════════════════════════"
echo ""
echo "Saved to: .devopsinfra/LIVE-LINK.txt"
echo "Keep this terminal open OR leave tunnel running in background."
echo "Stop tunnel: ./stop-all-ui.sh"
echo ""

# If run interactively, follow tunnel log; if sourced/background, exit
if [ "${1:-}" != "--bg" ]; then
  tail -f "$LOG"
fi
