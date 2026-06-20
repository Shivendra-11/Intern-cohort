# ParallelOps Eval Dashboard

Read-only artifact dashboard for ParallelOps-Eval (A1–A5).

## Stack

- React 19 + Vite 6
- TypeScript
- Tailwind CSS 4
- shadcn/ui-style components (Radix primitives)

## Quick start

```bash
cd .parallelops/dashboard
npm install
npm run dev
```

Open http://localhost:5174 — Overview uses mock data from `src/data/mock/overview.json`.

## Pages

| Route | Status |
|-------|--------|
| `/` | Overview |
| `/agents/A1` | Multi-worktree plan |
| `/agents/A2` | Parallel worktree execution |
| `/agents/A3` | Polyglot system |
| `/agents/A4` | Repository modernization |
| `/agents/A5` | Code review |
| `/logs` | Placeholder |
| `/settings` | Placeholder |

## Mock data

| Agent | Mock file |
|-------|-----------|
| Overview | `src/data/mock/overview.json` |
| A1–A5 | `src/data/mock/a1.json` … `a5.json` |

Loaders in `src/data/overviewData.ts` and `src/data/agentData.ts`.

## Markdown reports

Agent pages fetch and render `.parallelops/artifacts/A{n}/report.md` at runtime via `/api/artifacts/A{n}/report.md` (Vite dev/preview middleware).

Components:

- `src/components/markdown/MarkdownViewer.tsx` — ReactMarkdown + remark-gfm
- `src/components/agents/AgentReportSection.tsx` — loads report by agent id
- `src/services/artifactClient.ts` — fetch helpers

Supported markdown: headings, tables, code blocks, lists, blockquotes, images (relative paths resolved under artifact dir).

## Charts (Recharts)

Charts read **`report.json`** (agents) or **`index.json`** (overview). Layout is driven by `chart_plan.sections` — no hardcoded metrics in UI.

| Component | Chart type | Data binding |
|-----------|------------|--------------|
| `execution_metrics` | Bar | `$.charts.execution_metrics` |
| `timeline` | Line | `$.charts.timeline` |
| `severity_distribution` | Pie | `$.charts.severity_distribution` |
| `branch_graph` | Sankey | `$.charts.branch_graph` |
| `worktree_graph` | Sankey | `$.charts.worktree_graph` |
| `success_rate` | Line + headline | `$.charts.success_rate` |
| `priority_matrix` | Scatter | `$.charts.priority_matrix` |

**Auto-refresh:** polls every 3s (`DEFAULT_POLL_INTERVAL_MS` in `src/stores/pollConfig.ts`). Edit JSON on disk → dashboard updates without reload.

Artifact paths:

- `/api/artifacts/index.json`
- `/api/artifacts/A1/report.json` … `A5/report.json`
