# D6 — Observability Bolt-On (60m)

## Components

### Instrumented service (service/)
- `service/app.py`   — FastAPI app with Prometheus middleware + structured JSON logs
- `service/metrics.py` — Counter + Histogram definitions

### Stack (docker-compose.obs.yml)
- `service` on port 8000 — FastAPI with /metrics endpoint
- `prometheus` on port 9090 — scrapes service:8000/metrics every 15s
- `grafana` on port 3000 — auto-provisioned datasource + dashboard

### Grafana dashboard panels
- **Requests per second**: `rate(http_requests_total[1m])`
- **p95 Latency ms**: `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m]))`

## Run sequence
```bash
docker-compose -f docker-compose.obs.yml up -d --build
# Wait 15s for first scrape
bash load.sh   # 50 req/s for 30s
# Screenshot Grafana dashboard → dashboard-screenshot.png
```

## Load script (load.sh)
```bash
for i in $(seq 1 1500); do
  curl -s http://localhost:8000/hello > /dev/null &
  sleep 0.02
done
wait
```

## DoD
- /metrics endpoint returns prometheus text format
- Prometheus scrapes metrics (curl localhost:9090/api/v1/targets shows "up")
- Grafana dashboard has both panels with live data
- dashboard-screenshot.png captured
- REPORT.json written
- PROOF.md with metrics endpoint output + grafana curl proof
