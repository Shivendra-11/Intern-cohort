import { ChartCard } from "@/components/charts/ChartCard";
import type { GraphData } from "@/types/report";
import {
  ResponsiveContainer,
  Sankey,
  Tooltip,
} from "recharts";

interface RelationGraphChartProps {
  title: string;
  description?: string;
  data: GraphData;
  lastUpdated?: string | null;
}

export function BranchGraphChart(props: RelationGraphChartProps) {
  return <RelationGraphChart {...props} />;
}

export function WorktreeGraphChart(props: RelationGraphChartProps) {
  return <RelationGraphChart {...props} />;
}

function hasCycle(links: { source: number; target: number }[], nodeCount: number): boolean {
  const adj: number[][] = Array.from({ length: nodeCount }, () => []);
  for (const l of links) {
    if (l.source >= 0 && l.source < nodeCount && l.target >= 0 && l.target < nodeCount) {
      adj[l.source].push(l.target);
    }
  }
  const visited = new Uint8Array(nodeCount);
  const stack = new Uint8Array(nodeCount);
  function dfs(n: number): boolean {
    visited[n] = 1; stack[n] = 1;
    for (const nb of adj[n]) {
      if (!visited[nb] && dfs(nb)) return true;
      if (stack[nb]) return true;
    }
    stack[n] = 0;
    return false;
  }
  for (let i = 0; i < nodeCount; i++) if (!visited[i] && dfs(i)) return true;
  return false;
}

function RelationGraphChart({
  title,
  description,
  data,
  lastUpdated,
}: RelationGraphChartProps) {
  if (
    !data?.nodes?.length ||
    !data?.links?.length
  ) {
    return (
      <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No graph data
        </p>
      </ChartCard>
    );
  }

  if (hasCycle(data.links, data.nodes.length)) {
    return (
      <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          Cyclic graph — Sankey requires a DAG
        </p>
      </ChartCard>
    );
  }

  const sankeyData = {
    nodes: data.nodes.map((n) => ({ name: n.name })),
    links: data.links.map((l) => ({
      source: l.source,
      target: l.target,
      value: l.value ?? 1,
    })),
  };

  return (
    <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
      <ResponsiveContainer width="100%" height="100%">
        <Sankey
          data={sankeyData}
          node={{ stroke: "hsl(var(--border))", strokeWidth: 1 }}
          link={{ stroke: "hsl(221 83% 53%)", strokeOpacity: 0.35 }}
          nodePadding={24}
          margin={{ top: 8, right: 24, left: 24, bottom: 8 }}
        >
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
        </Sankey>
      </ResponsiveContainer>
    </ChartCard>
  );
}
