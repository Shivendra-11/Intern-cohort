# D4 — Kubernetes Manifests (kind)

## Prerequisites

- kind, kubectl, Docker, skopeo (for corporate TLS workaround)

## Verify

```bash
./scripts/verify.sh
```

## Manual commands

```bash
# Create cluster
kind create cluster --name devops-eval

# Dry-run validate
kubectl apply -f manifests/ --dry-run=client

# Apply
kubectl apply -f manifests/

# Wait for rollout
kubectl rollout status deployment/devops-eval-app -n devops-eval

# Curl proof
kubectl port-forward svc/devops-eval-svc 8080:80 -n devops-eval &
curl -s http://localhost:8080/

# Destroy
kind delete cluster --name devops-eval
```

## Manifests

- `namespace.yaml` — devops-eval namespace
- `configmap.yaml` — app configuration
- `deployment.yaml` — 2 replicas with resource limits
- `service.yaml` — ClusterIP
- `ingress.yaml` — nginx ingress (optional on kind)
