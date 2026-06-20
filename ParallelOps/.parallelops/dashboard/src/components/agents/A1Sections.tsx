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
import type {
  BranchInfo,
  DecompositionLane,
  RiskItem,
  VerificationStep,
  WorktreeInfo,
} from "@/types/agents";
import { ArrowRight, GitBranch, GitMerge } from "lucide-react";
import { SectionCard } from "./AgentPageHeader";

export function DecompositionTable({ lanes }: { lanes: DecompositionLane[] }) {
  return (
    <SectionCard
      title="Task Decomposition"
      description="Independent lanes with owned and forbidden file lists"
    >
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Lane</TableHead>
            <TableHead>Goal</TableHead>
            <TableHead>Owned</TableHead>
            <TableHead>Forbidden</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {lanes.map((lane) => (
            <TableRow key={lane.lane_id}>
              <TableCell>
                <div>
                  <p className="font-medium">{lane.name}</p>
                  <p className="font-mono text-xs text-muted-foreground">
                    {lane.lane_id}
                  </p>
                </div>
              </TableCell>
              <TableCell className="max-w-xs text-sm">{lane.goal}</TableCell>
              <TableCell>
                <FileChips files={lane.files_owned} variant="owned" />
              </TableCell>
              <TableCell>
                <FileChips files={lane.files_forbidden} variant="forbidden" />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  );
}

function FileChips({
  files,
  variant,
}: {
  files: string[];
  variant: "owned" | "forbidden";
}) {
  return (
    <div className="flex max-w-[200px] flex-wrap gap-1">
      {files.map((f) => (
        <Badge
          key={f}
          variant="outline"
          className={
            variant === "forbidden"
              ? "border-red-500/30 text-[10px] text-red-700 dark:text-red-400"
              : "text-[10px]"
          }
        >
          {f.split("/").pop()}
        </Badge>
      ))}
    </div>
  );
}

export function BranchTable({ branches }: { branches: BranchInfo[] }) {
  return (
    <SectionCard title="Branches" description="Feature branches per lane">
      <div className="space-y-2">
        {branches.map((b) => (
          <div
            key={b.name}
            className="flex items-center justify-between rounded-lg border bg-muted/30 px-4 py-3"
          >
            <div className="flex items-center gap-3">
              <GitBranch className="h-4 w-4 text-muted-foreground" />
              <div>
                <p className="font-mono text-sm font-medium">{b.name}</p>
                <p className="text-xs text-muted-foreground">
                  lane: {b.lane_id} · base: {b.base}
                </p>
              </div>
            </div>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export function WorktreeList({ worktrees }: { worktrees: WorktreeInfo[] }) {
  return (
    <SectionCard title="Worktrees" description="Planned git worktree paths">
      <div className="space-y-2">
        {worktrees.map((wt) => (
          <div
            key={wt.name}
            className="rounded-lg border px-4 py-3"
          >
            <div className="flex items-center justify-between">
              <p className="font-medium">{wt.name}</p>
              <Badge variant="secondary" className="font-mono text-[10px]">
                {wt.lane_id}
              </Badge>
            </div>
            <p className="mt-1 font-mono text-xs text-muted-foreground">{wt.path}</p>
            <p className="mt-1 text-xs">
              branch: <span className="font-mono">{wt.branch}</span>
            </p>
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export function MergeOrderPipeline({ order }: { order: string[] }) {
  return (
    <SectionCard title="Merge Order" description="Integrator merge sequence">
      <div className="flex flex-wrap items-center gap-2">
        {order.map((lane, i) => (
          <div key={lane} className="flex items-center gap-2">
            <div className="flex items-center gap-2 rounded-lg border bg-background px-3 py-2">
              <GitMerge className="h-4 w-4 text-muted-foreground" />
              <span className="font-mono text-sm font-medium">{lane}</span>
              <Badge variant="outline" className="text-[10px]">
                #{i + 1}
              </Badge>
            </div>
            {i < order.length - 1 && (
              <ArrowRight className="h-4 w-4 text-muted-foreground" />
            )}
          </div>
        ))}
      </div>
    </SectionCard>
  );
}

export function RiskPlanTable({ risks }: { risks: RiskItem[] }) {
  const severityVariant = {
    high: "destructive" as const,
    medium: "warning" as const,
    low: "secondary" as const,
  };

  return (
    <SectionCard title="Risk Plan" description="Identified risks and mitigations">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>ID</TableHead>
            <TableHead>Category</TableHead>
            <TableHead>Description</TableHead>
            <TableHead>Mitigation</TableHead>
            <TableHead>Lanes</TableHead>
            <TableHead>Severity</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {risks.map((r) => (
            <TableRow key={r.id}>
              <TableCell className="font-mono text-xs">{r.id}</TableCell>
              <TableCell className="text-sm">{r.category}</TableCell>
              <TableCell className="max-w-[200px] text-sm">{r.description}</TableCell>
              <TableCell className="max-w-[200px] text-sm text-muted-foreground">
                {r.mitigation}
              </TableCell>
              <TableCell>
                <div className="flex flex-wrap gap-1">
                  {r.affected_lanes.map((l) => (
                    <Badge key={l} variant="outline" className="text-[10px]">
                      {l}
                    </Badge>
                  ))}
                </div>
              </TableCell>
              <TableCell>
                <Badge variant={severityVariant[r.severity]}>{r.severity}</Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  );
}

export function VerificationPlanTable({ steps }: { steps: VerificationStep[] }) {
  return (
    <SectionCard title="Verification Plan" description="Commands and gates per phase">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead>Phase</TableHead>
            <TableHead>Command</TableHead>
            <TableHead>Required</TableHead>
            <TableHead>Status</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          {steps.map((s) => (
            <TableRow key={s.id}>
              <TableCell className="font-mono text-xs">{s.phase}</TableCell>
              <TableCell className="max-w-md font-mono text-xs">{s.command}</TableCell>
              <TableCell>
                <Badge variant={s.required ? "default" : "secondary"}>
                  {s.required ? "required" : "optional"}
                </Badge>
              </TableCell>
              <TableCell>
                <Badge variant={statusVariant(s.status === "n/a" ? "skipped" : s.status)}>
                  {s.status === "n/a" ? "N/A" : statusLabel(s.status as "pass" | "fail")}
                </Badge>
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    </SectionCard>
  );
}
