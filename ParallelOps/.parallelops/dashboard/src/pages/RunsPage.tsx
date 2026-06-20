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
import { useArtifactsIndex } from "@/hooks/useArtifactJson";
import { statusLabel, statusVariant } from "@/lib/status";
import { useSession } from "@/stores/sessionStore";
import { Link } from "react-router-dom";

export function RunsPage() {
  const { data: index, loading } = useArtifactsIndex();
  const { setSessionId } = useSession();
  const sessions = index?.sessions ?? [];

  return (
    <div className="mx-auto max-w-[1600px] space-y-6">
      <div>
        <h2 className="text-lg font-semibold">Execution History</h2>
        <p className="text-sm text-muted-foreground">
          All eval runs from <span className="font-mono">index.json</span> — click a row to
          open that session.
        </p>
      </div>

      <Card>
        <CardHeader>
          <CardTitle className="text-base">Runs</CardTitle>
        </CardHeader>
        <CardContent className="p-0">
          {loading && !sessions.length ? (
            <p className="p-6 text-sm text-muted-foreground">Loading runs…</p>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Session</TableHead>
                  <TableHead>Repository</TableHead>
                  <TableHead>Task</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead>Agents</TableHead>
                  <TableHead>Started</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {sessions.map((run) => (
                  <TableRow
                    key={run.session_id}
                    className="cursor-pointer"
                    onClick={() => setSessionId(run.session_id)}
                  >
                    <TableCell>
                      <Link
                        to={`/?session=${run.session_id}`}
                        className="font-mono text-xs hover:underline"
                        onClick={(e) => e.stopPropagation()}
                      >
                        {run.session_id}
                      </Link>
                    </TableCell>
                    <TableCell className="max-w-[200px]">
                      <p className="truncate text-sm font-medium">
                        {(run as { repo_name?: string }).repo_name ?? "—"}
                      </p>
                      {(run as { repo_root?: string }).repo_root && (
                        <p
                          className="truncate font-mono text-[10px] text-muted-foreground"
                          title={(run as { repo_root?: string }).repo_root}
                        >
                          {(run as { repo_root?: string }).repo_root}
                        </p>
                      )}
                    </TableCell>
                    <TableCell className="max-w-md truncate text-sm">
                      {(run as { task?: string }).task ?? "—"}
                    </TableCell>
                    <TableCell>
                      <Badge variant={statusVariant(run.overall_status ?? "pass")}>
                        {statusLabel(run.overall_status ?? "pass")}
                      </Badge>
                    </TableCell>
                    <TableCell>
                      <div className="flex flex-wrap gap-1">
                        {((run as { agents?: string[] }).agents ?? []).map((a) => (
                          <Badge key={a} variant="outline" className="font-mono text-[10px]">
                            {a}
                          </Badge>
                        ))}
                      </div>
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {(run as { started_at?: string }).started_at ?? "—"}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
