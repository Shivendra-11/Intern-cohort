import { useMemo, useState } from "react";
import { api } from "../api/client";
import { PageShell } from "../components/Layout";
import { useRepoFetch } from "../context/RepoContext";
import { RepoGraphCanvas } from "../components/graph/RepoGraphCanvas";
import { StatCard } from "../components/StatCard";
import {
  GRAPH_TABS,
  type GraphTabKey,
  type RawGraph,
} from "../utils/graphAdapter";

export function GraphsPage() {
  const { data, error, loading } = useRepoFetch("graphs-viz", () => api.graphs());
  const [active, setActive] = useState<GraphTabKey>("import");

  const current = useMemo((): RawGraph | null => {
    if (!data?.graphs) return null;
    const g = data.graphs[active];
    if (!g?.nodes) return null;
    return g as RawGraph;
  }, [data, active]);

  const tabMeta = useMemo(() => {
    if (!data?.graphs) return null;
    return GRAPH_TABS.find((t) => t.key === active);
  }, [data, active]);

  if (loading) return <div className="loading-state">Loading graphs…</div>;
  if (error || !data) return <div className="error-state">{error ?? "No graph data"}</div>;

  const meta = data.metadata;

  return (
    <>
      <div className="stat-grid">
        <StatCard label="Engine" value={data.engine} />
        <StatCard label="Active graph" value={tabMeta?.label ?? active} />
        <StatCard label="Nodes" value={current?.metadata?.node_count ?? current?.nodes.length ?? 0} />
        <StatCard label="Edges" value={current?.metadata?.edge_count ?? current?.edges.length ?? 0} />
      </div>

      <div className="graph-tabs">
        {GRAPH_TABS.map((tab) => {
          const g = data.graphs[tab.key];
          const count = g?.metadata?.node_count ?? g?.nodes?.length ?? 0;
          return (
            <button
              key={tab.key}
              type="button"
              className={`graph-tab${active === tab.key ? " graph-tab-active" : ""}`}
              onClick={() => setActive(tab.key)}
            >
              {tab.label}
              <span className="graph-tab-count">{count}</span>
            </button>
          );
        })}
      </div>

      {current && current.nodes.length > 0 ? (
        <RepoGraphCanvas
          graph={current}
          title={tabMeta?.label ?? active}
          description={current.metadata?.description}
        />
      ) : (
        <PageShell title={tabMeta?.label ?? "Graph"}>
          <div className="empty-state">No nodes in this graph.</div>
        </PageShell>
      )}

      <div style={{ marginTop: "1rem" }}>
        <PageShell title="All graph types">
          <ul className="graph-type-list">
            {(meta?.graph_types ?? GRAPH_TABS.map((t) => t.key)).map((key) => {
              const g = data.graphs[key];
              return (
                <li key={key}>
                  <strong>{GRAPH_TABS.find((t) => t.key === key)?.label ?? key}</strong>
                  {" — "}
                  {g?.metadata?.node_count ?? 0} nodes, {g?.metadata?.edge_count ?? 0} edges
                  {g?.metadata?.description ? ` · ${g.metadata.description}` : ""}
                </li>
              );
            })}
          </ul>
        </PageShell>
      </div>
    </>
  );
}
