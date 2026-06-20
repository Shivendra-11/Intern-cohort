import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { agentColor, statusLabel, statusVariant } from "@/lib/status";
import { cn, formatDuration } from "@/lib/utils";
import type { AgentCard } from "@/types/overview";
import { ArrowRight, CheckCircle2, Clock, FileStack, XCircle } from "lucide-react";
import { Link } from "react-router-dom";

interface AgentStatusCardsProps {
  agents: AgentCard[];
}

export function AgentStatusCards({ agents }: AgentStatusCardsProps) {
  const passCount = agents.filter((a) => a.status === "pass").length;

  return (
    <div>
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-foreground">Agent Status</h3>
        <span className="rounded-full bg-emerald-500/10 px-2.5 py-0.5 text-xs font-medium text-emerald-600 dark:text-emerald-400">
          {passCount}/{agents.length} passed
        </span>
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
        {agents.map((agent) => (
          <AgentStatusCard key={agent.agent} agent={agent} />
        ))}
      </div>
    </div>
  );
}

function AgentStatusCard({ agent }: { agent: AgentCard }) {
  const isPassed = agent.status === "pass";
  const isFailed = agent.status === "fail";

  return (
    <Link to={`/agents/${agent.agent}`} className="group block">
      <Card
        className={cn(
          "h-full overflow-hidden transition-all hover:shadow-lg",
          isPassed
            ? "hover:border-emerald-500/30 hover:shadow-emerald-500/10"
            : isFailed
              ? "hover:border-red-500/30 hover:shadow-red-500/10"
              : "hover:border-amber-500/30 hover:shadow-amber-500/10",
        )}
      >
        <div
          className={cn(
            "h-1 w-full",
            isPassed ? "bg-emerald-500" : isFailed ? "bg-red-500" : "bg-amber-500",
          )}
        />
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <span
              className={cn(
                "flex h-8 w-8 items-center justify-center rounded-lg text-xs font-bold text-white shadow-sm",
                agentColor(agent.agent),
              )}
            >
              {agent.agent}
            </span>
            <div className="flex items-center gap-1.5">
              {isPassed ? (
                <CheckCircle2 className="h-4 w-4 text-emerald-500" />
              ) : isFailed ? (
                <XCircle className="h-4 w-4 text-red-500" />
              ) : null}
              <ArrowRight className="h-3.5 w-3.5 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
            </div>
          </div>

          <div className="mt-3">
            <p className="text-sm font-semibold leading-snug">{agent.label}</p>
            <Badge variant={statusVariant(agent.status)} className="mt-1.5 text-[10px]">
              {statusLabel(agent.status)}
            </Badge>
          </div>

          <p className="mt-2 line-clamp-2 text-[11px] leading-relaxed text-muted-foreground">
            {agent.summary}
          </p>

          <div className="mt-3 flex items-center justify-between border-t border-border/50 pt-3 text-[11px] text-muted-foreground">
            <span className="flex items-center gap-1">
              <FileStack className="h-3 w-3" />
              {agent.artifact_count} files
            </span>
            {agent.duration_seconds ? (
              <span className="flex items-center gap-1">
                <Clock className="h-3 w-3" />
                {formatDuration(agent.duration_seconds)}
              </span>
            ) : (
              <span className="text-muted-foreground/50">—</span>
            )}
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
