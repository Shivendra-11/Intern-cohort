#!/usr/bin/env bash
# D4 verification: kubeconform + kind cluster apply + curl proof
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
CLUSTER_NAME="${KIND_CLUSTER_NAME:-devops-eval}"
MANIFESTS="$ROOT/manifests"

load_image() {
  local ref=$1 tag=$2
  if docker image inspect "$tag" >/dev/null 2>&1; then
    return 0
  fi
  if command -v skopeo >/dev/null 2>&1; then
    echo "Loading $tag via skopeo..."
    local tar="/tmp/skopeo-$(echo "$tag" | tr '/:' '_').tar"
    skopeo copy --src-tls-verify=false --override-os linux --override-arch arm64 \
      "docker://${ref}" "docker-archive:${tar}" && docker load -i "$tar"
    local loaded_id
    loaded_id=$(docker load -i "$tar" 2>&1 | awk '/Loaded image/ {print $NF}')
    docker tag "$loaded_id" "$tag" 2>/dev/null || docker tag "$(docker images -q | head -1)" "$tag"
  else
    docker pull "$tag"
  fi
}

echo "=== D4 Step 1: kubeconform validation ===" | tee "$ROOT/dry-run.log"
kubeconform -summary -kubernetes-version 1.29.0 "$MANIFESTS"/*.yaml 2>&1 | tee -a "$ROOT/dry-run.log"

echo "=== D4 Step 2: kind cluster + apply ===" | tee "$ROOT/apply.log"
if ! command -v kind >/dev/null 2>&1; then
  echo "kind not installed" | tee -a "$ROOT/apply.log"
  exit 1
fi

load_image "kindest/node:v1.29.2" "kindest/node:v1.29.2" || true
load_image "nginx:alpine" "nginx:alpine" || true

if kind get clusters 2>/dev/null | grep -qx "$CLUSTER_NAME"; then
  kind delete cluster --name "$CLUSTER_NAME"
fi

kind create cluster --name "$CLUSTER_NAME" --image kindest/node:v1.29.2 2>&1 | tee -a "$ROOT/apply.log"
kind load docker-image nginx:alpine --name "$CLUSTER_NAME" 2>&1 | tee -a "$ROOT/apply.log"

echo "=== kubectl dry-run (client) ===" | tee -a "$ROOT/dry-run.log"
kubectl apply -f "$MANIFESTS/" --dry-run=client 2>&1 | tee -a "$ROOT/dry-run.log"

kubectl apply -f "$MANIFESTS/namespace.yaml" 2>&1 | tee -a "$ROOT/apply.log"
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/devops-eval --timeout=60s 2>&1 | tee -a "$ROOT/apply.log"
kubectl apply -f "$MANIFESTS/configmap.yaml" -f "$MANIFESTS/deployment.yaml" -f "$MANIFESTS/service.yaml" -f "$MANIFESTS/ingress.yaml" 2>&1 | tee -a "$ROOT/apply.log"
kubectl rollout status deployment/devops-eval-app -n devops-eval --timeout=120s 2>&1 | tee -a "$ROOT/apply.log"

echo "=== D4 Step 4: curl proof ===" | tee "$ROOT/curl-proof.log"
kubectl port-forward svc/devops-eval-svc 18080:80 -n devops-eval >/dev/null 2>&1 &
PF_PID=$!
sleep 3
curl -sf http://127.0.0.1:18080/ | tee -a "$ROOT/curl-proof.log"
kill "$PF_PID" 2>/dev/null || true

echo "=== D4 verification complete ==="
