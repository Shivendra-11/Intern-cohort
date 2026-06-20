# D2 — Docker Compose Stack + E2E Tests (90m)

## Stack
- **api**: FastAPI (Python 3.12) on port 8000
  - `POST /jobs`  → creates job record in DB, returns `{job_id, status: "pending"}`
  - `GET /jobs/{id}` → returns job with current status
  - `GET /health`
- **worker**: Python script that polls DB every 2s, picks pending jobs,
  marks them processed, logs "processed job <id>"
- **db**: postgres:16-alpine, port 5432
  - seed.sql creates table `jobs(id serial, payload jsonb, status text, created_at timestamptz)`

## Test plan (tests/e2e_test.sh)
1. `docker-compose up -d --build` && wait for api:8000 (30s timeout)
2. `curl POST /jobs` → capture job_id
3. `sleep 5` (worker picks up)
4. `curl GET /jobs/{job_id}` → assert status == "processed"
5. `docker-compose logs worker | grep "processed job ${job_id}"` → cross-service proof

## Teardown
```bash
docker-compose down -v
```

## DoD
- All 5 test assertions pass
- Cross-service log line captured in logs/cross-service.log
- Teardown is clean (docker-compose down -v exits 0)
- REPORT.json written with correct schema
- PROOF.md contains full terminal output
