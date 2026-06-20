// src/components/TaskCard.tsx
import { useNavigate } from 'react-router-dom'
import type { AnyReport, TaskId } from '../types'
import { TASK_META } from '../types'
import StatusBadge from './StatusBadge'
import { formatDuration } from '../data/loadReports'

interface Props {
  taskId: TaskId
  report: AnyReport | null
}

const BORDER: Record<string, string> = {
  PASS:        'border-emerald-500/40 hover:border-emerald-500/70',
  WARN:        'border-amber-500/40  hover:border-amber-500/70',
  FAIL:        'border-red-500/40    hover:border-red-500/70',
  NOT_RUN:     'border-gray-700/40   hover:border-gray-600/60',
  IN_PROGRESS: 'border-blue-500/40   hover:border-blue-500/70',
}
const GLOW: Record<string, string> = {
  PASS:        'hover:shadow-emerald-500/10',
  WARN:        'hover:shadow-amber-500/10',
  FAIL:        'hover:shadow-red-500/10',
  NOT_RUN:     '',
  IN_PROGRESS: 'hover:shadow-blue-500/10',
}

function getMetric(report: AnyReport): string {
  if (!report || report.status === 'NOT_RUN') return '—'
  switch (report.task) {
    case 'D1': return `${(report as any).resource_count ?? '?'} resources`
    case 'D2': return `${(report as any).tests_passed ?? '?'}/${(report as any).tests_total ?? '?'} tests`
    case 'D3': return `${((report as any).stages ?? []).length} stages`
    case 'D4': return `${(report as any).replicas_ready ?? '?'}/2 pods`
    case 'D5': return `${(report as any).implicit_deps_documented ?? '?'} deps`
    case 'D6': return `${((report as any).dashboard_panels ?? []).length} panels`
    default: return '—'
  }
}

export default function TaskCard({ taskId, report }: Props) {
  const navigate = useNavigate()
  const meta = TASK_META[taskId]
  const status = report?.status ?? 'NOT_RUN'
  const border = BORDER[status] ?? BORDER['NOT_RUN']
  const glow = GLOW[status] ?? ''
  const dimmed = status === 'NOT_RUN'

  return (
    <div
      onClick={() => navigate(`/task/${taskId}`)}
      className={`
        group relative flex flex-col p-5 rounded-2xl border bg-gray-800/40 backdrop-blur-sm
        cursor-pointer transition-all duration-300
        hover:bg-gray-800/70 hover:shadow-xl hover:-translate-y-1 hover:scale-[1.02]
        ${border} ${glow} ${dimmed ? 'opacity-60' : ''}
      `}
    >
      {/* Task ID badge + Icon */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-2xl">{meta.icon}</span>
          <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-gray-700/60 text-gray-300 border border-gray-600/40">
            {taskId}
          </span>
        </div>
        <StatusBadge status={status} size="sm" />
      </div>

      {/* Title */}
      <h3 className="text-base font-semibold text-white mb-0.5">{meta.name}</h3>
      <p className="text-xs text-gray-400 mb-4">{meta.description}</p>

      {/* Metrics row */}
      <div className="flex items-center justify-between mt-auto text-xs">
        <span className="font-mono text-gray-300 bg-gray-700/40 px-2 py-1 rounded-md">
          {getMetric(report!)}
        </span>
        {report && report.duration_seconds > 0 ? (
          <span className="text-gray-500 font-mono">{formatDuration(report.duration_seconds)}</span>
        ) : (
          <span className="text-gray-600 font-mono">{meta.timebox} box</span>
        )}
      </div>

      {/* View arrow */}
      <div className="absolute bottom-4 right-5 text-gray-600 group-hover:text-gray-300 transition-colors text-sm">
        View →
      </div>
    </div>
  )
}
