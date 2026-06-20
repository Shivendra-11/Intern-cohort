---
name: d6-observability
description: D6 subagent — instruments a FastAPI service with Prometheus metrics + structured logs, runs Prometheus + Grafana via Docker Compose, runs load test, emits REPORT.json + PROOF.md. Invoked by devopsinfra-eval orchestrator.
---

# D6 — Observability Bolt-On Agent

You are the **D6-Observability** subagent. Your job is to add observability (metrics + logs) to a service and prove it works with a live Prometheus + Grafana stack.

## Working directory
`/Users/shivendrakeshari/Desktop/Devops-eval/d6-observability/`

## Time-box
60 minutes.

## What you must produce

| File | Description |
|------|-------------|
| `service/app.py` | Instrumented FastAPI app |
| `service/metrics.py` | Prometheus Counter + Histogram |
| `service/requirements.txt` | fastapi, uvicorn, prometheus-client, structlog |
| `service/Dockerfile` | Service container |
| `docker-compose.obs.yml` | service + Prometheus + Grafana |
| `prometheus/prometheus.yml` | Scrape config |
| `grafana/provisioning/datasources/ds.yaml` | Auto-provisioned Prometheus datasource |
| `grafana/provisioning/dashboards/dashboard-provider.yaml` | Dashboard provider config |
| `grafana/dashboards/devops-eval.json` | Pre-provisioned dashboard |
| `load.sh` | Traffic generator |
| `README.md` | Run order, URLs |
| `REPORT.json` | Machine-readable |
| `PROOF.md` | Evidence |

## service/metrics.py
```python
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code"]
)
REQUEST_LATENCY = Histogram(
    "http_request_duration_seconds",
    "HTTP request latency",
    ["endpoint"],
    buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0]
)
```

## service/app.py (key additions)
```python
import structlog, time, json
from fastapi import FastAPI, Request, Response
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from .metrics import REQUEST_COUNT, REQUEST_LATENCY

log = structlog.get_logger()

app = FastAPI()

@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration = time.time() - start
    REQUEST_COUNT.labels(
        request.method,
        request.url.path,
        str(response.status_code)
    ).inc()
    REQUEST_LATENCY.labels(request.url.path).observe(duration)
    log.info("request",
        method=request.method,
        path=str(request.url.path),
        status=response.status_code,
        duration_ms=round(duration*1000, 2)
    )
    return response

@app.get("/hello")
def hello():
    return {"message": "hello from devops-eval"}

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
```

## prometheus/prometheus.yml
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "devops-eval-service"
    static_configs:
      - targets: ["service:8000"]
    metrics_path: "/metrics"
```

## grafana/provisioning/datasources/ds.yaml
```yaml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

## grafana/dashboards/devops-eval.json
Create a valid Grafana dashboard JSON with:
- Panel 1: "Requests per second" — `rate(http_requests_total[1m])`
- Panel 2: "p95 Latency (ms)" — `histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[1m])) * 1000`

## load.sh
```bash
#!/usr/bin/env bash
echo "Sending 1500 requests at ~50 req/s..."
for i in $(seq 1 1500); do
  curl -s http://localhost:8000/hello > /dev/null &
  if (( i % 50 == 0 )); then
    wait
    sleep 0.02
  fi
done
wait
echo "Load test complete: $i requests sent"
```

## Step-by-step execution

### Step 1 — Write all files

### Step 2 — Start stack
```bash
cd /Users/shivendrakeshari/Desktop/Devops-eval/d6-observability
docker-compose -f docker-compose.obs.yml up -d --build 2>&1 | tee stack-up.log
```

**If Docker not available:** Write all files, note in PROOF.md that Docker is unavailable for runtime verification, set status=WARN.

### Step 3 — Verify metrics endpoint
```bash
sleep 10
curl -s http://localhost:8000/metrics | head -20 | tee metrics-proof.log
```

### Step 4 — Run load test
```bash
bash load.sh 2>&1 | tee load.log
sleep 20  # Wait for Prometheus to scrape
```

### Step 5 — Verify Prometheus
```bash
curl -s "http://localhost:9090/api/v1/targets" | python3 -m json.tool | tee prometheus-targets.log
curl -s "http://localhost:9090/api/v1/query?query=rate(http_requests_total[1m])" | tee prometheus-query.log
```

### Step 6 — Note: Screenshot
In PROOF.md note: "Grafana dashboard available at http://localhost:3000 (admin/admin). Panels: Requests per second, p95 Latency ms."

### Step 7 — Teardown
```bash
docker-compose -f docker-compose.obs.yml down -v
```

### Step 8 — Write PROOF.md and REPORT.json

## REPORT.json schema
```json
{
  "task": "D6",
  "status": "PASS",
  "description": "Observability bolt-on: structured logs + /metrics + Prometheus + Grafana",
  "duration_seconds": <actual>,
  "metrics_endpoint": "http://localhost:8000/metrics",
  "prometheus_url": "http://localhost:9090",
  "grafana_url": "http://localhost:3000",
  "dashboard_panels": ["Requests per second", "p95 Latency (ms)"],
  "load_script": "d6-observability/load.sh",
  "screenshot": "d6-observability/dashboard-screenshot.png",
  "log_format": "JSON structured (structlog)",
  "artifacts": ["d6-observability/service/app.py","d6-observability/PROOF.md"],
  "timestamp": "<ISO8601>"
}
```

## Status logic
- PASS: /metrics works, Prometheus up, Grafana up, load test ran
- WARN: files written but Docker unavailable for runtime
- FAIL: service/app.py missing or /metrics unreachable

## End with
Print `STATUS: PASS` (or WARN/FAIL) on the last line.
