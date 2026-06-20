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
      { name: "B2 Routes", value: p.B2_routes === "complete" ? 1 : 0, status: p.B2_routes },
      { name: "B3 Tests", value: p.B3_tests === "complete" ? 1 : 0, status: p.B3_tests },
      { name: "Graphs", value: p.graphs === "complete" ? 1 : 0, status: p.graphs },
    ];
  }, [data]);

  const sourceColumns: Column<SourceRecord>[] = useMemo(
    () => [
      { key: "key", header: "Source", render: (r) => r.key },
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
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading overview…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  const c = data.summary.counts;

  return (
    <>
      <div className="stat-grid">
        <StatCard label="Repository" value={data.repo_name} sub={data.repo_path} />
        <StatCard label="Artifacts" value={c.artifacts_total ?? "—"} />
        <StatCard label="Routes" value={c.routes_total ?? "—"} sub={`${c.routes_backend ?? 0} backend`} />
        <StatCard label="Tests passed" value={c.tests_passed ?? "—"} sub={c.tests_status ?? undefined} />
        <StatCard label="Sources" value={`${data.summary.sources_loaded}/${data.summary.sources_total}`} />
        <StatCard label="Greenfield" value={c.greenfield_projects ?? 0} />
      </div>

      <div className="chart-grid">
        <div className="chart-card">
          <h3>Artifact breakdown</h3>
          <ArtifactBarChart data={artifactChart} />
        </div>
        <div className="chart-card">
          <h3>Pipeline completion</h3>
          <PipelineDonutChart data={pipelineChart} />
        </div>
      </div>

      <PageShell title="Data sources">
        <DataTable
          columns={sourceColumns}
          rows={data.sources}
          rowKey={(r) => r.key}
        />
      </PageShell>
    </>
  );
}
