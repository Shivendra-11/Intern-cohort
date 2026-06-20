import { AgentChartsSection } from "@/components/charts/AgentChartsSection";
import { AgentReportSection } from "@/components/agents/AgentReportSection";
import {
  BranchTable,
  DecompositionTable,
  MergeOrderPipeline,
  RiskPlanTable,
  VerificationPlanTable,
  WorktreeList,
} from "@/components/agents/A1Sections";
import { SessionAgentPageHeader } from "@/components/agents/SessionAgentPageHeader";
import { getA1Data } from "@/data/agentData";

export function A1Page() {
  const data = getA1Data();

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <SessionAgentPageHeader
        agent="A1"
        fallbackMeta={data.meta}
        title="Multi-Worktree Parallel Plan"
        subtitle="Task decomposition and merge planning"
      />

      <AgentReportSection agent="A1" />

      <AgentChartsSection agent="A1" />

      <DecompositionTable lanes={data.decomposition} />

      <div className="grid gap-6 lg:grid-cols-2">
        <BranchTable branches={data.branches} />
        <WorktreeList worktrees={data.worktrees} />
      </div>

      <MergeOrderPipeline order={data.merge_order} />

      <div className="grid gap-6 xl:grid-cols-2">
        <RiskPlanTable risks={data.risk_plan} />
        <VerificationPlanTable steps={data.verification_plan} />
      </div>
    </div>
  );
}
