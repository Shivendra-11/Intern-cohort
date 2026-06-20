import {
  Bar,
  BarChart,
  Cell,
  Legend,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
];

interface ArtifactBarChartProps {
  data: { name: string; count: number }[];
}

export function ArtifactBarChart({ data }: ArtifactBarChartProps) {
  const filtered = data.filter((d) => d.count > 0);
  if (filtered.length === 0) {
    return <div className="empty-state">No artifact counts</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <BarChart data={filtered} margin={{ top: 8, right: 8, left: -16, bottom: 0 }}>
        <XAxis
          dataKey="name"
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "var(--text-muted)", fontSize: 11 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip
          contentStyle={{
            background: "var(--bg-elevated)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            color: "var(--text)",
          }}
        />
        <Bar dataKey="count" fill="var(--chart-1)" radius={[4, 4, 0, 0]} />
      </BarChart>
    </ResponsiveContainer>
  );
}

interface PipelineDonutChartProps {
  data: { name: string; value: number; status: string }[];
}

export function PipelineDonutChart({ data }: PipelineDonutChartProps) {
  const active = data.filter((d) => d.value > 0);
  if (active.length === 0) {
    return <div className="empty-state">No pipeline data</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={240}>
      <PieChart>
        <Pie
          data={active}
          dataKey="value"
          nameKey="name"
          cx="50%"
          cy="50%"
          innerRadius={52}
          outerRadius={80}
          paddingAngle={2}
        >
          {active.map((_, i) => (
            <Cell key={i} fill={COLORS[i % COLORS.length]} />
          ))}
        </Pie>
        <Tooltip
          contentStyle={{
            background: "var(--bg-elevated)",
            border: "1px solid var(--border)",
            borderRadius: 8,
            color: "var(--text)",
          }}
        />
        <Legend
          wrapperStyle={{ fontSize: 12, color: "var(--text-muted)" }}
        />
      </PieChart>
    </ResponsiveContainer>
  );
}
