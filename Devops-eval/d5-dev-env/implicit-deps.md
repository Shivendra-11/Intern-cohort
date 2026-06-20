# Previously implicit dependencies — now explicit

| Was implicit | Now explicit | Where pinned |
|---|---|---|
| Python 3.12 | Required by devcontainer image | devcontainer.json |
| Node v20 | Required by dashboard | devcontainer.json features + .tool-versions |
| Terraform ≥ 1.6 | Required for d1-terraform | devcontainer.json features |
| POSTGRES_PASSWORD env var | Must be set for d2 tests | .env.example |
| docker daemon | Must be running for d2/d3/d4 | devcontainer docker-in-docker feature |
