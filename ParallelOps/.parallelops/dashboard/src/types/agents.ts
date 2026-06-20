import type { AgentStatus } from "./overview";

export interface AgentMeta {
  agent: "A1" | "A2" | "A3" | "A4" | "A5";
  session_id: string;
  status: AgentStatus;
  mode: "plan" | "build" | "build+verify";
  summary: string;
  started_at: string;
  finished_at: string | null;
  duration_seconds: number | null;
}

export interface DecompositionLane {
  lane_id: string;
  name: string;
  goal: string;
  branch: string;
  worktree: string;
  files_owned: string[];
  files_forbidden: string[];
}

export interface BranchInfo {
  name: string;
  lane_id: string;
  base: string;
}

export interface WorktreeInfo {
  name: string;
  path: string;
  branch: string;
  lane_id: string;
}

export interface RiskItem {
  id: string;
  category: string;
  description: string;
  mitigation: string;
  affected_lanes: string[];
  severity: "low" | "medium" | "high";
}

export interface VerificationStep {
  id: string;
  phase: string;
  command: string;
  required: boolean;
  status: "pass" | "fail" | "pending" | "n/a";
}

export interface A1Data {
  meta: AgentMeta;
  decomposition: DecompositionLane[];
  branches: BranchInfo[];
  worktrees: WorktreeInfo[];
  merge_order: string[];
  risk_plan: RiskItem[];
  verification_plan: VerificationStep[];
}

export interface TimelineStep {
  id: string;
  timestamp: string;
  phase: string;
  message: string;
  status: "pass" | "fail" | "running" | "info" | "warning";
}

export interface CommitInfo {
  sha: string;
  message: string;
  lane_id: string;
  branch: string;
  authored_at: string;
}

export interface MergeResult {
  lane_id: string;
  branch: string;
  status: "pass" | "fail" | "pending";
  conflict: boolean;
  conflict_files: string[];
  resolution?: string;
}

export interface A2Data {
  meta: AgentMeta;
  timeline: TimelineStep[];
  branches: BranchInfo[];
  commits: CommitInfo[];
  push_status: {
    enabled: boolean;
    pushed: boolean;
    branches: { name: string; pushed: boolean; remote?: string }[];
    message: string;
  };
  merge_status: MergeResult[];
  conflicts: {
    id: string;
    file: string;
    branches: string[];
    status: "resolved" | "open";
    resolution?: string;
  }[];
}

export interface StackComponent {
  id: string;
  name: string;
  role: string;
  lang: string;
  path: string;
  port?: number;
  status: "pass" | "fail" | "running";
  tests_passed: number;
  tests_failed: number;
}

export interface DataContract {
  id: string;
  from: string;
  to: string;
  format: string;
  description: string;
}

export interface IntegrationTest {
  id: string;
  name: string;
  suite: string;
  status: "pass" | "fail";
  passed: number;
  failed: number;
  command: string;
}

export interface A3Data {
  meta: AgentMeta;
  architecture: {
    flow: string[];
    components: StackComponent[];
  };
  data_contracts: DataContract[];
  integration_tests: IntegrationTest[];
}

export interface Finding {
  id: string;
  title: string;
  severity: "critical" | "high" | "medium" | "low";
  impact: string;
  evidence: string;
  action: string;
  addressed: boolean;
}

export interface PriorityItem {
  finding_id: string;
  score: number;
  value: "high" | "medium" | "low";
  risk: "high" | "medium" | "low";
  selected: boolean;
}

export interface A4Data {
  meta: AgentMeta;
  target_repo: string;
  baseline_commit: string;
  findings: Finding[];
  priority_matrix: PriorityItem[];
  implemented_step: {
    finding_id: string;
    title: string;
    branch: string;
    patch_ref: string;
    status: "pass" | "fail";
    verification: string;
  };
  rollback_notes: string[];
}

export interface ReviewIssue {
  id: string;
  title: string;
  category: string;
  severity: "critical" | "high" | "medium" | "low";
  blocking: boolean;
  location: string;
  description: string;
  fix_suggestion: string;
  verified: boolean;
}

export interface A5Data {
  meta: AgentMeta;
  issues: ReviewIssue[];
  severity_summary: {
    critical: number;
    high: number;
    medium: number;
    low: number;
    blocking: number;
    non_blocking: number;
  };
}
