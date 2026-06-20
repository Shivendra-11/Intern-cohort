import { ChartEngine } from "@/components/charts/ChartEngine";
import { SectionCard } from "@/components/agents/AgentPageHeader";
import { Button } from "@/components/ui/button";
import { useAgentReportJson } from "@/hooks/useArtifactJson";
import { artifactReportJsonPath, type AgentId } from "@/services/artifactClient";
import { useSession } from "@/stores/sessionStore";
import { AlertCircle, BarChart3, RefreshCw } from "lucide-react";

interface AgentChartsSectionProps {
  agent: AgentId;
}

export function AgentChartsSection({ agent }: AgentChartsSectionProps) {
  const { sessionId } = useSession();
  const { data, loading, error, lastUpdated, reload } = useAgentReportJson(agent);
  const sourcePath = artifactReportJsonPath(sessionId, agent);

  return (
    <SectionCard title="Charts" description={`Live from ${sourcePath} · polls every 3s`}>
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <BarChart3 className="h-3.5 w-3.5" />
          <span className="font-mono">{sourcePath}</span>
          {lastUpdated && (
            <span>· updated {new Date(lastUpdated).toLocaleTimeString()}</span>
          )}
        </div>
        <Button variant="outline" size="sm" onClick={reload} disabled={loading}>
          <RefreshCw className={loading ? "animate-spin" : ""} />
          Reload
        </Button>
      </div>

      {loading && !data && (
        <div className="grid gap-6 md:grid-cols-2">
          {[1, 2].map((i) => (
            <div key={i} className="h-[320px] animate-pulse rounded-xl bg-muted" />
          ))}
        </div>
      )}

      {error && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
          <div>
            <p className="font-medium text-destructive">Could not load report.json</p>
            <p className="mt-1 text-muted-foreground">{error}</p>
          </div>
        </div>
      )}

      {data && <ChartEngine report={data} lastUpdated={lastUpdated} />}
    </SectionCard>
  );
}
