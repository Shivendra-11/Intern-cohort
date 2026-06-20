import type { AgentStatus, OverallStatus } from "@/types/overview";
import type { badgeVariants } from "@/components/ui/badge";
import type { VariantProps } from "class-variance-authority";

type BadgeVariant = NonNullable<VariantProps<typeof badgeVariants>["variant"]>;

export function statusLabel(status: AgentStatus | OverallStatus | string): string {
  const labels: Record<string, string> = {
    pass: "Passed",
    fail: "Failed",
    partial: "Partial",
    running: "Running",
    pending: "Pending",
    skipped: "Skipped",
    scaffolded: "Scaffolded",
  };
  return labels[status] ?? status;
}

export function statusVariant(status: AgentStatus | OverallStatus | string): BadgeVariant {
  const map: Record<string, BadgeVariant> = {
    pass: "success",
    fail: "destructive",
    partial: "warning",
    running: "running",
    pending: "running",
    skipped: "muted",
    scaffolded: "muted",
  };
  return map[status] ?? "secondary";
}

export function agentColor(agent: string): string {
  const colors: Record<string, string> = {
    A1: "bg-violet-500",
    A2: "bg-blue-500",
    A3: "bg-cyan-500",
    A4: "bg-amber-500",
    A5: "bg-rose-500",
    A6: "bg-emerald-500",
  };
  return colors[agent] ?? "bg-muted-foreground";
}
