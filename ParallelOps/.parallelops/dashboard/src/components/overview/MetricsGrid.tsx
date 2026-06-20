import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { formatDuration } from "@/lib/utils";
import type { OverviewMetrics } from "@/types/overview";
import {
  Activity,
  Archive,
  Clock,
  Percent,
  PlayCircle,
} from "lucide-react";

interface MetricsGridProps {
  metrics: OverviewMetrics;
}

const metricConfig = [
  {
    key: "total_runs" as const,
    label: "Total Runs",
    icon: PlayCircle,
    format: (v: number) => String(v),
  },
  {
    key: "agents_executed" as const,
    label: "Agents Executed",
    icon: Activity,
    format: (v: number) => String(v),
  },
  {
    key: "artifacts_generated" as const,
    label: "Artifacts",
    icon: Archive,
    format: (v: number) => String(v),
  },
  {
    key: "avg_duration_seconds" as const,
    label: "Avg Duration",
    icon: Clock,
    format: (v: number) => formatDuration(v),
  },
];

export function MetricsGrid({ metrics }: MetricsGridProps) {
  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
      {metricConfig.map(({ key, label, icon: Icon, format }) => (
        <Card key={key}>
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <p className="text-sm text-muted-foreground">{label}</p>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </div>
            <p className="mt-2 text-2xl font-semibold tracking-tight">
              {format(metrics[key])}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

interface SuccessRateCardProps {
  successRate: number;
  runningCount: number;
}

export function SuccessRateCard({
  successRate,
  runningCount,
}: SuccessRateCardProps) {
  return (
    <Card>
      <CardHeader className="pb-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Success Rate
          </CardTitle>
          <Percent className="h-4 w-4 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent>
        <div className="flex items-end gap-2">
          <span className="text-3xl font-semibold tracking-tight">
            {successRate.toFixed(1)}%
          </span>
          <span className="mb-1 text-sm text-muted-foreground">last 30 days</span>
        </div>
        <Progress value={successRate} className="mt-4" />
        {runningCount > 0 && (
          <p className="mt-3 text-xs text-blue-600 dark:text-blue-400">
            {runningCount} run{runningCount !== 1 ? "s" : ""} in progress
          </p>
        )}
      </CardContent>
    </Card>
  );
}
