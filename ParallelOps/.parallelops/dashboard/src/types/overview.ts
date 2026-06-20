export type AgentStatus =
  | "pass"
  | "fail"
  | "partial"
  | "running"
  | "skipped"
  | "scaffolded";

export type OverallStatus = "pass" | "fail" | "partial" | "running";

export interface AgentCard {
  agent: "A1" | "A2" | "A3" | "A4" | "A5";
  label: string;
  status: AgentStatus;
  summary: string;
  duration_seconds: number | null;
  mode: "plan" | "build" | "build+verify";
  artifact_count: number;
}

export interface TimelineEvent {
  id: string;
  timestamp: string;
  agent: string;
  phase: string;
  message: string;
  level: "info" | "success" | "warning" | "error";
}

export interface GeneratedArtifact {
  id: string;
  agent: string;
  label: string;
  kind: "json" | "markdown" | "log" | "attachment";
  path: string;
  updated_at: string;
}

export interface RecentRun {
  session_id: string;
  task: string;
  repo_root: string;
  repo_name: string;
  overall_status: OverallStatus;
  agents: string[];
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  success_rate: number;
}

export interface OverviewMetrics {
  total_runs: number;
  agents_executed: number;
  artifacts_generated: number;
  avg_duration_seconds: number;
  success_rate_percent: number;
  running_count: number;
}

export interface SelectedEvaluation {
  session_id: string;
  task: string;
  mode: string;
  repo_root: string;
  repo_name: string;
  base_branch: string;
  overall_status: OverallStatus;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
  agents: string[];
}

export interface OverviewData {
  updated_at: string;
  selected_evaluation: SelectedEvaluation;
  execution_status: OverallStatus;
  metrics: OverviewMetrics;
  agent_cards: AgentCard[];
  generated_artifacts: GeneratedArtifact[];
  timeline: TimelineEvent[];
  recent_runs: RecentRun[];
}
