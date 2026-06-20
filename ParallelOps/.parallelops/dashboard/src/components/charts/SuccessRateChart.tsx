import { ChartCard } from "@/components/charts/ChartCard";
import type { SuccessRateData } from "@/types/report";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

interface SuccessRateChartProps {
  title: string;
  description?: string;
  data: SuccessRateData;
  lastUpdated?: string | null;
}

export function SuccessRateChart({
  title,
  description,
  data,
  lastUpdated,
}: SuccessRateChartProps) {
  if (!data || typeof data.current !== "number") {
    return (
      <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No success rate data
        </p>
      </ChartCard>
    );
  }

  const history = data.history ?? [];

  return (
    <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
      <div className="mb-3 flex items-end gap-2">
        <span className="text-3xl font-semibold tracking-tight">{data.current}%</span>
        {data.label && (
          <span className="mb-1 text-xs text-muted-foreground">{data.label}</span>
        )}
      </div>
      {history.length > 0 ? (
        <ResponsiveContainer width="100%" height="75%">
          <LineChart data={history} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
            <CartesianGrid strokeDasharray="3 3" className="stroke-border" vertical={false} />
            <XAxis
              dataKey="label"
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
            />
            <YAxis
              domain={[0, 100]}
              tick={{ fontSize: 10 }}
              tickLine={false}
              axisLine={false}
              unit="%"
            />
            <Tooltip
              contentStyle={{
                background: "hsl(var(--card))",
                border: "1px solid hsl(var(--border))",
                borderRadius: 8,
                fontSize: 12,
              }}
              formatter={(value) => [`${Number(value ?? 0)}%`, "Rate"]}
            />
            <Line
              type="monotone"
              dataKey="rate"
              stroke="hsl(142 71% 45%)"
              strokeWidth={2}
              dot={{ r: 3, fill: "hsl(142 71% 45%)" }}
            />
          </LineChart>
        </ResponsiveContainer>
      ) : (
        <p className="text-xs text-muted-foreground">No history series</p>
      )}
    </ChartCard>
  );
}
