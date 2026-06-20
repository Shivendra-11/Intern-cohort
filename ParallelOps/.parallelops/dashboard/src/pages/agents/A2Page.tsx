import { AgentChartsSection } from "@/components/charts/AgentChartsSection";
import { AgentReportSection } from "@/components/agents/AgentReportSection";
import {
  A2BranchTable,
  CommitsTable,
  ConflictsPanel,
  ExecutionTimeline,
  MergeStatusTable,
  PushStatusCard,
} from "@/components/agents/A2Sections";
import { SessionAgentPageHeader } from "@/components/agents/SessionAgentPageHeader";
import { getA2Data } from "@/data/agentData";

export function A2Page() {
  const data = getA2Data();

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <SessionAgentPageHeader
        agent="A2"
        fallbackMeta={data.meta}
        title="Execute Parallel Worktrees"
        subtitle="Worktree creation, merge, and verification"
      />

      <AgentReportSection agent="A2" />

      <AgentChartsSection agent="A2" />

      <ExecutionTimeline steps={data.timeline} />

      <div className="grid gap-6 lg:grid-cols-3">
        <A2BranchTable branches={data.branches} />
        <PushStatusCard push={data.push_status} />
        <ConflictsPanel conflicts={data.conflicts} />
      </div>

      <CommitsTable commits={data.commits} />

      <MergeStatusTable merges={data.merge_status} />
    </div>
  );
}
