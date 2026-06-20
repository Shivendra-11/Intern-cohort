import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import type { A5Data, ReviewIssue } from "@/types/agents";
import { AlertOctagon, Ban, CheckCircle2, ShieldAlert } from "lucide-react";
import { SectionCard } from "./AgentPageHeader";

const severityVariant = {
  critical: "destructive" as const,
  high: "warning" as const,
  medium: "secondary" as const,
  low: "muted" as const,
};

export function SeveritySummaryCards({
  summary,
}: {
  summary: A5Data["severity_summary"];
}) {
  const cards = [
    { label: "Critical", value: summary.critical, variant: "destructive" as const },
    { label: "High", value: summary.high, variant: "warning" as const },
    { label: "Medium", value: summary.medium, variant: "secondary" as const },
    { label: "Low", value: summary.low, variant: "muted" as const },
    { label: "Blocking", value: summary.blocking, variant: "destructive" as const, icon: Ban },
    {
      label: "Non-blocking",
      value: summary.non_blocking,
      variant: "secondary" as const,
      icon: CheckCircle2,
    },
  ];

  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-6">
      {cards.map(({ label, value, variant, icon: Icon }) => (
        <Card key={label}>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <p className="text-xs text-muted-foreground">{label}</p>
              {Icon && <Icon className="h-3.5 w-3.5 text-muted-foreground" />}
            </div>
            <p className="mt-1 text-2xl font-semibold">{value}</p>
            <Badge variant={variant} className="mt-2 text-[10px]">
              {label.toLowerCase()}
            </Badge>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}

export function IssuesTable({ issues }: { issues: ReviewIssue[] }) {
  const blocking = issues.filter((i) => i.blocking);
  const nonBlocking = issues.filter((i) => !i.blocking);

  return (
    <div className="space-y-6">
      <IssueGroup title="Blocking Issues" issues={blocking} emptyMessage="No blocking issues" />
      <IssueGroup
        title="Non-blocking Issues"
        issues={nonBlocking}
        emptyMessage="No non-blocking issues"
      />
    </div>
  );
}

function IssueGroup({
  title,
  issues,
  emptyMessage,
}: {
  title: string;
  issues: ReviewIssue[];
  emptyMessage: string;
}) {
  return (
    <SectionCard title={title}>
      {issues.length === 0 ? (
        <p className="text-sm text-muted-foreground">{emptyMessage}</p>
      ) : (
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>ID</TableHead>
              <TableHead>Issue</TableHead>
              <TableHead>Category</TableHead>
              <TableHead>Severity</TableHead>
              <TableHead>Location</TableHead>
              <TableHead>Fix Suggestion</TableHead>
              <TableHead>Verified</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {issues.map((issue) => (
              <TableRow key={issue.id}>
                <TableCell className="font-mono text-xs">{issue.id}</TableCell>
                <TableCell>
                  <div className="flex items-start gap-2">
                    {issue.blocking ? (
                      <Ban className="mt-0.5 h-4 w-4 shrink-0 text-red-500" />
                    ) : (
                      <AlertOctagon className="mt-0.5 h-4 w-4 shrink-0 text-muted-foreground" />
                    )}
                    <div>
                      <p className="font-medium">{issue.title}</p>
                      <p className="mt-0.5 max-w-xs text-xs text-muted-foreground">
                        {issue.description}
                      </p>
                    </div>
                  </div>
                </TableCell>
                <TableCell>
                  <Badge variant="outline" className="text-[10px]">
                    {issue.category}
                  </Badge>
                </TableCell>
                <TableCell>
                  <Badge variant={severityVariant[issue.severity]}>
                    {issue.severity}
                  </Badge>
                </TableCell>
                <TableCell className="font-mono text-xs">{issue.location}</TableCell>
                <TableCell className="max-w-[220px] text-sm">
                  {issue.fix_suggestion}
                </TableCell>
                <TableCell>
                  {issue.verified ? (
                    <Badge variant="success" className="gap-1">
                      <ShieldAlert className="h-3 w-3" />
                      yes
                    </Badge>
                  ) : (
                    <Badge variant="outline">no</Badge>
                  )}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      )}
    </SectionCard>
  );
}
