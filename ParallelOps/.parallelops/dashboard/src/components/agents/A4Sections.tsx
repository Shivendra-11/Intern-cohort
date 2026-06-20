import { Badge } from "@/components/ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { statusLabel, statusVariant } from "@/lib/status";
import { cn } from "@/lib/utils";
import type { A4Data, Finding, PriorityItem } from "@/types/agents";
import { CheckCircle2, RotateCcw, Star } from "lucide-react";
import { SectionCard } from "./AgentPageHeader";

const severityVariant = {
  critical: "destructive" as const,
  high: "warning" as const,
  medium: "secondary" as const,
  low: "muted" as const,
};

export function RepositoryFindings({ findings }: { findings: Finding[] }) {
  return (
    <SectionCard
      title="Repository Findings"
      description="Evidence-backed modernization opportunities"
    >
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Finding</TableHead>
            <TableHead>Severity</TableHead>
            <TableHead>Impact</TableHead>
            <TableHead>Action</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {findings.map((f) => (
            <TableRow key={f.id}>
              <TableCell className="font-mono text-xs">{f.id}</TableCell>
              <TableCell>
                <p className="font-medium">{f.title}</p>
                <p className="mt-0.5 font-mono text-xs text-muted-foreground">
                  {f.evidence}
                </p>
              </TableCell>
              <TableCell>
                <Badge variant={severityVariant[f.severity]}>{f.severity}</Badge>
              </TableCell>
              <TableCell className="max-w-[180px] text-sm text-muted-foreground">
                {f.impact}
              </TableCell>
              <TableCell className="max-w-[180px] text-sm">{f.action}</TableCell>
              <TableCell>
                {f.addressed ? (
                  <Badge variant="success" className="gap-1">
                    <CheckCircle2 className="h-3 w-3" />
                    done
                  </Badge>
                ) : (
                  <Badge variant="outline">open</Badge>
                )}
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  );
}

export function PriorityMatrix({ items, findings }: { items: PriorityItem[]; findings: Finding[] }) {
  const findingMap = Object.fromEntries(findings.map((f) => [f.id, f]));

  return (
    <SectionCard
      title="Priority Matrix"
      description="Value vs risk scoring — selected item highlighted"
    >
      <div className="space-y-2">
        {items
          .slice()
          .sort((a, b) => b.score - a.score)
          .map((item) => {
            const finding = findingMap[item.finding_id];
            return (
              <div
                key={item.finding_id}
                className={cn(
                  "flex items-center justify-between rounded-lg border px-4 py-3",
                  item.selected && "border-primary bg-primary/5 ring-1 ring-primary/20",
                )}
              >
                <div className="flex items-center gap-3">
                  {item.selected && (
                    <Star className="h-4 w-4 fill-amber-400 text-amber-400" />
                  )}
                  <div>
                    <p className="text-sm font-medium">
                      {finding?.title ?? item.finding_id}
                    </p>
                    <p className="font-mono text-xs text-muted-foreground">
                      {item.finding_id}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <div className="text-right text-xs">
                    <p>
                      value: <span className="font-medium">{item.value}</span>
                    </p>
                    <p>
                      risk: <span className="font-medium">{item.risk}</span>
                    </p>
                  </div>
                  <div className="flex h-10 w-10 items-center justify-center rounded-full bg-muted text-sm font-bold">
                    {item.score}
                  </div>
                </div>
              </div>
            );
          })}
      </div>
    </SectionCard>
  );
}

export function ImplementedStepCard({ step }: { step: A4Data["implemented_step"] }) {
  return (
    <SectionCard title="Implemented Step" description="Highest-value first step applied">
      <div className="rounded-lg border bg-emerald-500/5 p-4">
        <div className="flex items-start justify-between">
          <div>
            <Badge variant="outline" className="font-mono">
              {step.finding_id}
            </Badge>
            <p className="mt-2 text-lg font-semibold">{step.title}</p>
            <p className="mt-1 font-mono text-sm text-muted-foreground">
              branch: {step.branch}
            </p>
            <p className="mt-1 font-mono text-xs text-muted-foreground">
              {step.patch_ref}
            </p>
          </div>
          <Badge variant={statusVariant(step.status)}>{statusLabel(step.status)}</Badge>
        </div>
        <p className="mt-4 text-sm">
          <span className="text-muted-foreground">Verification: </span>
          {step.verification}
        </p>
      </div>
    </SectionCard>
  );
}

export function RollbackNotes({ notes }: { notes: string[] }) {
  return (
    <SectionCard title="Rollback Notes" description="Steps to revert the first step">
      <div className="flex items-start gap-3 rounded-lg border border-amber-500/30 bg-amber-500/5 p-4">
        <RotateCcw className="mt-0.5 h-5 w-5 shrink-0 text-amber-600" />
        <ol className="list-decimal space-y-2 pl-4 text-sm">
          {notes.map((note, i) => (
            <li key={i} className="text-muted-foreground">
              {note}
            </li>
          ))}
        </ol>
      </div>
    </SectionCard>
  );
}

export function RepoMetaBar({
  targetRepo,
  baselineCommit,
}: {
  targetRepo: string;
  baselineCommit: string;
}) {
  return (
    <div className="flex flex-wrap gap-4 rounded-lg border bg-muted/30 px-4 py-3 text-sm">
      <div>
        <span className="text-muted-foreground">Target: </span>
        <span className="font-mono">{targetRepo}</span>
      </div>
      <div>
        <span className="text-muted-foreground">Baseline: </span>
        <span className="font-mono">{baselineCommit}</span>
      </div>
    </div>
  );
}
