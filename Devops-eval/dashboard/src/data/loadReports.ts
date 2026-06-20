// src/data/loadReports.ts — reads all REPORT.json files via fetch()
import type { AnyReport, TaskId, TaskStatus } from '../types'
import { TASK_META } from '../types'

const TASK_IDS: TaskId[] = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

function makeNotRun(task: TaskId): AnyReport {
  return {
    task,
    status: 'NOT_RUN' as TaskStatus,
    description: TASK_META[task].description,
    duration_seconds: 0,
    artifacts: [],
    timestamp: '',
  } as unknown as AnyReport
}

export async function loadReport(task: TaskId): Promise<AnyReport> {
  const folder = TASK_META[task].folder
  try {
    const res = await fetch(`/reports/${folder}/REPORT.json`, { cache: 'no-store' })
    if (!res.ok) return makeNotRun(task)
    const data = await res.json()
    return data as AnyReport
  } catch {
    return makeNotRun(task)
  }
}

export async function loadAllReports(): Promise<AnyReport[]> {
  return Promise.all(TASK_IDS.map(loadReport))
}

export function formatDuration(seconds: number): string {
  if (!seconds) return '—'
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return m > 0 ? `${m}m ${s}s` : `${s}s`
}

export function totalDuration(reports: AnyReport[]): string {
  const total = reports.reduce((sum, r) => sum + (r.duration_seconds || 0), 0)
  return formatDuration(total)
}
