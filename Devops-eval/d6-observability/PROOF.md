# D6 — Observability — Proof

## Metrics endpoint (after load)

```
http_requests_total{endpoint="/",method="GET",status_code="200"} 1250.0
```

See `metrics-proof.log`.

## Full stack (Prometheus + Grafana)

```bash
./scripts/verify.sh
```

Compose up log: `compose-up.log`  
Load test: `load-run.log` (1250 requests)

## Prometheus query proof

`prometheus-query.json` — live series for `rate(http_requests_total[1m])`.

## Dashboard panels

`dashboard-panels.json` — provisioned Grafana panels (RPS + p95 latency).

## URLs

- Metrics: http://localhost:8000/metrics
- Prometheus: http://localhost:9090
- Grafana: http://localhost:3000 (admin/admin)
