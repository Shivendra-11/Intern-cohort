import { AgentChartsSection } from "@/components/charts/AgentChartsSection";
import { AgentReportSection } from "@/components/agents/AgentReportSection";
import {
  ArchitectureGraph,
  DataContractsList,
  IntegrationTestsTable,
} from "@/components/agents/A3Sections";
import { SessionAgentPageHeader } from "@/components/agents/SessionAgentPageHeader";
import { getA3Data } from "@/data/agentData";

export function A3Page() {
  const data = getA3Data();

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <SessionAgentPageHeader
        agent="A3"
        fallbackMeta={data.meta}
        title="Polyglot Mini-System"
        subtitle="FastAPI · Node Worker · Rust Engine"
      />

      <AgentReportSection agent="A3" />

      <AgentChartsSection agent="A3" />

      <ArchitectureGraph
        flow={data.architecture.flow}
        components={data.architecture.components}
      />

      <DataContractsList contracts={data.data_contracts} />

      <IntegrationTestsTable tests={data.integration_tests} />
    </div>
  );
}
