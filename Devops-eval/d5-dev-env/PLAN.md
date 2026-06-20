# D5 — Reproducible Dev Environment (45m)

## Approach
VS Code Dev Container (`devcontainer.json`) + `Makefile` with `make bootstrap` single command.

## devcontainer.json
- Base image: `mcr.microsoft.com/devcontainers/python:3.12`
- Features: Node v20, Terraform latest, Docker-in-Docker
- `postCreateCommand`: `make bootstrap`
- Forward ports: 8000, 5432, 5173

## .tool-versions (asdf/mise pins)
```
python 3.12.3
nodejs 20.14.0
terraform 1.8.4
```

## Makefile targets
- `make bootstrap` — pip install, npm install, terraform init
- `make test`      — pytest (quick smoke test)

## implicit-deps.md
Document what was previously implicit, now explicit:
| Was implicit | Now explicit | Where pinned |
|---|---|---|
| Python 3.12 | Required by devcontainer image | devcontainer.json |
| Node v20 | Required by dashboard | devcontainer.json + .tool-versions |
| Terraform ≥ 1.6 | Required for d1-terraform | devcontainer.json features |
| POSTGRES_PASSWORD env var | Must be set for d2 tests | .env.example |
| docker daemon | Must be running for d2/d3/d4 | devcontainer docker-in-docker feature |

## DoD
- `make bootstrap` exits 0 (output in bootstrap.log)
- `make test` exits 0 (output in test-run.log)
- implicit-deps.md lists ≥ 5 items
- REPORT.json written
- PROOF.md contains log excerpts
