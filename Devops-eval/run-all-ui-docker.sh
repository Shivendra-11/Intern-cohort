#!/usr/bin/env bash
# Full stack via Docker (D2 compose + D6 compose + D4 kind) — requires working docker pull
set -euo pipefail
ROOT="$(cd "$(dirname "$0")" && pwd)"

if ! docker info >/dev/null 2>&1; then
  colima start --cpu 4 --memory 6 2>/dev/null || true
fi

cd "$ROOT/d2-compose-stack" && docker-compose up -d --build
cd "$ROOT/d6-observability" && docker-compose -f docker-compose.obs.yml -f docker-compose.override.yml up -d --build

if ! kind get clusters 2>/dev/null | grep -qx devops-eval; then
  kind create cluster --name devops-eval
fi
kubectl apply -f "$ROOT/d4-kubernetes/manifests/"
kubectl rollout status deployment/devops-eval-app -n devops-eval --timeout=120s
kubectl port-forward svc/devops-eval-svc 8080:80 -n devops-eval &
echo $! > "$ROOT/.devopsinfra/pids/d4-pf.pid"

echo "Docker stacks up. Run ./run-all-ui.sh for local APIs + dashboard."
