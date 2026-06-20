import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { agentColor, statusLabel, statusVariant } from "@/lib/status";
import { cn, formatDuration } from "@/lib/utils";
import type { AgentCard } from "@/types/overview";
import { ArrowRight, FileStack } from "lucide-react";
import { Link } from "react-router-dom";

interface AgentStatusCardsProps {
  agents: AgentCard[];
}

export function AgentStatusCards({ agents }: AgentStatusCardsProps) {
  return (
    <div>
      <h3 className="mb-3 text-sm font-medium text-muted-foreground">
        Agent Status
      </h3>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-5">
        {agents.map((agent) => (
          <AgentStatusCard key={agent.agent} agent={agent} />
        ))}
      </div>
    </div>
  );
}

function AgentStatusCard({ agent }: { agent: AgentCard }) {
  return (
    <Link to={`/agents/${agent.agent}`} className="group block">
      <Card className="h-full transition-all hover:border-foreground/20 hover:shadow-md">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <span
                className={cn(
                  "flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold text-white",
                  agentColor(agent.agent),
                )}
              >
                {agent.agent}
              </span>
              <Badge variant={statusVariant(agent.status)} className="text-[10px]">
                {statusLabel(agent.status)}
              </Badge>
            </div>
            <ArrowRight className="h-4 w-4 text-muted-foreground opacity-0 transition-opacity group-hover:opacity-100" />
          </div>
          <p className="mt-3 text-sm font-medium leading-snug">{agent.label}</p>
          <p className="mt-1 line-clamp-2 text-xs text-muted-foreground">
            {agent.summary}
          </p>
          <div className="mt-3 flex items-center justify-between border-t pt-3 text-xs text-muted-foreground">
            <span className="flex items-center gap-1">
              <FileStack className="h-3 w-3" />
              {agent.artifact_count} files
            </span>
            <span>
              {agent.duration_seconds
                ? formatDuration(agent.duration_seconds)
                : "—"}
            </span>
          </div>
        </CardContent>
      </Card>
    </Link>
  );
}
