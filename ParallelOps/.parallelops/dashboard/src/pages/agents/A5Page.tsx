import { AgentChartsSection } from "@/components/charts/AgentChartsSection";
import { AgentReportSection } from "@/components/agents/AgentReportSection";
import { IssuesTable, SeveritySummaryCards } from "@/components/agents/A5Sections";
import { SessionAgentPageHeader } from "@/components/agents/SessionAgentPageHeader";
import { getA5Data } from "@/data/agentData";

export function A5Page() {
  const data = getA5Data();

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <SessionAgentPageHeader
        agent="A5"
        fallbackMeta={data.meta}
        title="Agent Code Review"
        subtitle="Adversarial review with severity and fix suggestions"
      />

      <AgentReportSection agent="A5" />

      <AgentChartsSection agent="A5" />

      <SeveritySummaryCards summary={data.severity_summary} />

      <IssuesTable issues={data.issues} />
    </div>
  );
}
