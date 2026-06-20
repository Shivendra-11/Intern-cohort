# D2 — Docker Compose Stack — Proof

## docker-compose E2E (verified)

```bash
./tests/e2e_test.sh
# or: ./scripts/verify.sh
```

```
=== ALL 5 ASSERTIONS PASSED ===
```

See `tests/e2e_test.log` for full output.

## Cross-service log proof

```
worker-1  | worker started
worker-1  | processed job 2
```

## Teardown + clean re-up

```bash
docker compose down -v
docker compose down -v && docker compose up -d --build
```

Both commands documented in README; E2E script runs teardown automatically.
