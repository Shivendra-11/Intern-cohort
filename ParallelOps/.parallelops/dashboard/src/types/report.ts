export type ChartComponentType =
  | "execution_metrics"
  | "timeline"
  | "severity_distribution"
  | "branch_graph"
  | "worktree_graph"
  | "success_rate"
  | "priority_matrix";

export interface ChartPlanSection {
  id: string;
  component: ChartComponentType;
  title: string;
  description?: string;
  bindings: Record<string, string>;
}

export interface ChartPlan {
  schema_version: "1.0";
  sections: ChartPlanSection[];
}

export interface MetricItem {
  name: string;
  value: number;
  unit?: string;
}

export interface TimelineChartEvent {
  id: string;
  label: string;
  phase: string;
  timestamp: string;
  status: string;
  index?: number;
}

export interface SeveritySlice {
  name: string;
  value: number;
  fill?: string;
}

export interface GraphNode {
  name: string;
}

export interface GraphLink {
  source: number;
  target: number;
  value?: number;
}

export interface GraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

export interface SuccessRateData {
  current: number;
  label?: string;
  history?: { label: string; rate: number }[];
}

export interface PriorityMatrixPoint {
  id: string;
  label: string;
  value_score: number;
  risk_score: number;
  score: number;
  selected?: boolean;
}

export interface AgentReportJson {
  schema_version: string;
  agent: string;
  session_id: string;
  status: string;
  summary?: string;
  chart_plan: ChartPlan;
  charts: Record<string, unknown>;
  meta?: Record<string, unknown>;
}

export interface ArtifactsIndexJson {
  schema_version: string;
  updated_at: string;
  selected_session_id?: string;
  execution_status: string;
  repo_root?: string;
  repo_name?: string;
  sessions?: Array<{
    session_id: string;
    task?: string;
    mode?: string;
    repo_root?: string;
    repo_name?: string;
    started_at?: string;
    finished_at?: string | null;
    agents?: string[];
    overall_status?: string;
    agent_status?: Record<string, string>;
  }>;
  chart_plan: ChartPlan;
  charts: Record<string, unknown>;
  selected_evaluation?: Record<string, unknown>;
  agents?: string[];
}
