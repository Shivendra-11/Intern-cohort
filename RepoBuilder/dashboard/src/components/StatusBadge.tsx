type BadgeVariant = "success" | "warning" | "danger" | "neutral" | "purple" | "cyan";

interface StatusBadgeProps {
  label: string;
  variant?: BadgeVariant;
}

const SUCCESS_LABELS = new Set([
  "success", "complete", "completed", "pass", "passed", "loaded",
  "ok", "done", "active", "healthy", "running",
]);
const DANGER_LABELS = new Set([
  "failed", "fail", "error", "missing", "crash", "crashed",
  "broken", "rejected", "timeout",
]);
const WARNING_LABELS = new Set([
  "warn", "warning", "partial", "degraded", "skipped", "pending",
  "generated", "in_progress",
]);

function inferVariant(label: string): BadgeVariant {
  const l = label.toLowerCase();
  if (SUCCESS_LABELS.has(l)) return "success";
  if (DANGER_LABELS.has(l))  return "danger";
  if (WARNING_LABELS.has(l)) return "warning";
  return "neutral";
}

export function StatusBadge({ label, variant }: StatusBadgeProps) {
  const v = variant ?? inferVariant(label);
  return <span className={`badge badge-${v}`}>{label}</span>;
}
