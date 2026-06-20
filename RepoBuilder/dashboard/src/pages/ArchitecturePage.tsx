import { Link } from "react-router-dom";
import { useMemo } from "react";
import { api } from "../api/client";
import { DataTable, type Column } from "../components/DataTable";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { StatCard } from "../components/StatCard";

interface GraphRow {
  type: string;
  nodes: number;
  edges: number;
  description: string;
}

export function ArchitecturePage() {
  const overview = useRepoFetch("arch-overview", () => api.overview());
  const graphs = useRepoFetch("arch-graphs", () => api.graphs());

  const loading = overview.loading || graphs.loading;
  const error = overview.error ?? graphs.error;

  const graphRows: GraphRow[] = useMemo(() => {
    if (!graphs.data) return [];
    return Object.entries(graphs.data.graphs).map(([type, g]) => ({
      type,
      nodes: g.metadata?.node_count ?? 0,
      edges: g.metadata?.edge_count ?? 0,
      description: g.metadata?.description ?? "—",
    }));
  }, [graphs.data]);

  const columns: Column<GraphRow>[] = useMemo(
    () => [
      { key: "type", header: "Graph type", render: (r) => r.type },
      { key: "nodes", header: "Nodes", render: (r) => r.nodes },
      { key: "edges", header: "Edges", render: (r) => r.edges },
      { key: "desc", header: "Description", render: (r) => r.description },
    ],
    [],
  );

  if (loading) return <div className="loading-state">Loading architecture…</div>;
  if (error) return <div className="error-state">{error}</div>;

  const meta = graphs.data?.metadata;

  return (
    <>
      <div className="stat-grid">
        <StatCard label="Engine" value={graphs.data?.engine ?? "—"} />
        <StatCard label="Graph types" value={meta?.graph_types?.length ?? 0} />
        <StatCard label="Total nodes" value={meta?.total_nodes ?? "—"} />
        <StatCard label="Total edges" value={meta?.total_edges ?? "—"} />
      </div>

      <PageShell title="Data pipeline">
        <div className="arch-flow">
          <span className="arch-node">Repository</span>
          <span className="arch-arrow">→</span>
          <span className="arch-node">B1 Inventory</span>
          <span className="arch-arrow">→</span>
          <span className="arch-node">B2 Routes</span>
          <span className="arch-arrow">→</span>
          <span className="arch-node">B3 Tests</span>
          <span className="arch-arrow">→</span>
          <span className="arch-node">Graph Engine</span>
          <span className="arch-arrow">→</span>
          <span className="arch-node">dashboard_data.json</span>
          <span className="arch-arrow">→</span>
          <span className="arch-node">API :8000</span>
          <span className="arch-arrow">→</span>
          <span className="arch-node">React UI</span>
        </div>
        <p style={{ marginTop: "1rem", fontSize: "0.875rem", color: "var(--text-muted)" }}>
          Interactive graph visualizations (zoom, pan, search, highlight) are on the{" "}
          <Link to="/graphs" style={{ color: "var(--accent)" }}>Graphs</Link> page.
          Data is loaded from <code>graph_data.json</code> via the API.
        </p>
      </PageShell>

      <div style={{ marginTop: "1rem" }}>
        <PageShell title="Graph models (metadata only)">
          <div className="panel-body flush">
            <DataTable
              columns={columns}
              rows={graphRows}
              rowKey={(r) => r.type}
              emptyMessage="No graph metadata available."
            />
          </div>
        </PageShell>
      </div>

      {overview.data ? (
        <div style={{ marginTop: "1rem" }}>
          <PageShell title="Workspace">
            <dl style={{ margin: 0, fontSize: "0.875rem", display: "grid", gap: "0.5rem" }}>
              <div>
                <dt style={{ color: "var(--text-muted)", display: "inline" }}>Repo: </dt>
                <dd style={{ display: "inline", fontFamily: "var(--font-mono)", fontSize: "0.8125rem" }}>
                  {overview.data.repo_path}
                </dd>
              </div>
              <div>
                <dt style={{ color: "var(--text-muted)", display: "inline" }}>Workspace: </dt>
                <dd style={{ display: "inline", fontFamily: "var(--font-mono)", fontSize: "0.8125rem" }}>
                  {overview.data.workspace_dir}
                </dd>
              </div>
            </dl>
          </PageShell>
        </div>
      ) : null}
    </>
  );
}
