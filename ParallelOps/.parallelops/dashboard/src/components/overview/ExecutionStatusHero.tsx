import type { ReactNode } from "react";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { statusLabel, statusVariant } from "@/lib/status";
import { formatDateTime, formatDuration } from "@/lib/utils";
import type { SelectedEvaluation } from "@/types/overview";
import {
  CheckCircle2,
  Clock,
  FolderGit2,
  GitBranch,
  Loader2,
  Zap,
} from "lucide-react";

interface ExecutionStatusHeroProps {
  status: SelectedEvaluation["overall_status"];
  evaluation: SelectedEvaluation;
}

export function ExecutionStatusHero({
  status,
  evaluation,
}: ExecutionStatusHeroProps) {
  const isRunning = status === "running";
  const isPassed = status === "pass";
  const isFailed = status === "fail";

  const gradientClass = isRunning
    ? "from-blue-500/5 via-card to-card"
    : isPassed
      ? "from-emerald-500/5 via-card to-card"
      : isFailed
        ? "from-red-500/5 via-card to-card"
        : "from-amber-500/5 via-card to-card";

  const accentColor = isRunning
    ? "bg-blue-500"
    : isPassed
      ? "bg-emerald-500"
      : isFailed
        ? "bg-red-500"
        : "bg-amber-500";

  return (
    <Card
      className={`overflow-hidden border-border/80 bg-gradient-to-br ${gradientClass}`}
    >
      <div className={`h-1 w-full ${accentColor}`} />
      <CardContent className="p-6">
        <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">
          <div className="flex items-start gap-4">
            <div
              className={`flex h-12 w-12 shrink-0 items-center justify-center rounded-xl shadow-sm ${
                isRunning
                  ? "bg-blue-500/10 text-blue-600 dark:text-blue-400"
                  : isPassed
                    ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
                    : isFailed
                      ? "bg-red-500/10 text-red-600 dark:text-red-400"
                      : "bg-amber-500/10 text-amber-600 dark:text-amber-400"
              }`}
            >
              {isRunning ? (
                <Loader2 className="h-6 w-6 animate-spin" />
              ) : isPassed ? (
                <CheckCircle2 className="h-6 w-6" />
              ) : (
                <Zap className="h-6 w-6" />
              )}
            </div>
            <div>
              <p className="text-[10px] font-bold uppercase tracking-widest text-muted-foreground">
                Execution Status
              </p>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                <h2 className="text-2xl font-bold tracking-tight">
                  {statusLabel(status)}
                </h2>
                <Badge variant={statusVariant(status)} className="text-xs">
                  {status}
                </Badge>
              </div>
              <p className="mt-2 max-w-2xl text-sm text-muted-foreground">
                {evaluation.task}
              </p>
              {(evaluation.repo_name || evaluation.repo_root) && (
                <p className="mt-1.5 flex flex-wrap items-center gap-1.5 text-xs text-muted-foreground">
                  <FolderGit2 className="h-3.5 w-3.5 shrink-0" />
                  {evaluation.repo_name && (
                    <span className="font-semibold text-foreground">
                      {evaluation.repo_name}
                    </span>
                  )}
                  {evaluation.repo_root && (
                    <span
                      className="truncate font-mono opacity-60"
                      title={evaluation.repo_root}
                    >
                      {evaluation.repo_root}
                    </span>
                  )}
                </p>
              )}
              <div className="mt-3 flex flex-wrap gap-1.5">
                {evaluation.agents.map((a) => (
                  <span
                    key={a}
                    className="rounded-md bg-muted px-2 py-0.5 font-mono text-[10px] font-bold"
                  >
                    {a}
                  </span>
                ))}
              </div>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:gap-4">
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
    <div className="rounded-lg border bg-background/70 px-3 py-2.5 shadow-sm">
      <div className="flex items-center gap-1.5 text-muted-foreground">
        {icon}
        <span className="text-[10px] font-medium uppercase tracking-wider">{label}</span>
      </div>
      <p className="mt-1 text-sm font-semibold">{value}</p>
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
        <CardTitle className="text-sm font-semibold">Session Details</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <p className="font-mono text-xs text-muted-foreground">Session ID</p>
          <p className="mt-0.5 font-mono text-sm font-bold">
            {evaluation.session_id || "—"}
          </p>
        </div>
        <div className="grid grid-cols-2 gap-3 text-sm">
          <div>
            <p className="text-xs text-muted-foreground">Mode</p>
            <p className="mt-0.5 font-semibold">{evaluation.mode}</p>
          </div>
          <div>
            <p className="text-xs text-muted-foreground">Agents Run</p>
            <p className="mt-0.5 font-semibold">{evaluation.agents.length}</p>
          </div>
        </div>
        <div>
          <p className="text-xs text-muted-foreground">Repository</p>
          {evaluation.repo_name && (
            <p className="mt-0.5 font-semibold">{evaluation.repo_name}</p>
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
            <Badge key={agent} variant="secondary" className="font-mono text-[10px]">
              {agent}
            </Badge>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}
