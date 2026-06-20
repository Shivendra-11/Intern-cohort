# D5 — Reproducible Dev Environment

## Single command bootstrap

```bash
make bootstrap
```

## Run tests

```bash
make test
```

## What's included

- `devcontainer.json` — Python 3.12 + Node 20 + Terraform + Docker-in-Docker
- `.tool-versions` — asdf/mise version pins
- `.env.example` — explicit env vars for compose tests
- `implicit-deps.md` — documents previously implicit dependencies
