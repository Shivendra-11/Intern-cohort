import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DataTable, type Column } from "../components/DataTable";
import { FilterSelect } from "../components/FilterSelect";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { SearchInput } from "../components/SearchInput";
import { StatCard } from "../components/StatCard";
import { TypeDonutChart } from "../components/charts/OverviewCharts";
import type { InventoryItem } from "../types/api";

function flattenInventory(artifacts: Record<string, InventoryItem[]>): InventoryItem[] {
  return Object.values(artifacts).flat();
}

const TYPE_CLASS: Record<string, string> = {
  function:  "badge badge-neutral",
  class:     "badge badge-purple",
  component: "badge badge-cyan",
  route:     "badge badge-success",
  model:     "badge badge-warning",
  variable:  "badge badge-orange",
  interface: "badge badge-purple",
  type:      "badge badge-faint",
};

function typeBadgeClass(type: string): string {
  return TYPE_CLASS[type.toLowerCase()] ?? "badge badge-faint";
}

export function InventoryPage() {
  const { data, error, loading } = useRepoFetch("inventory", () => api.inventory());
  const [search, setSearch] = useState("");
  const [typeFilter, setTypeFilter] = useState("all");

  const items = useMemo(() => {
    if (!data) return [];
    if (data.items?.length) return data.items;
    return flattenInventory(data.artifacts ?? {});
  }, [data]);

  const types = useMemo(() => {
    const set = new Set(items.map((i) => i.type));
    return ["all", ...Array.from(set).sort()];
  }, [items]);

  const typeChartData = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const item of items) {
      counts[item.type] = (counts[item.type] ?? 0) + 1;
    }
    return Object.entries(counts)
      .map(([type, count]) => ({ type, count }))
      .sort((a, b) => b.count - a.count)
      .slice(0, 6);
  }, [items]);

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return items.filter((item) => {
      if (typeFilter !== "all" && item.type !== typeFilter) return false;
      if (!q) return true;
      return (
        item.name.toLowerCase().includes(q) ||
        item.file.toLowerCase().includes(q) ||
        item.type.toLowerCase().includes(q) ||
        (item.signature ?? "").toLowerCase().includes(q)
      );
    });
  }, [items, search, typeFilter]);

  const topFiles = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const item of items) {
      counts[item.file] = (counts[item.file] ?? 0) + 1;
    }
    return Object.entries(counts)
      .sort((a, b) => b[1] - a[1])
      .slice(0, 3);
  }, [items]);

  const columns: Column<InventoryItem>[] = useMemo(
    () => [
      {
        key: "name",
        header: "Name",
        render: (r) => (
          <span style={{ fontWeight: 600, color: "var(--text)" }}>{r.name}</span>
        ),
      },
      {
        key: "type",
        header: "Type",
        render: (r) => (
          <span className={typeBadgeClass(r.type)}>{r.type}</span>
        ),
      },
      {
        key: "kind",
        header: "Kind",
        render: (r) =>
          r.syntactic_kind ? (
            <span className="badge badge-faint">{r.syntactic_kind}</span>
          ) : (
            <span style={{ color: "var(--text-faint)" }}>—</span>
          ),
      },
      {
        key: "signature",
        header: "Signature",
        render: (r) =>
          r.signature ? (
            <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.7rem", color: "var(--text-muted)" }}>
              {r.signature.length > 60 ? r.signature.slice(0, 60) + "…" : r.signature}
            </span>
          ) : (
            <span style={{ color: "var(--text-faint)" }}>—</span>
          ),
      },
      { key: "file", header: "File", render: (r) => r.file, className: "mono" },
      {
        key: "line",
        header: "Line",
        render: (r) => (
          <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem", color: "var(--accent)" }}>
            :{r.line}
          </span>
        ),
      },
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading inventory…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  return (
    <>
      {/* Summary stats */}
      <div className="stat-grid" style={{ gridTemplateColumns: "repeat(auto-fit, minmax(150px, 1fr))" }}>
        <StatCard label="Total artifacts" value={items.length} icon="▣" accent="default" />
        <StatCard label="Unique types" value={types.length - 1} icon="◉" accent="purple" />
        <StatCard label="Files scanned" value={topFiles.length > 0 ? Object.keys(
          items.reduce((acc, i) => { acc[i.file] = true; return acc; }, {} as Record<string,boolean>)
        ).length : "—"} icon="◫" accent="cyan" />
        {topFiles[0] && (
          <StatCard
            label="Densest file"
            value={topFiles[0][1]}
            sub={topFiles[0][0].split("/").pop()}
            icon="✓"
            accent="warning"
          />
        )}
      </div>

      {/* Type distribution chart */}
      {typeChartData.length > 0 && (
        <div className="chart-grid" style={{ marginBottom: "1.5rem" }}>
          <div className="chart-card">
            <div className="chart-card-header">
              <h3>Type distribution</h3>
              <p>Artifact breakdown by syntactic type</p>
            </div>
            <TypeDonutChart data={typeChartData} />
          </div>
          <div className="chart-card">
            <div className="chart-card-header">
              <h3>Type counts</h3>
              <p>All discovered artifact types</p>
            </div>
            <div style={{ display: "flex", flexWrap: "wrap", gap: "0.5rem", paddingTop: "0.5rem" }}>
              {typeChartData.map((t) => (
                <button
                  key={t.type}
                  type="button"
                  onClick={() => setTypeFilter(typeFilter === t.type ? "all" : t.type)}
                  style={{
                    display: "inline-flex",
                    alignItems: "center",
                    gap: "0.4rem",
                    padding: "0.35rem 0.7rem",
                    borderRadius: "var(--radius-md)",
                    border: `1px solid ${typeFilter === t.type ? "var(--accent)" : "var(--border)"}`,
                    background: typeFilter === t.type ? "var(--accent-soft)" : "var(--bg-elevated)",
                    cursor: "pointer",
                    fontSize: "0.8rem",
                    color: typeFilter === t.type ? "var(--accent)" : "var(--text-muted)",
                    fontWeight: 600,
                    transition: "all 0.15s",
                  }}
                >
                  <span className={typeBadgeClass(t.type)} style={{ padding: "0.1rem 0.4rem" }}>{t.type}</span>
                  <span style={{ fontFamily: "var(--font-mono)", fontSize: "0.72rem" }}>{t.count}</span>
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      <PageShell
        title={`Artifacts (${filtered.length}${filtered.length !== items.length ? ` of ${items.length}` : ""})`}
        toolbar={
          <>
            <SearchInput
              value={search}
              onChange={setSearch}
              placeholder="Search name, file, type, signature…"
            />
            <FilterSelect
              label="Type filter"
              value={typeFilter}
              onChange={setTypeFilter}
              options={types.map((t) => ({
                value: t,
                label: t === "all" ? "All types" : t,
              }))}
            />
          </>
        }
      >
        <div className="panel-body flush">
          <DataTable
            columns={columns}
            rows={filtered}
            rowKey={(r) => `${r.file}:${r.line}:${r.name}`}
          />
        </div>
      </PageShell>
    </>
  );
}
