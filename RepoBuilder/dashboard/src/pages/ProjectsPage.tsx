import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DataTable, type Column } from "../components/DataTable";
import { FilterSelect } from "../components/FilterSelect";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { SearchInput } from "../components/SearchInput";
import { StatCard } from "../components/StatCard";
import { StatusBadge } from "../components/StatusBadge";
import type { ProjectStatus } from "../types/api";

interface ProjectRow {
  id: string;
  project: ProjectStatus;
}

const METHOD_CLASS: Record<string, string> = {
  GET:    "badge method-get",
  POST:   "badge method-post",
  PUT:    "badge method-put",
  PATCH:  "badge method-patch",
  DELETE: "badge method-delete",
};

function methodBadge(method: string) {
  return METHOD_CLASS[method.toUpperCase()] ?? "badge badge-faint";
}

const STACK_ICON: Record<string, string> = {
  node:   "⬡",
  python: "◎",
  rust:   "◉",
  go:     "▣",
  ts:     "⇄",
};

export function ProjectsPage() {
  const { data, error, loading } = useRepoFetch("projects", () => api.projects());
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState("all");

  const rows: ProjectRow[] = useMemo(() => {
    if (!data) return [];
    return Object.entries(data).map(([id, project]) => ({ id, project }));
  }, [data]);

  const statuses = useMemo(() => {
    const set = new Set(rows.map((r) => r.project.status));
    return ["all", ...Array.from(set).sort()];
  }, [rows]);

  const statusCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const r of rows) {
      counts[r.project.status] = (counts[r.project.status] ?? 0) + 1;
    }
    return counts;
  }, [rows]);

  const totalTests = useMemo(
    () => rows.reduce((sum, r) => sum + (r.project.proof?.passed ?? 0), 0),
    [rows],
  );

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return rows.filter(({ id, project }) => {
      if (statusFilter !== "all" && project.status !== statusFilter) return false;
      if (!q) return true;
      return (
        id.toLowerCase().includes(q) ||
        project.project.toLowerCase().includes(q) ||
        project.project_path.toLowerCase().includes(q)
      );
    });
  }, [rows, search, statusFilter]);

  const columns: Column<ProjectRow>[] = useMemo(
    () => [
      {
        key: "id",
        header: "Stack",
        render: (r) => (
          <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
            <span aria-hidden style={{ fontSize: "1rem" }}>{STACK_ICON[r.id.toLowerCase()] ?? "◫"}</span>
            <span className="stack-pill">{r.id}</span>
          </div>
        ),
      },
      {
        key: "project",
        header: "Project",
        render: (r) => (
          <span style={{ fontWeight: 600, color: "var(--text)" }}>{r.project.project}</span>
        ),
      },
      {
        key: "status",
        header: "Status",
        render: (r) => <StatusBadge label={r.project.status} />,
      },
      {
        key: "tests",
        header: "Tests",
        render: (r) => {
          const passed = r.project.proof?.passed;
          const failed = r.project.proof?.failed;
          if (passed == null) return <span style={{ color: "var(--text-faint)" }}>—</span>;
          return (
            <div style={{ display: "flex", alignItems: "center", gap: "0.4rem" }}>
              <span style={{ color: "var(--success)", fontWeight: 700, fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                ✓ {passed}
              </span>
              {failed != null && failed > 0 && (
                <span style={{ color: "var(--danger)", fontWeight: 700, fontFamily: "var(--font-mono)", fontSize: "0.8rem" }}>
                  ✗ {failed}
                </span>
              )}
            </div>
          );
        },
      },
      {
        key: "endpoints",
        header: "Endpoints",
        render: (r) => {
          const eps = r.project.endpoints;
          if (!eps?.length) return <span style={{ color: "var(--text-faint)" }}>—</span>;
          return (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.25rem" }}>
              {eps.slice(0, 3).map((ep, i) => (
                <span key={i} className="endpoint-chip">
                  <span className={`badge ${methodBadge(ep.method)}`} style={{ fontSize: "0.58rem", padding: "0.08rem 0.35rem" }}>
                    {ep.method}
                  </span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.68rem" }}>{ep.path}</span>
                </span>
              ))}
              {eps.length > 3 && (
                <span style={{ fontSize: "0.7rem", color: "var(--text-faint)" }}>+{eps.length - 3} more</span>
              )}
            </div>
          );
        },
      },
      {
        key: "stack",
        header: "Dependencies",
        render: (r) => {
          const stack = r.project.stack;
          if (!stack) return <span style={{ color: "var(--text-faint)" }}>—</span>;
          const entries = Object.entries(stack).slice(0, 3);
          return (
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.2rem" }}>
              {entries.map(([k, v]) => (
                <span key={k} className="stack-pill" title={`${k}: ${v}`}>
                  {k}
                  <span style={{ color: "var(--text-faint)", fontSize: "0.62rem" }}>@{v}</span>
                </span>
              ))}
              {Object.keys(stack).length > 3 && (
                <span className="stack-pill" style={{ color: "var(--text-faint)" }}>
                  +{Object.keys(stack).length - 3}
                </span>
              )}
            </div>
          );
        },
      },
      {
        key: "path",
        header: "Path",
        render: (r) => r.project.project_path,
        className: "mono",
      },
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading projects…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  const successCount = statusCounts["success"] ?? statusCounts["complete"] ?? statusCounts["pass"] ?? 0;
  const errorCount = statusCounts["error"] ?? statusCounts["failed"] ?? statusCounts["fail"] ?? 0;

  return (
    <>
      {/* Stats */}
      <div className="stat-grid">
        <StatCard label="Total projects" value={rows.length} icon="◫" accent="default" />
        <StatCard
          label="Successful"
          value={successCount}
          sub="build + test passing"
          icon="✓"
          accent="success"
        />
        <StatCard
          label="Failed"
          value={errorCount}
          icon="✗"
          accent={errorCount > 0 ? "danger" : "default"}
        />
        <StatCard
          label="Tests total"
          value={totalTests}
          sub="across all projects"
          icon="◎"
          accent="cyan"
        />
        <StatCard
          label="Stacks"
          value={rows.map(r => r.id).filter((v, i, a) => a.indexOf(v) === i).length}
          sub={rows.map(r => r.id).filter((v, i, a) => a.indexOf(v) === i).join(", ")}
          icon="⬡"
          accent="purple"
        />
      </div>

      {/* Status breakdown cards */}
      {Object.keys(statusCounts).length > 1 && (
        <div style={{ display: "flex", gap: "0.625rem", marginBottom: "1.5rem", flexWrap: "wrap" }}>
          {Object.entries(statusCounts).map(([status, count]) => (
            <button
              key={status}
              type="button"
              onClick={() => setStatusFilter(statusFilter === status ? "all" : status)}
              style={{
                display: "flex",
                alignItems: "center",
                gap: "0.5rem",
                padding: "0.5rem 0.875rem",
                borderRadius: "var(--radius-md)",
                border: `1px solid ${statusFilter === status ? "var(--accent)" : "var(--border)"}`,
                background: statusFilter === status ? "var(--accent-soft)" : "var(--bg-surface)",
                cursor: "pointer",
                fontSize: "0.8rem",
                color: statusFilter === status ? "var(--accent)" : "var(--text-muted)",
                fontWeight: 600,
                transition: "all 0.15s",
              }}
            >
              <StatusBadge label={status} />
              <span style={{ fontFamily: "var(--font-mono)", fontWeight: 700 }}>{count}</span>
            </button>
          ))}
        </div>
      )}

      <PageShell
        title={`Greenfield projects (${filtered.length}${filtered.length !== rows.length ? ` of ${rows.length}` : ""})`}
        toolbar={
          <>
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search stack, project, path…"
            />
            <FilterSelect
              label="Status"
              value={statusFilter}
              onChange={setStatusFilter}
              options={statuses.map((s) => ({
                value: s,
                label: s === "all" ? "All statuses" : s,
              }))}
            />
          </>
        }
      >
        <div className="panel-body flush">
          <DataTable
            columns={columns}
            rows={filtered}
            rowKey={(r) => r.id}
          />
        </div>
      </PageShell>
    </>
  );
}
