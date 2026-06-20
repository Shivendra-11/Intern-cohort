import { ChartCard } from "@/components/charts/ChartCard";
import type { TimelineChartEvent } from "@/types/report";
import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const STATUS_VALUE: Record<string, number> = {
  pass: 3,
  success: 3,
  warning: 2,
  partial: 2,
  fail: 1,
  error: 1,
  info: 2,
  running: 2,
};

interface TimelineChartProps {
  title: string;
  description?: string;
  data: TimelineChartEvent[];
  lastUpdated?: string | null;
}

export function TimelineChart({
  title,
  description,
  data,
  lastUpdated,
}: TimelineChartProps) {
  if (!Array.isArray(data) || data.length === 0) {
    return (
      <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
        <p className="flex h-full items-center justify-center text-sm text-muted-foreground">
          No timeline data
        </p>
      </ChartCard>
    );
  }

  const chartData = data.map((event, index) => ({
    ...event,
    index: index + 1,
    time: new Date(event.timestamp).toLocaleTimeString([], {
      hour: "2-digit",
      minute: "2-digit",
    }),
    statusValue: STATUS_VALUE[event.status] ?? 2,
  }));

  return (
    <ChartCard title={title} description={description} lastUpdated={lastUpdated}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={chartData} margin={{ top: 8, right: 16, left: -16, bottom: 0 }}>
          <CartesianGrid strokeDasharray="3 3" className="stroke-border" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10 }}
            tickLine={false}
            axisLine={false}
            interval={0}
            angle={-15}
            textAnchor="end"
            height={55}
          />
          <YAxis
            domain={[0, 4]}
            ticks={[1, 2, 3]}
            tickFormatter={(v) => (v === 3 ? "pass" : v === 2 ? "warn" : "fail")}
            tick={{ fontSize: 10 }}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              background: "hsl(var(--card))",
              border: "1px solid hsl(var(--border))",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(_, payload) => {
              const row = payload?.[0]?.payload as TimelineChartEvent & { time: string };
              return row ? `${row.phase} · ${row.time}` : "";
            }}
            formatter={(_, __, item) => {
              const row = item.payload as TimelineChartEvent;
              return [row.status, "Status"];
            }}
          />
          <Line
            type="monotone"
            dataKey="statusValue"
            stroke="hsl(221 83% 53%)"
            strokeWidth={2}
            dot={{ r: 4, fill: "hsl(221 83% 53%)" }}
            activeDot={{ r: 6 }}
          />
        </LineChart>
      </ResponsiveContainer>
    </ChartCard>
  );
}
