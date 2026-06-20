#!/usr/bin/env bash
# D2 end-to-end test: API → worker → DB cross-service proof
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
LOG="$ROOT/tests/e2e_test.log"
mkdir -p "$ROOT/logs"

exec > >(tee "$LOG") 2>&1

echo "=== D2 E2E Test ==="
echo "Started: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

wait_for_api() {
  local i
  for i in $(seq 1 30); do
    if curl -sf http://localhost:8000/health >/dev/null 2>&1; then
      echo "API ready after ${i}s"
      return 0
    fi
    sleep 1
  done
  echo "FAIL: API not ready on :8000"
  return 1
}

# 1. Start stack
docker compose up -d --build
wait_for_api

# 2. Create job
RESP=$(curl -sf -X POST http://localhost:8000/jobs \
  -H "Content-Type: application/json" \
  -d '{"payload": {"test": "e2e"}}')
echo "POST /jobs response: $RESP"
JOB_ID=$(echo "$RESP" | python3 -c "import sys,json; print(json.load(sys.stdin)['job_id'])")
echo "job_id=$JOB_ID"

# 3. Wait for worker
sleep 6

# 4. Verify processed
STATUS=$(curl -sf "http://localhost:8000/jobs/${JOB_ID}" | python3 -c "import sys,json; print(json.load(sys.stdin)['status'])")
echo "GET /jobs/${JOB_ID} status=$STATUS"
if [ "$STATUS" != "processed" ]; then
  echo "FAIL: expected status=processed got $STATUS"
  exit 1
fi

# 5. Cross-service log proof
docker compose logs worker 2>&1 | tee "$ROOT/logs/cross-service.log"
if ! grep -q "processed job ${JOB_ID}" "$ROOT/logs/cross-service.log"; then
  echo "FAIL: worker log missing 'processed job ${JOB_ID}'"
  exit 1
fi

# 6. Teardown
docker compose down -v
echo "=== ALL 5 ASSERTIONS PASSED ==="
