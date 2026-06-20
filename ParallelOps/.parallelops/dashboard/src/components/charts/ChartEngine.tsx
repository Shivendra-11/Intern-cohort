import { BranchGraphChart, WorktreeGraphChart } from "@/components/charts/RelationGraphChart";
import { ExecutionMetricsChart } from "@/components/charts/ExecutionMetricsChart";
import { PriorityMatrixChart } from "@/components/charts/PriorityMatrixChart";
import { SeverityDistributionChart } from "@/components/charts/SeverityDistributionChart";
import { SuccessRateChart } from "@/components/charts/SuccessRateChart";
import { TimelineChart } from "@/components/charts/TimelineChart";
import { resolveBindings } from "@/lib/jsonPointer";
import type {
  ChartPlan,
  GraphData,
  MetricItem,
  PriorityMatrixPoint,
  SeveritySlice,
  SuccessRateData,
  TimelineChartEvent,
} from "@/types/report";

interface ChartEngineProps {
  report: unknown;
  lastUpdated?: string | null;
}

export function ChartEngine({ report, lastUpdated }: ChartEngineProps) {
  const doc = report as Record<string, unknown>;
  const plan = doc.chart_plan as ChartPlan | undefined;
  const sections = plan?.sections ?? [];

  if (sections.length === 0) {
    return (
      <p className="text-sm text-muted-foreground">No charts defined in chart_plan.</p>
    );
  }

  return (
    <div className="grid gap-6 md:grid-cols-2 xl:grid-cols-2">
      {sections.map((section) => {
        const resolved = resolveBindings(report, section.bindings);
        const data = resolved.data;

        switch (section.component) {
          case "execution_metrics":
            return (
              <ExecutionMetricsChart
                key={section.id}
                title={section.title}
                description={section.description}
                data={data as MetricItem[]}
                lastUpdated={lastUpdated}
              />
            );
          case "timeline":
            return (
              <TimelineChart
                key={section.id}
                title={section.title}
                description={section.description}
                data={data as TimelineChartEvent[]}
                lastUpdated={lastUpdated}
              />
            );
          case "severity_distribution":
            return (
              <SeverityDistributionChart
                key={section.id}
                title={section.title}
                description={section.description}
                data={data as SeveritySlice[]}
                lastUpdated={lastUpdated}
              />
            );
          case "branch_graph":
            return (
              <BranchGraphChart
                key={section.id}
                title={section.title}
                description={section.description}
                data={data as GraphData}
                lastUpdated={lastUpdated}
              />
            );
          case "worktree_graph":
            return (
              <WorktreeGraphChart
                key={section.id}
                title={section.title}
                description={section.description}
                data={data as GraphData}
                lastUpdated={lastUpdated}
              />
            );
          case "success_rate":
            return (
              <SuccessRateChart
                key={section.id}
                title={section.title}
                description={section.description}
                data={data as SuccessRateData}
                lastUpdated={lastUpdated}
              />
            );
          case "priority_matrix":
            return (
              <PriorityMatrixChart
                key={section.id}
                title={section.title}
                description={section.description}
                data={data as PriorityMatrixPoint[]}
                lastUpdated={lastUpdated}
              />
            );
          default:
            return (
              <div
                key={section.id}
                className="rounded-lg border border-dashed p-6 text-sm text-muted-foreground"
              >
                Unknown chart: {section.component}
              </div>
            );
        }
      })}
    </div>
  );
}
