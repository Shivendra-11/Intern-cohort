import { CHART_COLORS, ChartCard } from "@/components/charts/ChartCard";
import type { MetricItem } from "@/types/report";
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface ExecutionMetricsChartProps {
  title: string;
  description?: string;
  data: MetricItem[];
  lastUpdated?: string | null;
}

export function ExecutionMetricsChart({
  title,
  description,
  data,
  lastUpdated,
}: ExecutionMetricsChartProps) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No metric data
        </p>
      </ChartCard>
    );
  }

  return (
    <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
          <XAxis
            dataKey="name"
            tick={{ fontSize: 11 }}
            tickLine={false}
            axisLine={false}
            interval={0}
            angle={-20}
            textAnchor="end"
            height={50}
          />
          <YAxis tick={{ fontSize: 11 }} tickLine={false} axisLine={false} allowDecimals={false} />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
            formatter={(value, _name, item) => {
              const num = Number(value ?? 0);
              const unit = (item?.payload as MetricItem | undefined)?.unit;
              return [unit ? `${num} ${unit}` : num, "Value"];
            }}
          />
          <Bar dataKey="value" radius={[4, 4, 0, 0]}>
            {data.map((_, i) => (
              <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
