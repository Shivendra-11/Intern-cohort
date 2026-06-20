#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"
PIDS="$ROOT/.devopsinfra/pids"

for f in "$PIDS"/*.pid; do
  [ -f "$f" ] || continue
  pid=$(cat "$f")
  kill "$pid" 2>/dev/null || true
  rm -f "$f"
done

pkill -f "vite.*5173" 2>/dev/null || true
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "uvicorn.*8001" 2>/dev/null || true
pkill -f "uvicorn.*8002" 2>/dev/null || true
pkill -f "prometheus.*9090" 2>/dev/null || true
pkill -f "grafana server" 2>/dev/null || true

pkill -f "cloudflared tunnel" 2>/dev/null || true
if [ -f "$PIDS/tunnel.pid" ]; then
  kill "$(cat "$PIDS/tunnel.pid")" 2>/dev/null || true
  rm -f "$PIDS/tunnel.pid"
fi

cd "$ROOT/d2-compose-stack" && docker-compose down -v 2>/dev/null || true
cd "$ROOT/d6-observability" && docker-compose -f docker-compose.obs.yml -f docker-compose.override.yml down -v 2>/dev/null || true
kind delete cluster --name devops-eval 2>/dev/null || true

echo "All services stopped."
