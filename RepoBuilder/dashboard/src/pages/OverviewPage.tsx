import { useMemo } from "react";
import { api } from "../api/client";
import {
  ArtifactBarChart,
  PipelineDonutChart,
} from "../components/charts/OverviewCharts";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import { DataTable, type Column } from "../components/DataTable";
import type { SourceRecord } from "../types/api";

const PIPELINE_STAGES = [
  { key: "B1_inventory", label: "Inventory",    icon: "▣", desc: "Artifact scan" },
  { key: "B2_routes",    label: "Routes",        icon: "⇄", desc: "Route extraction" },
  { key: "B3_tests",     label: "Tests",         icon: "✓", desc: "Test execution" },
  { key: "graphs",       label: "Graphs",        icon: "◎", desc: "Graph generation" },
] as const;

function stageClass(status: string): string {
  if (status === "complete") return "pipeline-stage pipeline-stage-complete";
  if (status === "running" || status === "in_progress") return "pipeline-stage pipeline-stage-running";
  return "pipeline-stage pipeline-stage-pending";
}

function stageIcon(status: string): string {
  if (status === "complete") return "✓";
  if (status === "running" || status === "in_progress") return "⟳";
  return "○";
}

export function OverviewPage() {
  const { data, error, loading } = useRepoFetch("overview", () => api.overview());

  const artifactChart = useMemo(() => {
    const breakdown = data?.summary.counts.artifact_breakdown ?? {};
    return Object.entries(breakdown).map(([name, count]) => ({ name, count }));
  }, [data]);

  const pipelineChart = useMemo(() => {
    const p = data?.summary.pipelines;
    if (!p) return [];
    return [
      { name: "B1 Inventory", value: p.B1_inventory === "complete" ? 1 : 0, status: p.B1_inventory },
      { name: "B2 Routes",    value: p.B2_routes === "complete" ? 1 : 0,    status: p.B2_routes },
      { name: "B3 Tests",     value: p.B3_tests === "complete" ? 1 : 0,     status: p.B3_tests },
      { name: "Graphs",       value: p.graphs === "complete" ? 1 : 0,       status: p.graphs },
    ];
  }, [data]);

  const sourceColumns: Column<SourceRecord>[] = useMemo(
    () => [
      {
        key: "key",
        header: "Source",
        render: (r) => (
          <span style={{ fontWeight: 600, color: "var(--text)" }}>{r.key}</span>
        ),
      },
      {
        key: "path",
        header: "Path",
        render: (r) => r.relative_path,
        className: "mono",
      },
      {
        key: "present",
        header: "Status",
        render: (r) => (
          <StatusBadge
            label={r.present ? "loaded" : "missing"}
            variant={r.present ? "success" : "danger"}
          />
        ),
      },
      {
        key: "error",
        header: "Error",
        render: (r) =>
          r.error ? (
            <span style={{ color: "var(--danger)", fontSize: "0.72rem", fontFamily: "var(--font-mono)" }}>
              {r.error}
            </span>
          ) : (
            <span style={{ color: "var(--text-faint)" }}>—</span>
          ),
      },
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading overview…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  const c = data.summary.counts;
  const p = data.summary.pipelines;
  const completedPipelines = [p.B1_inventory, p.B2_routes, p.B3_tests, p.graphs].filter(
    (s) => s === "complete",
  ).length;

  const testPassRate =
    c.tests_passed != null && (c.tests_passed + (c.tests_failed ?? 0)) > 0
      ? Math.round((c.tests_passed / (c.tests_passed + (c.tests_failed ?? 0))) * 100)
      : null;

  return (
    <>
      {/* Key metrics */}
      <div className="stat-grid">
        <StatCard
          label="Repository"
          value={data.repo_name}
          sub={data.repo_path}
          icon="◫"
          accent="default"
        />
        <StatCard
          label="Artifacts"
          value={c.artifacts_total ?? "—"}
          sub={`${Object.keys(data.summary.counts.artifact_breakdown ?? {}).length} types`}
          icon="▣"
          accent="default"
        />
        <StatCard
          label="Routes"
          value={c.routes_total ?? "—"}
          sub={`${c.routes_backend ?? 0} backend · ${c.routes_frontend ?? 0} frontend`}
          icon="⇄"
          accent="cyan"
        />
        <StatCard
          label="Tests passed"
          value={c.tests_passed ?? "—"}
          sub={testPassRate != null ? `${testPassRate}% pass rate` : (c.tests_status ?? undefined)}
          icon="✓"
          accent={c.tests_failed ? "warning" : "success"}
        />
        <StatCard
          label="Data sources"
          value={`${data.summary.sources_loaded}/${data.summary.sources_total}`}
          sub={`${data.summary.sources_total - data.summary.sources_loaded} missing`}
          icon="⬡"
          accent={data.summary.sources_loaded === data.summary.sources_total ? "success" : "warning"}
        />
        <StatCard
          label="Greenfield"
          value={c.greenfield_projects ?? 0}
          sub="generated projects"
          icon="◎"
          accent="purple"
        />
        <StatCard
          label="Pipelines"
          value={`${completedPipelines}/4`}
          sub="stages complete"
          icon="◉"
          accent={completedPipelines === 4 ? "success" : completedPipelines > 0 ? "warning" : "danger"}
        />
      </div>

      {/* Pipeline stages flow */}
      <div className="pipeline-stages">
        {PIPELINE_STAGES.map((stage) => {
          const status = (p as unknown as Record<string, string>)[stage.key] ?? "pending";
          return (
            <div key={stage.key} className={stageClass(status)}>
              <div className="pipeline-stage-icon" aria-hidden>{stage.icon}</div>
              <div className="pipeline-stage-label">{stage.label}</div>
              <div className="pipeline-stage-status">
                {stageIcon(status)} {status}
              </div>
              <div style={{ fontSize: "0.65rem", color: "var(--text-faint)", marginTop: 2 }}>{stage.desc}</div>
            </div>
          );
        })}
      </div>

      {/* Charts */}
      <div className="chart-grid">
        <div className="chart-card">
          <div className="chart-card-header">
            <h3>Artifact breakdown</h3>
            <p>Types discovered across all scanned files</p>
          </div>
          <ArtifactBarChart data={artifactChart} />
        </div>
        <div className="chart-card">
          <div className="chart-card-header">
            <h3>Pipeline completion</h3>
            <p>Status of each analysis pipeline</p>
          </div>
          <PipelineDonutChart data={pipelineChart} />
        </div>
      </div>

      {/* Data sources table */}
      <PageShell title="Data sources" toolbar={
        <span style={{ fontSize: "0.75rem", color: "var(--text-faint)" }}>
          {data.summary.sources_loaded} loaded · {data.summary.sources_total - data.summary.sources_loaded} missing
        </span>
      }>
        <div className="panel-body flush">
          <DataTable
            columns={sourceColumns}
            rows={data.sources}
            rowKey={(r) => r.key}
          />
        </div>
      </PageShell>
    </>
  );
}
