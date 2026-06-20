# D6 — Observability Bolt-On

## Run order

```bash
./scripts/verify.sh
```

Or manually:

```bash
docker compose -f docker-compose.obs.yml up -d --build
chmod +x load.sh
./load.sh http://localhost:8000/
```

## URLs

| Service    | URL |
|------------|-----|
| App        | http://localhost:8000 |
| Metrics    | http://localhost:8000/metrics |
| Prometheus | http://localhost:9090 |
| Grafana    | http://localhost:3000 (admin/admin) |

## Dashboard panels

- Requests per second — `rate(http_requests_total[1m])`
- p95 Latency — `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))`

## Teardown

```bash
docker compose -f docker-compose.obs.yml down -v
```
