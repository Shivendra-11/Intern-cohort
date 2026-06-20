import { AgentChartsSection } from "@/components/charts/AgentChartsSection";
import { AgentReportSection } from "@/components/agents/AgentReportSection";
import {
  BenchmarkComparisonChart,
  FixCard,
  HotspotTable,
  SpeedupHeroCard,
  TargetFunctionCard,
} from "@/components/agents/A6Sections";
import { SessionAgentPageHeader } from "@/components/agents/SessionAgentPageHeader";
import { getA6Data } from "@/data/agentData";

export function A6Page() {
  const data = getA6Data();

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <SessionAgentPageHeader
        agent="A6"
        fallbackMeta={data.meta}
        title="Performance Profiler"
        subtitle="Baseline measurement · profile · targeted fix · re-measure"
      />

      <AgentReportSection agent="A6" />

      <AgentChartsSection agent="A6" />

      <SpeedupHeroCard data={data} />

      <div className="grid gap-6 lg:grid-cols-2">
        <TargetFunctionCard data={data} />
        <FixCard data={data} />
      </div>

      <HotspotTable hotspots={data.profile_hotspots} />

      <BenchmarkComparisonChart data={data.benchmark_comparison} />
    </div>
  );
}
