interface StatCardProps {
  label: string;
  value: string | number;
  sub?: string;
  icon?: string;
  accent?: "default" | "success" | "warning" | "danger" | "purple" | "cyan";
  trend?: { value: string; direction: "up" | "down" | "flat" };
}

export function StatCard({ label, value, sub, icon, accent = "default", trend }: StatCardProps) {
  const accentClass = accent !== "default" ? ` stat-card-accent-${accent}` : "";
  const iconClass = `stat-icon stat-icon-${accent === "default" ? "accent" : accent}`;

  const isLong = String(value).length > 8;

  return (
    <div className={`stat-card${accentClass}`}>
      <div className="stat-card-top">
        <div className="stat-label">{label}</div>
        {icon && <div className={iconClass}>{icon}</div>}
      </div>
      <div className={isLong ? "stat-value-sm" : "stat-value"}>{value}</div>
      {sub && <div className="stat-sub">{sub}</div>}
      {trend && (
        <div className={`stat-trend stat-trend-${trend.direction}`}>
          {trend.direction === "up" ? "↑" : trend.direction === "down" ? "↓" : "→"}{" "}
          {trend.value}
        </div>
      )}
    </div>
  );
}
