import { AgentPageHeader } from "@/components/agents/AgentPageHeader";
import { useAgentMetadata } from "@/hooks/useAgentMetadata";
import { useSession } from "@/stores/sessionStore";
import type { AgentMeta } from "@/types/agents";
import type { AgentId } from "@/services/artifactClient";

interface SessionAgentPageHeaderProps {
  agent: AgentId;
  title: string;
  subtitle?: string;
  fallbackMeta?: AgentMeta;
}

export function SessionAgentPageHeader({
  agent,
  title,
  subtitle,
  fallbackMeta,
}: SessionAgentPageHeaderProps) {
  const { sessionId } = useSession();
  const { meta, loading, missing } = useAgentMetadata(agent);

  if (loading && !meta) {
    return (
      <div className="h-28 animate-pulse rounded-xl border bg-muted/40" aria-hidden />
    );
  }

  const resolved: AgentMeta =
    meta ??
    fallbackMeta ?? {
      agent,
      session_id: sessionId ?? "",
      status: missing ? "skipped" : "pass",
      mode: "build+verify",
      summary: missing
        ? `No ${agent} report in this session — run the agent or add report markdown, then eval-finish.`
        : "",
      started_at: "",
      finished_at: null,
      duration_seconds: null,
    };

  return <AgentPageHeader meta={resolved} title={title} subtitle={subtitle} />;
}
