# Repo Intelligence Dashboard

React + Vite + TypeScript UI for the RepoBuilder platform. Reads live data from the FastAPI backend at **http://localhost:8000** (proxied as `/api` in dev/preview).

## Pages

| Route | Purpose |
|-------|---------|
| `/` | Overview — stats, Recharts, source registry |
| `/inventory` | Artifact table with search + type filter |
| `/routes` | API/route table with method + surface filters |
| `/tests` | Test framework, execution output |
| `/projects` | Greenfield project statuses |
| `/graphs` | React Flow — import, class, service, route, test graphs |
| `/architecture` | Pipeline diagram + graph metadata |

## Run

Terminal 1 — API (from repo root):

```bash
pip install -r requirements-api.txt
python3 -m core.api_server --dashboard workspace/py_app/dashboard_data.json
```

Terminal 2 — UI:

```bash
cd dashboard
npm install
npm run dev
```

Open **http://localhost:3000**

## Build & screenshots

```bash
npm run build
npm run preview
npm run screenshots   # requires API running; writes docs/screenshots/*.png
```

## Stack

- React 18 + TypeScript + Vite
- React Router
- Recharts (Overview charts only)
- CSS custom properties (dark/light mode)
