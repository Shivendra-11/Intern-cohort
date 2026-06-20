# D2 — Docker Compose Stack (FastAPI + Postgres + Worker)

## Quick start

```bash
docker compose up -d --build
curl http://localhost:8000/health
```

## End-to-end test

```bash
chmod +x tests/e2e_test.sh scripts/verify.sh
./scripts/verify.sh   # preferred — auto-loads images if needed
# or: ./tests/e2e_test.sh
```

## Teardown

```bash
docker compose down -v
```

## Clean re-up

```bash
docker compose down -v && docker compose up -d --build
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| api     | 8000 | FastAPI — POST/GET /jobs |
| db      | 5432 | Postgres 16 with seed.sql |
| worker  | —    | Polls DB, marks jobs processed |
