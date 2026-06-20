import { ChartCard } from "@/components/charts/ChartCard";
import type { PriorityMatrixPoint } from "@/types/report";
import {
  CartesianGrid,
  ResponsiveContainer,
  Scatter,
  ScatterChart,
  Tooltip,
  XAxis,
  YAxis,
  ZAxis,
} from "recharts";

interface PriorityMatrixChartProps {
  title: string;
  description?: string;
  data: PriorityMatrixPoint[];
  lastUpdated?: string | null;
}

export function PriorityMatrixChart({
  title,
  description,
  data,
  lastUpdated,
}: PriorityMatrixChartProps) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No priority matrix data
        </p>
      </ChartCard>
    );
  }

  const selected = data.filter((d) => d.selected);
  const others = data.filter((d) => !d.selected);

  return (
    <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 8, right: 16, left: -8, bottom: 8 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            type="number"
            dataKey="risk_score"
            name="Risk"
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
            label={{ value: "Risk →", position: "insideBottom", offset: -4, fontSize: 11 }}
          />
          <YAxis
            type="number"
            dataKey="value_score"
            name="Value"
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
            label={{ value: "Value →", angle: -90, position: "insideLeft", fontSize: 11 }}
          />
          <ZAxis type="number" dataKey="score" range={[80, 400]} />
          <Tooltip
            cursor={{ strokeDasharray: "3 3" }}
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(_, __, item) => {
              const p = item.payload as PriorityMatrixPoint;
              return [`score ${p.score}`, p.label];
            }}
          />
          <Scatter name="Findings" data={others} fill="hsl(221 83% 53%)" />
          <Scatter name="Selected" data={selected} fill="hsl(38 92% 50%)" />
        </ScatterChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
