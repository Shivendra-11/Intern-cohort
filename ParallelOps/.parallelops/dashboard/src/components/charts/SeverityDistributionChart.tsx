import { CHART_COLORS, ChartCard } from "@/components/charts/ChartCard";
import type { SeveritySlice } from "@/types/report";
import {
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
} from "recharts";

interface SeverityDistributionChartProps {
  title: string;
  description?: string;
  data: SeveritySlice[];
  lastUpdated?: string | null;
}

export function SeverityDistributionChart({
  title,
  description,
  data,
  lastUpdated,
}: SeverityDistributionChartProps) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No severity data
        </p>
      </ChartCard>
    );
  }

  return (
    <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
      <ResponsiveContainer width="100%" height="100%">
        <PieChart>
          <Pie
            data={data}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            paddingAngle={2}
          >
            {data.map((entry, i) => (
              <Cell
                key={entry.name}
                fill={entry.fill ?? CHART_COLORS[i % CHART_COLORS.length]}
              />
            ))}
          </Pie>
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
          />
          <Legend wrapperStyle={{ fontSize: 12 }} />
        </PieChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
