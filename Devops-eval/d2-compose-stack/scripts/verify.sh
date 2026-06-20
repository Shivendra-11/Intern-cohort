#!/usr/bin/env bash
# D2 verification: docker-compose E2E (preferred) or native postgres fallback
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG_DIR="$ROOT/logs"
mkdir -p "$LOG_DIR"

export PATH="/opt/homebrew/opt/postgresql@16/bin:$PATH"

try_docker_e2e() {
  if ! command -v docker >/dev/null 2>&1 || ! docker info >/dev/null 2>&1; then
    return 1
  fi
  if ! docker image inspect postgres:16-alpine >/dev/null 2>&1; then
    if command -v skopeo >/dev/null 2>&1; then
      echo "Loading postgres:16-alpine via skopeo..."
      local tar="/tmp/skopeo-postgres.tar"
      skopeo copy --src-tls-verify=false --override-os linux --override-arch arm64 \
        docker://postgres:16-alpine "docker-archive:${tar}" && docker load -i "$tar"
      docker tag "$(docker load -i "$tar" 2>&1 | awk '/Loaded image/ {print $NF}')" postgres:16-alpine 2>/dev/null || true
    fi
  fi
  if docker image inspect postgres:16-alpine >/dev/null 2>&1; then
    echo "Running docker-compose E2E..."
    chmod +x tests/e2e_test.sh
    ./tests/e2e_test.sh 2>&1 | tee "$LOG_DIR/e2e-docker.log"
    return 0
  fi
  return 1
}

run_native_e2e() {
  echo "=== D2 Native E2E (API + Postgres + Worker) ===" | tee "$LOG_DIR/e2e-native.log"
  PGDATA="${PGDATA:-/tmp/devops-eval-pgdata}"
  PGPORT="${PGPORT:-55432}"
  API_PORT="${API_PORT:-8000}"
  export DATABASE_URL="postgresql://postgres@127.0.0.1:${PGPORT}/devops_eval"

  cleanup() {
    [ -n "${API_PID:-}" ] && kill "$API_PID" 2>/dev/null || true
    [ -n "${WORKER_PID:-}" ] && kill "$WORKER_PID" 2>/dev/null || true
    if [ -d "$PGDATA" ]; then
      pg_ctl -D "$PGDATA" -m fast stop 2>/dev/null || true
      rm -rf "$PGDATA"
    fi
  }
  trap cleanup EXIT

  rm -rf "$PGDATA"
  initdb -D "$PGDATA" -U postgres --auth=trust >/dev/null
  pg_ctl -D "$PGDATA" -o "-p ${PGPORT} -k /tmp" -w start >/dev/null
  createdb -h 127.0.0.1 -p "$PGPORT" -U postgres devops_eval
  psql -h 127.0.0.1 -p "$PGPORT" -U postgres -d devops_eval -f "$ROOT/db/seed.sql"

  python3 -m pip install -q -r "$ROOT/api/requirements.txt" -r "$ROOT/worker/requirements.txt"

  (
    cd "$ROOT/api"
    DATABASE_URL="$DATABASE_URL" python3 -m uvicorn app.main:app --host 127.0.0.1 --port "$API_PORT"
  ) >"$LOG_DIR/api.log" 2>&1 &
  API_PID=$!

  (
    cd "$ROOT/worker"
    DATABASE_URL="$DATABASE_URL" POLL_INTERVAL=1 python3 src/worker.py
  ) >"$LOG_DIR/worker.log" 2>&1 &
  WORKER_PID=$!

  for i in $(seq 1 30); do
    curl -sf "http://127.0.0.1:${API_PORT}/health" >/dev/null && break
    sleep 1
  done

  RESP=$(curl -sf -X POST "http://127.0.0.1:${API_PORT}/jobs" \
    -H "Content-Type: application/json" \
    -d '{"payload": {"test": "e2e"}}')
  echo "POST /jobs response: $RESP" | tee -a "$LOG_DIR/e2e-native.log"
  JOB_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")

  sleep 4
  STATUS=$(curl -sf "http://127.0.0.1:${API_PORT}/jobs/${JOB_ID}" \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
  echo "GET /jobs/${JOB_ID} status=$STATUS" | tee -a "$LOG_DIR/e2e-native.log"
  [ "$STATUS" = "processed" ] || { echo "FAIL: status=$STATUS"; exit 1; }

  grep "processed job ${JOB_ID}" "$LOG_DIR/worker.log" | tee "$LOG_DIR/cross-service.log"
  grep -q "processed job ${JOB_ID}" "$LOG_DIR/cross-service.log"

  echo "=== ALL 5 ASSERTIONS PASSED (native) ===" | tee -a "$LOG_DIR/e2e-native.log"
}

if try_docker_e2e; then
  MODE="docker"
else
  echo "Docker E2E unavailable; using native postgres fallback"
  run_native_e2e
  MODE="native"
fi

echo "VERIFY_MODE=$MODE"
echo "D2 verification complete"
