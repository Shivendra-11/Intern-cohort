import { SectionCard } from "@/components/agents/AgentPageHeader";
import { MarkdownViewer } from "@/components/markdown/MarkdownViewer";
import { Button } from "@/components/ui/button";
import { useAgentReport } from "@/hooks/useAgentReport";
import { artifactReportPath, type AgentId } from "@/services/artifactClient";
import { useSession } from "@/stores/sessionStore";
import { AlertCircle, FileText, RefreshCw } from "lucide-react";

interface AgentReportSectionProps {
  agent: AgentId;
}

export function AgentReportSection({ agent }: AgentReportSectionProps) {
  const { sessionId } = useSession();
  const { content, loading, error, reload } = useAgentReport(agent);
  const sourcePath = artifactReportPath(sessionId, agent);

  return (
    <SectionCard
      title="Report"
      description={sourcePath}
    >
      <div className="mb-4 flex items-center justify-between gap-2">
        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <FileText className="h-3.5 w-3.5" />
          <span className="font-mono">{sourcePath}</span>
        </div>
        <Button variant="outline" size="sm" onClick={reload} disabled={loading}>
          <RefreshCw className={loading ? "animate-spin" : ""} />
          Reload
        </Button>
      </div>

      {loading && (
        <div className="space-y-3 animate-pulse">
          <div className="h-4 w-1/3 rounded bg-muted" />
          <div className="h-4 w-full rounded bg-muted" />
          <div className="h-4 w-5/6 rounded bg-muted" />
          <div className="h-32 w-full rounded bg-muted" />
        </div>
      )}

      {!loading && error && (
        <div className="flex items-start gap-3 rounded-lg border border-destructive/30 bg-destructive/5 p-4 text-sm">
          <AlertCircle className="mt-0.5 h-4 w-4 shrink-0 text-destructive" />
          <div>
            <p className="font-medium text-destructive">Could not load report</p>
            <p className="mt-1 text-muted-foreground">{error}</p>
          </div>
        </div>
      )}

      {!loading && !error && content && (
        <MarkdownViewer content={content} agent={agent} sessionId={sessionId} />
      )}
    </SectionCard>
  );
}
