#!/usr/bin/env bash
# Generate load: ~50 req/s for 30 seconds
set -euo pipefail
URL="${1:-http://localhost:8000/}"
echo "Load test against $URL for 30s..."
end=$((SECONDS + 30))
count=0
while [ $SECONDS -lt $end ]; do
  for _ in $(seq 1 50); do
    curl -sf "$URL" >/dev/null &
    count=$((count + 1))
  done
  wait
  sleep 1
done
echo "Total requests: $count"
