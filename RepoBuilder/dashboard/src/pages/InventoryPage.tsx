import { useMemo, useState } from "react";
import { api } from "../api/client";
import { DataTable, type Column } from "../components/DataTable";
import { FilterSelect } from "../components/FilterSelect";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { SearchInput } from "../components/SearchInput";
import type { InventoryItem } from "../types/api";

function flattenInventory(artifacts: Record<string, InventoryItem[]>): InventoryItem[] {
  return Object.values(artifacts).flat();
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

  const filtered = useMemo(() => {
    const q = search.toLowerCase();
    return items.filter((item) => {
      if (typeFilter !== "all" && item.type !== typeFilter) return false;
      if (!q) return true;
      return (
        item.name.toLowerCase().includes(q) ||
        item.file.toLowerCase().includes(q) ||
        item.type.toLowerCase().includes(q)
      );
    });
  }, [items, search, typeFilter]);

  const columns: Column<InventoryItem>[] = useMemo(
    () => [
      { key: "name", header: "Name", render: (r) => r.name },
      { key: "type", header: "Type", render: (r) => r.type },
      { key: "file", header: "File", render: (r) => r.file, className: "mono" },
      { key: "line", header: "Line", render: (r) => r.line },
      {
        key: "kind",
        header: "Kind",
        render: (r) => r.syntactic_kind ?? "—",
      },
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading inventory…</div>;
  if (error || !data)
    return <div className="error-state">{error ?? "No data"}</div>;

  return (
    <PageShell
      title={`Artifacts (${filtered.length})`}
      toolbar={
        <>
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search name, file, type…"
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
  );
}
