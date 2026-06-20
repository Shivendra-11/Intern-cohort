export interface RepoInfo {
  id: string;
  repo_name: string;
  repo_path: string;
  workspace_dir: string;
  dashboard_path: string;
  generated_at: string;
  status: string;
}

export interface ReposList {
  workspace: string;
  default: string | null;
  count: number;
  repos: RepoInfo[];
}

export interface Overview {
  repo_id?: string;
  schema_version: string;
  role: string;
  repo: string;
  repo_name: string;
  repo_path: string;
  workspace_dir: string;
  generated_at: string;
  sources: SourceRecord[];
  summary: Summary;
}

export interface SourceRecord {
  key: string;
  relative_path: string;
  absolute_path: string;
  present: boolean;
  error: string | null;
}

export interface Summary {
  sources_loaded: number;
  sources_total: number;
  core: Record<string, boolean>;
  pipelines: {
    B1_inventory: string;
    B2_routes: string;
    B3_tests: string;
    graphs: string;
    greenfield: Record<string, string> | null;
  };
  counts: {
    artifacts_total: number | null;
    artifact_breakdown: Record<string, number> | null;
    routes_total: number | null;
    routes_backend: number | null;
    routes_frontend: number | null;
    tests_passed: number | null;
    tests_failed: number | null;
    tests_status: string | null;
    graph_types: string[] | null;
    greenfield_projects: number | null;
  };
}

export interface InventoryItem {
  name: string;
  type: string;
  file: string;
  line: number;
  syntactic_kind?: string;
  signature?: string;
}

export interface Inventory {
  repo_name: string;
  counts: Record<string, number>;
  artifacts: Record<string, InventoryItem[]>;
  items?: InventoryItem[];
}

export interface RouteRecord {
  method: string;
  path: string;
  file: string;
  line: number;
  framework: string;
  surface: string;
  handler?: string;
}

export interface Routes {
  repo_name: string;
  counts: Record<string, number>;
  backend: RouteRecord[];
  frontend: RouteRecord[];
  routes: RouteRecord[];
}

export interface Tests {
  repo_name: string;
  framework: string;
  status: string;
  passed: number | null;
  failed: number | null;
  test_files: string[];
  execution?: {
    command: string;
    exit_code: number;
    stdout: string;
    interpretation: string;
    status: string;
    duration_ms?: number;
  };
}

export interface GraphMeta {
  graph_type: string;
  metadata?: {
    node_count?: number;
    edge_count?: number;
    description?: string;
  };
}

export interface Graphs {
  repo_name: string;
  engine: string;
  graphs: Record<string, GraphMeta & { nodes?: unknown[]; edges?: unknown[] }>;
  metadata?: {
    graph_types: string[];
    total_nodes: number;
    total_edges: number;
  };
}

export interface ProjectStatus {
  project: string;
  status: string;
  repo_name: string;
  project_path: string;
  generated_at: string;
  endpoints?: { method: string; path: string }[];
  cli?: { binary: string; usage: string };
  stack?: Record<string, string>;
  proof?: {
    passed?: number;
    failed?: number;
    test_exit_code?: number;
  };
}

export type Projects = Record<string, ProjectStatus>;
