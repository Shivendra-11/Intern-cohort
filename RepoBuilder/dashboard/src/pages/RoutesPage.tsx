import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DataTable, type Column } from "../components/DataTable";
import { FilterSelect } from "../components/FilterSelect";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { SearchInput } from "../components/SearchInput";
import { StatusBadge } from "../components/StatusBadge";
import type { RouteRecord } from "../types/api";

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
        render: (r) => <StatusBadge label={r.method} variant="neutral" />,
      },
      { key: "path", header: "Path", render: (r) => r.path, className: "mono" },
      { key: "framework", header: "Framework", render: (r) => r.framework },
      { key: "surface", header: "Surface", render: (r) => r.surface },
      { key: "handler", header: "Handler", render: (r) => r.handler ?? "—" },
      { key: "file", header: "File", render: (r) => `${r.file}:${r.line}`, className: "mono" },
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading routes…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  return (
    <PageShell
      title={`Routes (${filtered.length} / ${data.counts.total ?? routes.length})`}
      toolbar={
        <>
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search path, handler, file…"
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
  );
}
