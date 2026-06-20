import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { statusLabel, statusVariant } from "@/lib/status";
import { formatDateTime, formatDuration, formatRelativeTime } from "@/lib/utils";
import type { RecentRun } from "@/types/overview";
import { History } from "lucide-react";

interface ExecutionHistoryTableProps {
  runs: RecentRun[];
}

export function ExecutionHistoryTable({ runs }: ExecutionHistoryTableProps) {
  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between pb-3">
        <div>
          <CardTitle className="text-sm font-medium text-muted-foreground">
            Execution History
          </CardTitle>
          <p className="mt-1 text-xs text-muted-foreground">Recent Runs</p>
        </div>
        <History className="h-4 w-4 text-muted-foreground" />
      </CardHeader>
      <CardContent className="p-0">
        <Table>
          <TableHeader>
            <TableRow className="hover:bg-transparent">
              <TableHead>Session</TableHead>
              <TableHead>Repository</TableHead>
              <TableHead>Task</TableHead>
              <TableHead>Status</TableHead>
              <TableHead>Agents</TableHead>
              <TableHead>Duration</TableHead>
              <TableHead>Success</TableHead>
              <TableHead>When</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {runs.map((run) => (
              <TableRow key={run.session_id} className="cursor-pointer">
                <TableCell className="font-mono text-xs">
                  {run.session_id}
                </TableCell>
                <TableCell className="max-w-[180px]">
                  <p className="truncate text-sm font-medium">
                    {run.repo_name || "—"}
                  </p>
                  {run.repo_root && (
                    <p
                      className="truncate font-mono text-[10px] text-muted-foreground"
                      title={run.repo_root}
                    >
                      {run.repo_root}
                    </p>
                  )}
                </TableCell>
                <TableCell className="max-w-[220px] truncate text-sm">
                  {run.task}
                </TableCell>
                <TableCell>
                  <Badge variant={statusVariant(run.overall_status)}>
                    {statusLabel(run.overall_status)}
                  </Badge>
                </TableCell>
                <TableCell>
                  <div className="flex flex-wrap gap-1">
                    {run.agents.map((a) => (
                      <Badge
                        key={a}
                        variant="outline"
                        className="font-mono text-[10px]"
                      >
                        {a}
                      </Badge>
                    ))}
                  </div>
                </TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  {run.duration_seconds
                    ? formatDuration(run.duration_seconds)
                    : "—"}
                </TableCell>
                <TableCell className="text-sm">{run.success_rate}%</TableCell>
                <TableCell className="text-sm text-muted-foreground">
                  <span title={formatDateTime(run.started_at)}>
                    {formatRelativeTime(run.started_at)}
                  </span>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  );
}
