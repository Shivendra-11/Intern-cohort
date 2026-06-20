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

const CHART_COLORS = [
  "var(--chart-1)",
  "var(--chart-2)",
  "var(--chart-3)",
  "var(--chart-4)",
  "var(--chart-5)",
  "var(--chart-6)",
];

const STATUS_COLORS: Record<string, string> = {
  complete: "var(--chart-2)",
  running:  "var(--chart-3)",
  pending:  "var(--chart-4)",
  error:    "var(--chart-5)",
};

const tooltipStyle = {
  contentStyle: {
    background: "var(--bg-elevated)",
    border: "1px solid var(--border)",
    borderRadius: 10,
    color: "var(--text)",
    fontSize: 12,
    boxShadow: "var(--shadow)",
  },
  labelStyle: { color: "var(--text-muted)", fontWeight: 600 },
  itemStyle: { color: "var(--text)" },
};

interface ArtifactBarChartProps {
  data: { name: string; count: number }[];
}

export function ArtifactBarChart({ data }: ArtifactBarChartProps) {
  const filtered = data.filter((d) => d.count > 0);
  if (filtered.length === 0) {
    return <div className="empty-state">No artifact counts</div>;
  }

  return (
    <ResponsiveContainer width="100%" height={220}>
      <BarChart data={filtered} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <defs>
          {CHART_COLORS.map((_, i) => (
            <linearGradient key={i} id={`bar-grad-${i}`} x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor={CHART_COLORS[i]} stopOpacity={0.9} />
              <stop offset="100%" stopColor={CHART_COLORS[i]} stopOpacity={0.5} />
            </linearGradient>
          ))}
        </defs>
        <XAxis
          dataKey="name"
          tick={{ fill: "var(--text-faint)", fontSize: 10, fontWeight: 600 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "var(--text-faint)", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="count" radius={[5, 5, 0, 0]} maxBarSize={48}>
          {filtered.map((_, i) => (
            <Cell key={i} fill={`url(#bar-grad-${i % CHART_COLORS.length})`} />
          ))}
        </Bar>
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

  const completedCount = data.filter((d) => d.status === "complete").length;
  const totalCount = data.length;

  return (
    <div style={{ position: "relative" }}>
      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <defs>
            {active.map((d, i) => (
              <linearGradient key={i} id={`pie-grad-${i}`} x1="0" y1="0" x2="1" y2="1">
                <stop offset="0%" stopColor={STATUS_COLORS[d.status] ?? CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={1} />
                <stop offset="100%" stopColor={STATUS_COLORS[d.status] ?? CHART_COLORS[i % CHART_COLORS.length]} stopOpacity={0.7} />
              </linearGradient>
            ))}
          </defs>
          <Pie
            data={active}
            dataKey="value"
            nameKey="name"
            cx="50%"
            cy="50%"
            innerRadius={56}
            outerRadius={84}
            paddingAngle={3}
            strokeWidth={0}
          >
            {active.map((_d, i) => (
              <Cell key={i} fill={`url(#pie-grad-${i})`} />
            ))}
          </Pie>
          <Tooltip {...tooltipStyle} formatter={(_v, n) => [n, ""]} />
          <Legend
            wrapperStyle={{ fontSize: 11, color: "var(--text-muted)" }}
            iconSize={8}
            iconType="circle"
          />
        </PieChart>
      </ResponsiveContainer>
      {/* Center label */}
      <div style={{
        position: "absolute",
        top: "50%",
        left: "50%",
        transform: "translate(-50%, -62%)",
        textAlign: "center",
        pointerEvents: "none",
      }}>
        <div style={{ fontSize: "1.5rem", fontWeight: 800, letterSpacing: "-0.04em", lineHeight: 1 }}>
          {completedCount}/{totalCount}
        </div>
        <div style={{ fontSize: "0.65rem", color: "var(--text-faint)", fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em", marginTop: 2 }}>
          complete
        </div>
      </div>
    </div>
  );
}

interface MethodBarChartProps {
  data: { method: string; count: number }[];
}

export function MethodBarChart({ data }: MethodBarChartProps) {
  const METHOD_COLOR: Record<string, string> = {
    GET:     "var(--chart-2)",
    POST:    "var(--chart-1)",
    PUT:     "var(--chart-3)",
    PATCH:   "var(--orange)",
    DELETE:  "var(--chart-5)",
    OPTIONS: "var(--chart-4)",
    HEAD:    "var(--cyan)",
  };

  if (data.length === 0) return <div className="empty-state">No route data</div>;

  return (
    <ResponsiveContainer width="100%" height={180}>
      <BarChart data={data} margin={{ top: 4, right: 8, left: -20, bottom: 0 }}>
        <XAxis
          dataKey="method"
          tick={{ fill: "var(--text-faint)", fontSize: 10, fontWeight: 700 }}
          axisLine={false}
          tickLine={false}
        />
        <YAxis
          allowDecimals={false}
          tick={{ fill: "var(--text-faint)", fontSize: 10 }}
          axisLine={false}
          tickLine={false}
        />
        <Tooltip {...tooltipStyle} />
        <Bar dataKey="count" radius={[4, 4, 0, 0]} maxBarSize={40}>
          {data.map((d, i) => (
            <Cell key={i} fill={METHOD_COLOR[d.method] ?? CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Bar>
      </BarChart>
    </ResponsiveContainer>
  );
}

interface TypeDonutChartProps {
  data: { type: string; count: number }[];
}

export function TypeDonutChart({ data }: TypeDonutChartProps) {
  if (data.length === 0) return <div className="empty-state">No type data</div>;

  return (
    <ResponsiveContainer width="100%" height={180}>
      <PieChart>
        <Pie
          data={data}
          dataKey="count"
          nameKey="type"
          cx="50%"
          cy="50%"
          innerRadius={44}
          outerRadius={68}
          paddingAngle={2}
          strokeWidth={0}
        >
          {data.map((_, i) => (
            <Cell key={i} fill={CHART_COLORS[i % CHART_COLORS.length]} />
          ))}
        </Pie>
        <Tooltip {...tooltipStyle} />
        <Legend wrapperStyle={{ fontSize: 10, color: "var(--text-muted)" }} iconSize={7} iconType="circle" />
      </PieChart>
    </ResponsiveContainer>
  );
}
