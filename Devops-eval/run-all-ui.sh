#!/usr/bin/env bash
# Start all DevOps-Infra Eval UIs (local mode — no Docker required)
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
# shellcheck disable=SC1091
source "$ROOT/scripts/load-env.sh"
load_root_env "$ROOT"
PIDS_DIR="$ROOT/.devopsinfra/pids"
mkdir -p "$PIDS_DIR"

log() { echo "[run-all-ui] $*"; }
start_bg() {
  local name=$1
  shift
  log "Starting $name..."
  "$@" &
  echo $! > "$PIDS_DIR/$name.pid"
}

# Stop previous instances
"$ROOT/stop-all-ui.sh" 2>/dev/null || true
mkdir -p "$PIDS_DIR"

SHARE=false
for arg in "$@"; do
  case "$arg" in
    --share) SHARE=true ;;
  esac
done

# ── D6 observability service (:8001) ─────────────────────────────
cd "$ROOT/d6-observability/service"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
start_bg d6-api uvicorn app:app --host 127.0.0.1 --port "${D6_API_PORT:-8001}"

# ── D2 API (:8000) — UI/docs (DB routes need compose postgres) ───
cd "$ROOT/d2-compose-stack/api"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
start_bg d2-api uvicorn app.main:app --host 127.0.0.1 --port "${D2_API_PORT:-8000}"

# ── D3 CI app (:8002) ───────────────────────────────────────────
cd "$ROOT/d3-ci-pipeline"
[ -d .venv ] || python3 -m venv .venv
source .venv/bin/activate
pip install -q fastapi uvicorn
start_bg d3-api env PYTHONPATH=. uvicorn app.main:app --host 127.0.0.1 --port "${D3_API_PORT:-8002}"

# ── Prometheus (:9090) ────────────────────────────────────────────
if command -v prometheus >/dev/null; then
  start_bg prometheus prometheus \
    --config.file="$ROOT/d6-observability/prometheus/prometheus-local.yml" \
    --web.listen-address=127.0.0.1:9090 \
    --storage.tsdb.path="$ROOT/.devopsinfra/prometheus-data"
fi

# ── Grafana (:3000) ───────────────────────────────────────────────
if command -v grafana >/dev/null; then
  export GF_SECURITY_ADMIN_PASSWORD="${GF_SECURITY_ADMIN_PASSWORD:-admin}"
  export GF_SECURITY_ADMIN_USER="${GF_SECURITY_ADMIN_USER:-admin}"
  GRAFANA_PREFIX="$(brew --prefix grafana)"
  start_bg grafana grafana server \
    --homepath "$GRAFANA_PREFIX/share/grafana" \
    --config "/opt/homebrew/etc/grafana/grafana.ini"
fi

# Load test for D6 metrics
sleep 2
chmod +x "$ROOT/d6-observability/load.sh"
"$ROOT/d6-observability/load.sh" http://127.0.0.1:8001/ || true

# ── Eval dashboard (:5173) ────────────────────────────────────────
mkdir -p "$ROOT/dashboard/public/reports"
for d in d1-terraform d2-compose-stack d3-ci-pipeline d4-kubernetes d5-dev-env d6-observability; do
  ln -sfn "$ROOT/$d" "$ROOT/dashboard/public/reports/$d"
done
cd "$ROOT/dashboard"
start_bg dashboard npm run dev -- --host 127.0.0.1 --port "${PORT:-5173}"

sleep 4

log ""
log "══════════════════════════════════════════════════════════"
log "  DevOps-Infra Eval — ALL UIs (local mode)"
log "══════════════════════════════════════════════════════════"
log "  ★ Eval dashboard (main)  http://localhost:5173"
log "  ★ Services hub (all links) http://localhost:5173/hub"
log "  D2 Compose API           http://localhost:8000/docs"
log "  D3 CI app                http://localhost:8002/docs"
log "  D6 /metrics              http://localhost:8001/metrics"
log "  Prometheus               http://localhost:9090"
log "  Grafana (admin/admin)    http://localhost:3000"
log "══════════════════════════════════════════════════════════"
log "  Docker mode (full D2/D4/D6): fix TLS then ./run-all-ui-docker.sh"
log "  Stop: ./stop-all-ui.sh"
log ""

if [ "$SHARE" = true ]; then
  "$ROOT/share-ui.sh" --bg
  if [ -f "$ROOT/.devopsinfra/LIVE-LINK.txt" ]; then
    # shellcheck disable=SC1091
    source "$ROOT/.devopsinfra/LIVE-LINK.txt"
    log "  ★ PUBLIC LINK (share): ${PUBLIC_LINK:-see .devopsinfra/LIVE-LINK.txt}"
    log ""
  fi
fi

# Keep script alive
wait
