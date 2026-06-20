import { OverviewChartsSection } from "@/components/charts/OverviewChartsSection";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { AgentStatusCards } from "@/components/overview/AgentStatusCards";
import { ExecutionHistoryTable } from "@/components/overview/ExecutionHistoryTable";
import {
  ExecutionStatusHero,
  SelectedEvaluationCard,
} from "@/components/overview/ExecutionStatusHero";
import { useArtifactsIndex } from "@/hooks/useArtifactJson";
import { agentColor, statusLabel, statusVariant } from "@/lib/status";
import { cn } from "@/lib/utils";
import { useSession } from "@/stores/sessionStore";
import type { AgentCard, RecentRun } from "@/types/overview";
import { Link } from "react-router-dom";

const AGENT_LABELS: Record<string, string> = {
  A1: "Multi-Worktree Plan",
  A2: "Parallel Worktrees",
  A3: "Polyglot System",
  A4: "Modernization",
  A5: "Code Review",
  A6: "Perf Profiler",
};

export function OverviewPage() {
  const { data: index, loading } = useArtifactsIndex();
  const { sessionId } = useSession();

  const selected = index?.selected_evaluation as Record<string, unknown> | undefined;
  const currentSession = index?.sessions?.find((s) => s.session_id === sessionId);

  const evaluation = {
    session_id: String(sessionId ?? selected?.session_id ?? ""),
    task: String(currentSession?.task ?? selected?.task ?? "ParallelOps eval"),
    mode: String(currentSession?.mode ?? selected?.mode ?? "build+verify"),
    repo_root: String(
      currentSession?.repo_root ??
        selected?.repo_root ??
        index?.repo_root ??
        "",
    ),
    repo_name: String(
      currentSession?.repo_name ??
        selected?.repo_name ??
        index?.repo_name ??
        "",
    ),
    base_branch: "main",
    overall_status: (currentSession?.overall_status ??
      selected?.overall_status ??
      index?.execution_status ??
      "pass") as "pass" | "fail" | "partial" | "running",
    started_at: String(currentSession?.started_at ?? ""),
    finished_at: (currentSession?.finished_at as string | null) ?? null,
    duration_seconds: null,
    agents: (currentSession?.agents ?? selected?.agents ?? []) as string[],
  };

  const recentRuns: RecentRun[] = (index?.sessions ?? []).map((s) => {
    const agents = s.agents ?? [];
    const statuses = s.agent_status ?? {};
    const passCount = agents.filter((a) => statuses[a] === "pass").length;
    return {
      session_id: s.session_id,
      task: s.task ?? "ParallelOps eval",
      repo_root: s.repo_root ?? "",
      repo_name: s.repo_name ?? "",
      overall_status: (s.overall_status ?? "pass") as RecentRun["overall_status"],
      agents,
      started_at: s.started_at ?? "",
      finished_at: s.finished_at ?? null,
      duration_seconds: null,
      success_rate: agents.length ? Math.round((100 * passCount) / agents.length) : 0,
    };
  });

  const agentCards: AgentCard[] = (evaluation.agents as string[]).map((agent) => {
    const status =
      (currentSession?.agent_status?.[agent] as AgentCard["status"]) ?? "pass";
    return {
      agent: agent as AgentCard["agent"],
      label: AGENT_LABELS[agent] ?? agent,
      status,
      summary: `${agent} — ${statusLabel(status)}`,
      duration_seconds: null,
      mode: evaluation.mode as AgentCard["mode"],
      artifact_count: 4,
    };
  });

  return (
    <div className="mx-auto max-w-[1600px] space-y-8">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <p className="text-sm text-muted-foreground">
          Live dashboard · polls <span className="font-mono">index.json</span> + session
          artifacts every 3s
        </p>
        {!loading && index?.updated_at && (
          <span className="font-mono text-[10px] text-muted-foreground">
            index updated {new Date(index.updated_at).toLocaleTimeString()}
          </span>
        )}
      </div>

      <ExecutionStatusHero
        status={evaluation.overall_status}
        evaluation={evaluation}
      />

      <OverviewChartsSection />

      <SelectedEvaluationCard evaluation={evaluation} />

      {agentCards.length > 0 ? (
        <AgentStatusCards agents={agentCards} />
      ) : (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Agents</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm text-muted-foreground">
              No agents in this session. Run{" "}
              <span className="font-mono">/parallelops-eval</span> and finalize artifacts.
            </p>
          </CardContent>
        </Card>
      )}

      {recentRuns.length > 0 && <ExecutionHistoryTable runs={recentRuns} />}

      <Card>
        <CardHeader>
          <CardTitle className="text-base">All Agents (A1–A6)</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-6">
            {(["A1", "A2", "A3", "A4", "A5", "A6"] as const).map((agent) => {
              const inSession = evaluation.agents.includes(agent);
              const status = currentSession?.agent_status?.[agent];
              return (
                <Link
                  key={agent}
                  to={`/agents/${agent}?session=${sessionId ?? ""}`}
                  className={cn(
                    "rounded-lg border p-4 transition-all hover:border-foreground/20 hover:shadow-md",
                    !inSession && "opacity-50",
                  )}
                >
                  <div className="flex items-center gap-2">
                    <span
                      className={cn(
                        "flex h-7 w-7 items-center justify-center rounded-md text-xs font-bold text-white",
                        agentColor(agent),
                      )}
                    >
                      {agent}
                    </span>
                    {status && (
                      <Badge variant={statusVariant(status)} className="text-[10px]">
                        {statusLabel(status)}
                      </Badge>
                    )}
                  </div>
                  <p className="mt-2 text-sm font-medium">{AGENT_LABELS[agent]}</p>
                </Link>
              );
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
