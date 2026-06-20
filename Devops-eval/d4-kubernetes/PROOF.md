# D4 — Kubernetes — Proof

## kubeconform + kubectl dry-run

```
Summary: 5 resources found in 5 files - Valid: 5, Invalid: 0, Errors: 0, Skipped: 0
configmap/app-config created (dry run)
deployment.apps/devops-eval-app created (dry run)
...
```

See `dry-run.log`.

## kind cluster apply

```
deployment "devops-eval-app" successfully rolled out
```

See `apply.log`.

## curl proof

```bash
kubectl port-forward svc/devops-eval-svc 18080:80 -n devops-eval
curl http://127.0.0.1:18080/
```

Returns nginx welcome page — see `curl-proof.log`.

## Verify

```bash
./scripts/verify.sh
kind delete cluster --name devops-eval
```
