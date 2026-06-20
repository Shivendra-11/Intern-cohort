type BadgeVariant = "success" | "warning" | "danger" | "neutral";

interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
}

function inferVariant(label: string): BadgeVariant {
  const u = label.toUpperCase();
  if (u === "SUCCESS" || u === "COMPLETE") return "success";
  if (u === "FAILED" || u === "MISSING") return "danger";
  if (u === "GENERATED" || u === "WARN") return "warning";
  return "neutral";
}

export function StatusBadge({ label, variant }: StatusBadgeProps) {
  const v = variant ?? inferVariant(label);
  return <span className={`badge badge-${v}`}>{label}</span>;
}
