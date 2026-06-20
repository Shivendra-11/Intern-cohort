import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DataTable, type Column } from "../components/DataTable";
import { FilterSelect } from "../components/FilterSelect";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { SearchInput } from "../components/SearchInput";
import { StatCard } from "../components/StatCard";
import { MethodBarChart } from "../components/charts/OverviewCharts";
import type { RouteRecord } from "../types/api";

const METHOD_CLASS: Record<string, string> = {
  GET:     "badge method-get",
  POST:    "badge method-post",
  PUT:     "badge method-put",
  PATCH:   "badge method-patch",
  DELETE:  "badge method-delete",
  OPTIONS: "badge method-options",
  HEAD:    "badge method-head",
};

function methodBadgeClass(method: string): string {
  return METHOD_CLASS[method.toUpperCase()] ?? "badge badge-faint";
}

const SURFACE_ICONS: Record<string, string> = {
  backend:  "⚙",
  frontend: "⬡",
};

export function RoutesPage() {
  const { data, error, loading } = useRepoFetch("routes", () => api.routes());
  const [search, setSearch] = useState("");
  const [methodFilter, setMethodFilter] = useState("all");
  const [surfaceFilter, setSurfaceFilter] = useState("all");

  const routes = data?.routes ?? [];

  const methods = useMemo(() => {
    const set = new Set(routes.map((r) => r.method));
    return ["all", ...Array.from(set).sort()];
  }, [routes]);

  const methodChartData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of routes) {
      counts[r.method] = (counts[r.method] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([method, count]) => ({ method, count }))
      .sort((a, b) => b.count - a.count);
  }, [routes]);

  const frameworkCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of routes) {
      counts[r.framework] = (counts[r.framework] ?? 0) + 1;
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [routes]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return routes.filter((r) => {
      if (methodFilter !== "all" && r.method !== methodFilter) return false;
      if (surfaceFilter !== "all" && r.surface !== surfaceFilter) return false;
      if (!q) return true;
      return (
        r.path.toLowerCase().includes(q) ||
        r.file.toLowerCase().includes(q) ||
        (r.handler ?? "").toLowerCase().includes(q) ||
        r.framework.toLowerCase().includes(q)
      );
    });
  }, [routes, search, methodFilter, surfaceFilter]);

  const columns: Column<RouteRecord>[] = useMemo(
    () => [
      {
        key: "method",
        header: "Method",
        render: (r) => (
          <span className={methodBadgeClass(r.method)}>{r.method}</span>
        ),
      },
      {
        key: "path",
        header: "Path",
        render: (r) => (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.8rem", fontWeight: 600, color: "var(--text)" }}>
            {r.path}
          </span>
        ),
      },
      {
        key: "framework",
        header: "Framework",
        render: (r) => (
          <span className="badge badge-faint">{r.framework}</span>
        ),
      },
      {
        key: "surface",
        header: "Surface",
        render: (r) => (
          <span style={{ fontSize: "0.8rem", color: "var(--text-muted)" }}>
            <span aria-hidden style={{ marginRight: "0.3em" }}>{SURFACE_ICONS[r.surface] ?? "◉"}</span>
            {r.surface}
          </span>
        ),
      },
      {
        key: "handler",
        header: "Handler",
        render: (r) =>
          r.handler ? (
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--text-muted)" }}>
              {r.handler}
            </span>
          ) : (
            <span style={{ color: "var(--text-faint)" }}>—</span>
          ),
      },
      {
        key: "file",
        header: "File : Line",
        render: (r) => (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)" }}>
            {r.file}
            <span style={{ color: "var(--accent)" }}>:{r.line}</span>
          </span>
        ),
      },
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading routes…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  const backendCount = data.counts.backend ?? routes.filter((r) => r.surface === "backend").length;
  const frontendCount = data.counts.frontend ?? routes.filter((r) => r.surface === "frontend").length;

  return (
    <>
      {/* Stats */}
      <div className="stat-grid">
        <StatCard label="Total routes" value={data.counts.total ?? routes.length} icon="⇄" accent="default" />
        <StatCard label="Backend" value={backendCount} sub="server endpoints" icon="⚙" accent="cyan" />
        <StatCard label="Frontend" value={frontendCount} sub="client pages/views" icon="⬡" accent="purple" />
        <StatCard
          label="Frameworks"
          value={frameworkCounts.length}
          sub={frameworkCounts[0] ? `${frameworkCounts[0][0]} (${frameworkCounts[0][1]})` : undefined}
          icon="◎"
          accent="warning"
        />
        <StatCard
          label="HTTP methods"
          value={methodChartData.length}
          sub={methodChartData[0] ? `Most: ${methodChartData[0].method}` : undefined}
          icon="◉"
          accent="success"
        />
      </div>

      {/* Method chart + frameworks */}
      <div className="chart-grid" style={{ marginBottom: "1.5rem" }}>
        <div className="chart-card">
          <div className="chart-card-header">
            <h3>Routes by HTTP method</h3>
            <p>Distribution of HTTP verb usage</p>
          </div>
          <MethodBarChart data={methodChartData} />
        </div>
        <div className="chart-card">
          <div className="chart-card-header">
            <h3>Frameworks detected</h3>
            <p>Routing frameworks across all surfaces</p>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: "0.5rem", paddingTop: "0.5rem" }}>
            {frameworkCounts.map(([fw, count]) => {
              const max = frameworkCounts[0][1];
              const pct = Math.round((count / max) * 100);
              return (
                <div key={fw}>
                  <div style={{ display: "flex", justifyContent: "space-between", marginBottom: "0.25rem" }}>
                    <span style={{ fontSize: "0.8rem", fontWeight: 600, color: "var(--text-muted)" }}>{fw}</span>
                    <span style={{ fontSize: "0.75rem", fontFamily: "var(--font-mono)", color: "var(--accent)" }}>{count}</span>
                  </div>
                  <div className="progress-bar-wrap">
                    <div
                      className="progress-bar-fill progress-bar-fill-success"
                      style={{ width: `${pct}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      </div>

      <PageShell
        title={`Routes (${filtered.length}${filtered.length !== routes.length ? ` of ${routes.length}` : ""})`}
        toolbar={
          <>
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search path, handler, framework…"
            />
            <FilterSelect
              label="Method"
              value={methodFilter}
              onChange={setMethodFilter}
              options={methods.map((m) => ({
                value: m,
                label: m === "all" ? "All methods" : m,
              }))}
            />
            <FilterSelect
              label="Surface"
              value={surfaceFilter}
              onChange={setSurfaceFilter}
              options={[
                { value: "all", label: "All surfaces" },
                { value: "backend", label: "Backend" },
                { value: "frontend", label: "Frontend" },
              ]}
            />
          </>
        }
      >
        <div className="panel-body flush">
          <DataTable
            columns={columns}
            rows={filtered}
            rowKey={(r) => `${r.method}:${r.path}:${r.file}:${r.line}`}
          />
        </div>
      </PageShell>
    </>
  );
}
