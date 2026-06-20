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
