# D4 — Kubernetes Manifests (60m)

## Cluster tool
`kind` (Kubernetes IN Docker) — local cluster named `devops-eval`

## Manifests (in manifests/)
- `deployment.yaml` — 2 replicas, resource requests/limits, readiness probe
- `service.yaml`    — ClusterIP on port 80
- `configmap.yaml`  — App environment config
- `ingress.yaml`    — kind-nginx ingress (optional)

## Namespace
`devops-eval`

## Verification sequence
```bash
# 1. Create kind cluster
kind create cluster --name devops-eval

# 2. Dry-run validate
kubectl apply -f manifests/ --dry-run=client 2>&1 | tee dry-run.log

# 3. Apply
kubectl create namespace devops-eval
kubectl apply -f manifests/ 2>&1 | tee apply.log

# 4. Wait for rollout
kubectl rollout status deployment/devops-eval-app -n devops-eval

# 5. Curl proof
kubectl port-forward svc/devops-eval-svc 8080:80 -n devops-eval &
sleep 2 && curl -s http://localhost:8080/ | tee curl-proof.log

# 6. Destroy
kind delete cluster --name devops-eval
```

## DoD
- dry-run exits 0 (4 resources validated)
- apply exits 0
- 2/2 pods ready
- curl returns HTTP 200 with response body
- REPORT.json written
- PROOF.md contains all log excerpts
