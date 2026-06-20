import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { statusLabel, statusVariant } from "@/lib/status";
import { formatDateTime, formatDuration } from "@/lib/utils";
import type { SelectedEvaluation } from "@/types/overview";
import { CheckCircle2, Clock, FolderGit2, GitBranch, Loader2 } from "lucide-react";

interface ExecutionStatusHeroProps {
  status: SelectedEvaluation["overall_status"];
  evaluation: SelectedEvaluation;
}

export function ExecutionStatusHero({
  status,
  evaluation,
}: ExecutionStatusHeroProps) {
  const isRunning = status === "running";

  return (
    <Card className="overflow-hidden border-border/80 bg-gradient-to-br from-card via-card to-muted/30">
      <CardContent className="p-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-4">
            <div
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl ${
                isRunning
                  ? "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                  : status === "pass"
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : status === "fail"
                      ? "bg-red-500/10 text-red-600 dark:text-red-400"
                      : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
              }`}
            >
              {isRunning ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : (
                <CheckCircle2 className="h-6 w-6" />
              )}
            </div>
            <div>
              <p className="text-xs font-medium uppercase tracking-wider text-muted-foreground">
                Execution Status
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <h2 className="text-2xl font-semibold tracking-tight">
                  {statusLabel(status)}
                </h2>
                <Badge variant={statusVariant(status)}>{status}</Badge>
              </div>
              <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                {evaluation.task}
              </p>
              {(evaluation.repo_name || evaluation.repo_root) && (
                <p className="mt-1 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                  <FolderGit2 className="h-3.5 w-3.5 shrink-0" />
                  {evaluation.repo_name && (
                    <span className="font-medium text-foreground">{evaluation.repo_name}</span>
                  )}
                  {evaluation.repo_root && (
                    <span className="truncate font-mono" title={evaluation.repo_root}>
                      {evaluation.repo_root}
                    </span>
                  )}
                </p>
              )}
            </div>
          </div>

          <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:gap-6">
            <StatPill
              icon={<Clock className="h-4 w-4" />}
              label="Duration"
              value={
                evaluation.duration_seconds
                  ? formatDuration(evaluation.duration_seconds)
                  : "—"
              }
            />
            <StatPill
              icon={<GitBranch className="h-4 w-4" />}
              label="Branch"
              value={evaluation.base_branch}
            />
            <StatPill
              icon={<Clock className="h-4 w-4" />}
              label="Finished"
              value={
                evaluation.finished_at
                  ? formatDateTime(evaluation.finished_at)
                  : "In progress"
              }
            />
          </div>
        </div>
      </CardContent>
    </Card>
  );
}

function StatPill({
  icon,
  label,
  value,
}: {
  icon: ReactNode;
  label: string;
  value: string;
}) {
  return (
    <div className="rounded-lg border bg-background/60 px-3 py-2">
      <div className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <span className="text-xs">{label}</span>
      </div>
      <p className="mt-1 text-sm font-medium">{value}</p>
    </div>
  );
}

interface SelectedEvaluationCardProps {
  evaluation: SelectedEvaluation;
}

export function SelectedEvaluationCard({ evaluation }: SelectedEvaluationCardProps) {
  return (
    <Card>
      <CardHeader className="pb-3">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          Selected Evaluation
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="font-mono text-xs text-muted-foreground">Session</p>
          <p className="mt-0.5 font-mono text-sm font-medium">
            {evaluation.session_id}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Mode</p>
            <p className="font-medium">{evaluation.mode}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Agents</p>
            <p className="font-medium">{evaluation.agents.length}</p>
          </div>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Repository</p>
          {evaluation.repo_name && (
            <p className="mt-0.5 font-medium">{evaluation.repo_name}</p>
          )}
          <p
            className="mt-0.5 truncate font-mono text-xs text-muted-foreground"
            title={evaluation.repo_root}
          >
            {evaluation.repo_root || "—"}
          </p>
        </div>
        <div className="flex flex-wrap gap-1.5">
          {evaluation.agents.map((agent) => (
            <Badge key={agent} variant="secondary" className="font-mono">
              {agent}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
