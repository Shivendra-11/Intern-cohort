import { AgentChartsSection } from "@/components/charts/AgentChartsSection";
import { AgentReportSection } from "@/components/agents/AgentReportSection";
import {
  ImplementedStepCard,
  PriorityMatrix,
  RepoMetaBar,
  RepositoryFindings,
  RollbackNotes,
} from "@/components/agents/A4Sections";
import { SessionAgentPageHeader } from "@/components/agents/SessionAgentPageHeader";
import { getA4Data } from "@/data/agentData";

export function A4Page() {
  const data = getA4Data();

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <SessionAgentPageHeader
        agent="A4"
        fallbackMeta={data.meta}
        title="Repository Modernization"
        subtitle="Findings analysis and first-step implementation"
      />

      <AgentReportSection agent="A4" />

      <AgentChartsSection agent="A4" />

      <RepoMetaBar
        targetRepo={data.target_repo}
        baselineCommit={data.baseline_commit}
      />

      <RepositoryFindings findings={data.findings} />

      <div className="grid gap-6 xl:grid-cols-2">
        <PriorityMatrix items={data.priority_matrix} findings={data.findings} />
        <ImplementedStepCard step={data.implemented_step} />
      </div>

      <RollbackNotes notes={data.rollback_notes} />
    </div>
  );
}
