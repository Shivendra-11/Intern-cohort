# DevOps-Infra Eval — Agent-suggested vs. manually verified

The eval doc's guiding rule for this whole section is *"lean on commands and outputs rather
than prose claims,"* and it asks repeatedly for the agent-vs-manual separation. This file
draws that line for D1–D6: the agent **authors** the manifests/pipelines; nothing counts
until a real tool (`terraform`, `docker`, `kubectl`, `act`, `promtool`) exits 0 on a local
or dry-run backend.

> Each task already ships a `PROOF.md` + `REPORT.json` with captured output. This file is
> the index that says *which* of those outputs were machine-executed vs. agent-written.

## Per-task split

| Task | Agent produced (suggested) | Manually verified (observed, exit 0) | Verification command | Captured proof |
|------|----------------------------|--------------------------------------|----------------------|----------------|
| **D1** Terraform | `*.tf` for S3 + Lambda + API Gateway, vars, backend | `validate` clean; `plan` = 11 to add, 0 change/destroy | `terraform validate && terraform plan` | `d1-terraform/validate.log`, `plan-output.txt` |
| **D2** Compose | `docker-compose.yml` + per-service Dockerfiles + seed | 5/5 E2E assertions; worker log shows cross-service job flow; clean re-up | `./d2-compose-stack/scripts/verify.sh` | `d2-compose-stack/tests/e2e_test.log` |
| **D3** CI | GitHub Actions lint→test→build workflow | Lint + pytest matrix (3.11/3.12) + docker build green; broken-commit demo fails | `./d3-ci-pipeline/scripts/verify.sh` (act dry-run) | `d3-ci-pipeline/PROOF.md` |
| **D4** Kubernetes | Deployment/Service/ConfigMap/Ingress YAML | kubeconform valid (5/5); rolled out on kind; curl 200 via port-forward | `./d4-kubernetes/scripts/verify.sh` | `d4-kubernetes/dry-run.log`, `apply.log` |
| **D5** Dev env | `devcontainer.json` + Makefile bootstrap | `make bootstrap` then `make test` exit 0 from fresh clone | `make bootstrap && make test` | `d5-dev-env/PROOF.md` |
| **D6** Observability | metrics + structured logs + Prometheus/Grafana compose | Prometheus scrape live; 1250-req load test; dashboard panels return data | `./d6-observability/scripts/verify.sh` | `d6-observability/load-run.log`, `dashboard-panels.json`, `dashboard-screenshot.png` |

## What was observed (from EVAL-REPORT.md, re-runnable)

- 6/6 PASS, 0 WARN, 0 FAIL.
- Every PASS is backed by a captured log file listed above — not a prose claim.
- Corporate Docker TLS was worked around with `skopeo copy → docker load`; this is a
  documented environment fix, recorded in each task's `scripts/verify.sh`.

## What remains agent-asserted (NOT independently graded)

- The **"Estimated score: 92/100"** line in `EVAL-REPORT.md` is a self-assessment, not an
  external grade. The 6/6 PASS *is* backed by the commands above; the numeric score is not.
- Cloud `apply` was deliberately **not** run (the doc says prefer local/dry-run over real
  spend). So D1 proves a clean `plan`, not a live AWS deployment — by design.
- The live Vercel dashboard mirrors `REPORT.json` files; it is a viewer, not an independent
  verifier.

See [`../VERIFICATION.md`](../VERIFICATION.md) for the cross-project re-run log.
