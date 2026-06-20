import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { agentColor, statusLabel, statusVariant } from "@/lib/status";
import { cn, formatDuration } from "@/lib/utils";
import { useSession } from "@/stores/sessionStore";
import type { AgentMeta } from "@/types/agents";
import { Clock, FolderGit2 } from "lucide-react";

interface AgentPageHeaderProps {
  meta: AgentMeta;
  title: string;
  subtitle?: string;
}

export function AgentPageHeader({ meta, title, subtitle }: AgentPageHeaderProps) {
  const { repoName, repoRoot } = useSession();

  return (
    <Card className="overflow-hidden border-border/80 bg-gradient-to-br from-card via-card to-muted/20">
      <CardContent className="p-6">
        <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">
          <div className="flex items-start gap-4">
            <span
              className={cn(
                "flex h-11 w-11 shrink-0 items-center justify-center rounded-xl text-sm font-bold text-white",
                agentColor(meta.agent),
              )}
            >
              {meta.agent}
            </span>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                {meta.agent} Agent
              </p>
              <h2 className="mt-0.5 text-xl font-semibold tracking-tight">{title}</h2>
              {subtitle && (
                <p className="mt-1 text-sm text-muted-foreground">{subtitle}</p>
              )}
              <p className="mt-2 text-sm">{meta.summary}</p>
            </div>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant={statusVariant(meta.status)}>{statusLabel(meta.status)}</Badge>
            <Badge variant="outline">{meta.mode}</Badge>
            {meta.duration_seconds != null && (
              <Badge variant="secondary" className="gap-1">
                <Clock className="h-3 w-3" />
                {formatDuration(meta.duration_seconds)}
              </Badge>
            )}
            <span className="font-mono text-xs text-muted-foreground">
              {meta.session_id}
            </span>
            {(repoName || repoRoot) && (
              <Badge variant="secondary" className="gap-1 text-[10px]" title={repoRoot}>
                <FolderGit2 className="h-3 w-3" />
                {repoName || repoRoot}
              </Badge>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

interface SectionCardProps {
  title: string;
  description?: string;
  children: ReactNode;
  className?: string;
}

export function SectionCard({
  title,
  description,
  children,
  className,
}: SectionCardProps) {
  return (
    <Card className={className}>
      <CardHeader className="pb-3">
        <CardTitle className="text-base">{title}</CardTitle>
        {description && (
          <p className="text-sm text-muted-foreground">{description}</p>
        )}
      </CardHeader>
      <CardContent>{children}</CardContent>
    </Card>
  );
}
