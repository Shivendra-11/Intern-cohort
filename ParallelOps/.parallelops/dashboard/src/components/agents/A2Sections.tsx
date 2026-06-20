import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { statusLabel, statusVariant } from "@/lib/status";
import { cn, formatDateTime } from "@/lib/utils";
import type {
  A2Data,
  BranchInfo,
  CommitInfo,
  TimelineStep,
} from "@/types/agents";
import {
  AlertTriangle,
  CheckCircle2,
  CloudOff,
  CloudUpload,
  GitCommit,
  Info,
  XCircle,
} from "lucide-react";
import { SectionCard } from "./AgentPageHeader";

const stepIcons = {
  pass: CheckCircle2,
  fail: XCircle,
  running: Info,
  info: Info,
  warning: AlertTriangle,
};

const stepColors = {
  pass: "text-emerald-600 dark:text-emerald-400",
  fail: "text-red-600 dark:text-red-400",
  running: "text-blue-600 dark:text-blue-400",
  info: "text-muted-foreground",
  warning: "text-amber-600 dark:text-amber-400",
};

export function ExecutionTimeline({ steps }: { steps: TimelineStep[] }) {
  return (
    <SectionCard title="Execution Timeline" description="Phase-by-phase run log">
      <ScrollArea className="h-[360px] pr-4">
        <div className="space-y-0">
          {steps.map((step, index) => {
            const Icon = stepIcons[step.status];
            const isLast = index === steps.length - 1;
            return (
              <div key={step.id} className="relative flex gap-4 pb-6">
                {!isLast && (
                  <div className="absolute left-[11px] top-7 h-[calc(100%-12px)] w-px bg-border" />
                )}
                <Icon className={cn("h-6 w-6 shrink-0", stepColors[step.status])} />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="font-mono text-xs font-medium">{step.phase}</span>
                    <Badge variant={statusVariant(step.status === "info" ? "skipped" : step.status === "warning" ? "partial" : step.status)} className="text-[10px]">
                      {step.status}
                    </Badge>
                  </div>
                  <p className="mt-0.5 text-sm">{step.message}</p>
                  <p className="mt-1 text-xs text-muted-foreground">
                    {formatDateTime(step.timestamp)}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </ScrollArea>
    </SectionCard>
  );
}

export function CommitsTable({ commits }: { commits: CommitInfo[] }) {
  return (
    <SectionCard title="Commits" description="Lane and integrator commits">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>SHA</TableHead>
            <TableHead>Message</TableHead>
            <TableHead>Lane</TableHead>
            <TableHead>Branch</TableHead>
            <TableHead>When</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {commits.map((c) => (
            <TableRow key={c.sha}>
              <TableCell>
                <div className="flex items-center gap-2">
                  <GitCommit className="h-4 w-4 text-muted-foreground" />
                  <span className="font-mono text-xs">{c.sha}</span>
                </div>
              </TableCell>
              <TableCell className="max-w-xs text-sm">{c.message}</TableCell>
              <TableCell>
                <Badge variant="outline" className="font-mono text-[10px]">
                  {c.lane_id}
                </Badge>
              </TableCell>
              <TableCell className="font-mono text-xs">{c.branch}</TableCell>
              <TableCell className="text-xs text-muted-foreground">
                {formatDateTime(c.authored_at)}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  );
}

export function PushStatusCard({ push }: { push: A2Data["push_status"] }) {
  return (
    <SectionCard title="Push Status">
      <div className="flex items-start gap-4">
        <div
          className={cn(
            "flex h-10 w-10 items-center justify-center rounded-lg",
            push.pushed
              ? "bg-emerald-500/10 text-emerald-600"
              : "bg-muted text-muted-foreground",
          )}
        >
          {push.pushed ? (
            <CloudUpload className="h-5 w-5" />
          ) : (
            <CloudOff className="h-5 w-5" />
          )}
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium">
            {push.pushed ? "Pushed to remote" : "Not pushed"}
          </p>
          <p className="mt-1 text-sm text-muted-foreground">{push.message}</p>
          <div className="mt-3 space-y-1">
            {push.branches.map((b) => (
              <div
                key={b.name}
                className="flex items-center justify-between rounded border px-3 py-2 text-sm"
              >
                <span className="font-mono text-xs">{b.name}</span>
                <Badge variant={b.pushed ? "success" : "secondary"}>
                  {b.pushed ? "pushed" : "local"}
                </Badge>
              </div>
            ))}
          </div>
        </div>
      </div>
    </SectionCard>
  );
}

export function MergeStatusTable({ merges }: { merges: A2Data["merge_status"] }) {
  return (
    <SectionCard title="Merge Status">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Lane</TableHead>
            <TableHead>Branch</TableHead>
            <TableHead>Status</TableHead>
            <TableHead>Conflict</TableHead>
            <TableHead>Resolution</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {merges.map((m) => (
            <TableRow key={m.lane_id}>
              <TableCell className="font-mono text-xs">{m.lane_id}</TableCell>
              <TableCell className="font-mono text-xs">{m.branch}</TableCell>
              <TableCell>
                <Badge variant={statusVariant(m.status)}>{statusLabel(m.status)}</Badge>
              </TableCell>
              <TableCell>
                {m.conflict ? (
                  <Badge variant="warning">yes</Badge>
                ) : (
                  <Badge variant="secondary">no</Badge>
                )}
              </TableCell>
              <TableCell className="max-w-xs text-sm text-muted-foreground">
                {m.resolution ?? "—"}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  );
}

export function ConflictsPanel({ conflicts }: { conflicts: A2Data["conflicts"] }) {
  if (conflicts.length === 0) {
    return (
      <SectionCard title="Conflicts">
        <p className="text-sm text-muted-foreground">No conflicts recorded.</p>
      </SectionCard>
    );
  }

  return (
    <SectionCard title="Conflicts" description="Merge conflicts and resolutions">
      <div className="space-y-3">
        {conflicts.map((c) => (
          <div
            key={c.id}
            className="rounded-lg border border-amber-500/30 bg-amber-500/5 p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <AlertTriangle className="h-4 w-4 text-amber-600" />
                <span className="font-mono text-sm font-medium">{c.file}</span>
              </div>
              <Badge variant={c.status === "resolved" ? "success" : "destructive"}>
                {c.status}
              </Badge>
            </div>
            <p className="mt-2 text-xs text-muted-foreground">
              Branches: {c.branches.join(" ↔ ")}
            </p>
            {c.resolution && (
              <p className="mt-2 text-sm">{c.resolution}</p>
            )}
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export function A2BranchTable({ branches }: { branches: BranchInfo[] }) {
  return (
    <SectionCard title="Branches">
      <div className="flex flex-wrap gap-2">
        {branches.map((b) => (
          <Badge key={b.name} variant="outline" className="px-3 py-1.5 font-mono">
            {b.name}
            <span className="ml-2 text-muted-foreground">({b.lane_id})</span>
          </Badge>
        ))}
      </div>
    </SectionCard>
  );
}
