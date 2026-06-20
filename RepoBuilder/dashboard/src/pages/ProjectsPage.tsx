import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DataTable, type Column } from "../components/DataTable";
import { FilterSelect } from "../components/FilterSelect";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { SearchInput } from "../components/SearchInput";
import { StatusBadge } from "../components/StatusBadge";
import type { ProjectStatus } from "../types/api";

interface ProjectRow {
  id: string;
  project: ProjectStatus;
}

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
      { key: "id", header: "Stack", render: (r) => r.id },
      { key: "project", header: "Project", render: (r) => r.project.project },
      {
        key: "status",
        header: "Status",
        render: (r) => <StatusBadge label={r.project.status} />,
      },
      {
        key: "tests",
        header: "Tests passed",
        render: (r) => r.project.proof?.passed ?? "—",
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

  return (
    <PageShell
      title={`Greenfield projects (${filtered.length})`}
      toolbar={
        <>
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search stack, path…"
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
  );
}
