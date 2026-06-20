// src/types.ts — shared TypeScript types for all REPORT.json schemas

export type TaskStatus = 'PASS' | 'WARN' | 'FAIL' | 'NOT_RUN' | 'IN_PROGRESS'

export type TaskId = 'D1' | 'D2' | 'D3' | 'D4' | 'D5' | 'D6'

export interface BaseReport {
  task: TaskId
  status: TaskStatus
  description: string
  duration_seconds: number
  artifacts: string[]
  timestamp: string
}

export interface D1Report extends BaseReport {
  task: 'D1'
  validate_exit_code: number
  plan_exit_code: number
  resource_count: number
  resources: string[]
  proof_excerpt: string
}

export interface D2Report extends BaseReport {
  task: 'D2'
  services: string[]
  tests_total: number
  tests_passed: number
  tests_failed: number
  cross_service_log_lines: number
  teardown_command: string
  clean_reup_command: string
}

export interface D3Report extends BaseReport {
  task: 'D3'
  pipeline_tool: string
  stages: string[]
  matrix: string[]
  cache_configured: boolean
  green_run_log: string
  failure_demo_log: string
}

export interface D4Report extends BaseReport {
  task: 'D4'
  cluster_tool: string
  namespace: string
  manifest_files: string[]
  dry_run_exit_code: number
  apply_exit_code: number
  replicas_ready: number
  curl_status_code: number
  curl_response_excerpt: string
}

export interface D5Report extends BaseReport {
  task: 'D5'
  bootstrap_command: string
  bootstrap_exit_code: number
  test_command: string
  test_exit_code: number
  implicit_deps_documented: number
}

export interface D6Report extends BaseReport {
  task: 'D6'
  metrics_endpoint: string
  prometheus_url: string
  grafana_url: string
  dashboard_panels: string[]
  load_script: string
  screenshot: string
  log_format: string
}

export type AnyReport = D1Report | D2Report | D3Report | D4Report | D5Report | D6Report

export interface TaskMeta {
  id: TaskId
  name: string
  folder: string
  timebox: string
  description: string
  icon: string
}

export const TASK_META: Record<TaskId, TaskMeta> = {
  D1: { id: 'D1', name: 'Terraform Plan', folder: 'd1-terraform', timebox: '60m', description: 'S3 + Lambda + API Gateway', icon: '🏗️' },
  D2: { id: 'D2', name: 'Compose Stack',  folder: 'd2-compose-stack', timebox: '90m', description: 'FastAPI + Postgres + Worker', icon: '🐳' },
  D3: { id: 'D3', name: 'CI Pipeline',    folder: 'd3-ci-pipeline', timebox: '45m', description: 'lint → test → build-image', icon: '⚙️' },
  D4: { id: 'D4', name: 'Kubernetes',     folder: 'd4-kubernetes', timebox: '60m', description: 'kind cluster + manifests', icon: '☸️' },
  D5: { id: 'D5', name: 'Dev Env',        folder: 'd5-dev-env', timebox: '45m', description: 'devcontainer.json + Makefile', icon: '💻' },
  D6: { id: 'D6', name: 'Observability',  folder: 'd6-observability', timebox: '60m', description: 'Prometheus + Grafana + logs', icon: '📊' },
}
