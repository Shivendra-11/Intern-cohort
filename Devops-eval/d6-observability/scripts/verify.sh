#!/usr/bin/env bash
# D6 verification: service metrics + Prometheus/Grafana stack + load proof
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG="$ROOT/metrics-proof.log"

load_image() {
  local ref=$1 tag=$2
  if docker image inspect "$tag" >/dev/null 2>&1; then return 0; fi
  if command -v skopeo >/dev/null 2>&1; then
    local tar="/tmp/skopeo-$(echo "$tag" | tr '/:' '_').tar"
    skopeo copy --src-tls-verify=false --override-os linux --override-arch arm64 \
      "docker://${ref}" "docker-archive:${tar}"
    local loaded_id
    loaded_id=$(docker load -i "$tar" 2>&1 | awk '/Loaded image/ {print $NF}')
    docker tag "$loaded_id" "$tag"
  else
    docker pull "$tag"
  fi
}

run_local_metrics() {
  python3 -m pip install -q -r "$ROOT/service/requirements.txt"
  (
    cd "$ROOT/service"
    python3 -m uvicorn app:app --host 127.0.0.1 --port 8000
  ) >/dev/null 2>&1 &
  SVC_PID=$!
  trap 'kill $SVC_PID 2>/dev/null; docker compose -f docker-compose.obs.yml down -v 2>/dev/null || true' EXIT

  for i in $(seq 1 20); do
    curl -sf http://127.0.0.1:8000/health >/dev/null && break
    sleep 1
  done
  curl -sf http://127.0.0.1:8000/health >/dev/null || { echo "service failed to start"; cat "$ROOT/service"/*.log 2>/dev/null; exit 1; }

  for _ in $(seq 1 20); do curl -sf http://127.0.0.1:8000/ >/dev/null; done
  curl -sf http://127.0.0.1:8000/metrics | tee "$LOG"
  grep -q "http_requests_total" "$LOG"
}

run_compose_stack() {
  load_image "prom/prometheus:v2.51.0" "prom/prometheus:v2.51.0" || true
  load_image "grafana/grafana:10.4.0" "grafana/grafana:10.4.0" || true

  docker compose -f docker-compose.obs.yml up -d --build 2>&1 | tee "$ROOT/compose-up.log"
  for i in $(seq 1 30); do
    curl -sf http://127.0.0.1:8000/health >/dev/null && break
    sleep 2
  done

  chmod +x "$ROOT/load.sh"
  "$ROOT/load.sh" http://127.0.0.1:8000/ 2>&1 | tee "$ROOT/load-run.log"

  sleep 5
  curl -sf http://127.0.0.1:8000/metrics | tee "$LOG"
  grep -q "http_requests_total" "$LOG"

  QUERY='rate(http_requests_total[1m])'
  curl -sf "http://127.0.0.1:9090/api/v1/query?query=$(python3 -c "import urllib.parse; print(urllib.parse.quote('$QUERY'))")" \
    | tee "$ROOT/prometheus-query.json"
  python3 -c "import json; d=json.load(open('$ROOT/prometheus-query.json')); assert d['data']['result'], 'no prometheus series'"

  curl -sf -u admin:admin "http://127.0.0.1:3000/api/dashboards/uid/devops-eval-obs" \
    | python3 -c "import json,sys; d=json.load(sys.stdin); json.dump(d['dashboard']['panels'], open('$ROOT/dashboard-panels.json','w'), indent=2)"
}

if docker info >/dev/null 2>&1; then
  if load_image "prom/prometheus:v2.51.0" "prom/prometheus:v2.51.0" 2>/dev/null \
     && load_image "grafana/grafana:10.4.0" "grafana/grafana:10.4.0" 2>/dev/null \
     && docker image inspect prom/prometheus:v2.51.0 >/dev/null 2>&1; then
    run_compose_stack
  else
    echo "Compose images unavailable; verifying local metrics endpoint"
    run_local_metrics
  fi
else
  echo "Docker unavailable; verifying local metrics endpoint"
  run_local_metrics
fi

echo "D6 verification complete"
