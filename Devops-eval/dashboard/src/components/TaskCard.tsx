// src/components/TaskCard.tsx
import { useNavigate } from 'react-router-dom'
import type { AnyReport, TaskId } from '../types'
import { TASK_META } from '../types'
import StatusBadge from './StatusBadge'
import { formatDuration } from '../data/loadReports'

interface Props {
  taskId: TaskId
  report: AnyReport | null
  index?: number
}

const STATUS_STYLE: Record<string, { border: string; bg: string; glow: string; accent: string }> = {
  PASS:        { border: 'border-emerald-500/35', bg: 'hover:bg-emerald-950/30', glow: 'hover:shadow-emerald-500/10 hover:shadow-xl', accent: 'bg-emerald-500' },
  WARN:        { border: 'border-amber-500/35',   bg: 'hover:bg-amber-950/20',   glow: 'hover:shadow-amber-500/10 hover:shadow-xl',   accent: 'bg-amber-500'   },
  FAIL:        { border: 'border-red-500/35',     bg: 'hover:bg-red-950/20',     glow: 'hover:shadow-red-500/10 hover:shadow-xl',     accent: 'bg-red-500'     },
  NOT_RUN:     { border: 'border-gray-700/40',    bg: 'hover:bg-gray-800/50',    glow: '',                                            accent: 'bg-gray-600'    },
  IN_PROGRESS: { border: 'border-blue-500/35',    bg: 'hover:bg-blue-950/20',    glow: 'hover:shadow-blue-500/10 hover:shadow-xl',    accent: 'bg-blue-500 animate-pulse' },
}

const ACCENT_GRADIENT: Record<string, string> = {
  PASS:        'from-emerald-500/20 to-transparent',
  WARN:        'from-amber-500/15 to-transparent',
  FAIL:        'from-red-500/15 to-transparent',
  NOT_RUN:     'from-gray-700/10 to-transparent',
  IN_PROGRESS: 'from-blue-500/15 to-transparent',
}

function getMetric(report: AnyReport): { value: string; label: string; pct?: number } {
  if (!report || report.status === 'NOT_RUN') return { value: '—', label: 'not run' }
  switch (report.task) {
    case 'D1': {
      const rc = (report as any).resource_count ?? 0
      return { value: `${rc}`, label: 'resources', pct: Math.min(rc / 12, 1) }
    }
    case 'D2': {
      const p = (report as any).tests_passed ?? 0
      const t = (report as any).tests_total  ?? 5
      return { value: `${p}/${t}`, label: 'tests pass', pct: t > 0 ? p / t : 0 }
    }
    case 'D3': {
      const s = ((report as any).stages ?? []).length
      return { value: `${s}`, label: 'stages', pct: s / 3 }
    }
    case 'D4': {
      const r = (report as any).replicas_ready ?? 0
      return { value: `${r}/2`, label: 'pods ready', pct: r / 2 }
    }
    case 'D5': {
      const d = (report as any).implicit_deps_documented ?? 0
      return { value: `${d}`, label: 'deps documented', pct: Math.min(d / 5, 1) }
    }
    case 'D6': {
      const panels = ((report as any).dashboard_panels ?? []).length
      return { value: `${panels}`, label: 'panels', pct: Math.min(panels / 6, 1) }
    }
    default: return { value: '—', label: '' }
  }
}

const STAGGER = ['stagger-1', 'stagger-2', 'stagger-3', 'stagger-4', 'stagger-5', 'stagger-6']

export default function TaskCard({ taskId, report, index = 0 }: Props) {
  const navigate = useNavigate()
  const meta   = TASK_META[taskId]
  const status = report?.status ?? 'NOT_RUN'
  const style  = STATUS_STYLE[status] ?? STATUS_STYLE['NOT_RUN']
  const dimmed = status === 'NOT_RUN'
  const metric = report ? getMetric(report) : { value: '—', label: 'not run' }

  return (
    <div
      onClick={() => navigate(`/task/${taskId}`)}
      className={`
        group relative flex flex-col rounded-2xl border bg-gray-900/60 backdrop-blur-sm
        cursor-pointer transition-all duration-300 overflow-hidden card-hover animate-slide-up
        ${style.border} ${style.bg} ${style.glow} ${STAGGER[index % 6]}
        ${dimmed ? 'opacity-55' : ''}
      `}
    >
      {/* Top accent stripe */}
      <div className={`h-0.5 w-full bg-gradient-to-r ${ACCENT_GRADIENT[status]}`} />

      {/* Side accent bar */}
      <div className={`absolute left-0 top-4 bottom-4 w-0.5 rounded-full ${style.accent} opacity-60`} />

      <div className="p-5 flex flex-col flex-1">
        {/* Header row: ID + icon + status badge */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2.5">
            <div className="w-9 h-9 rounded-xl bg-gray-800/80 border border-gray-700/50 flex items-center justify-center text-lg">
              {meta.icon}
            </div>
            <div>
              <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-gray-800/80 text-gray-300 border border-gray-700/40">
                {taskId}
              </span>
            </div>
          </div>
          <StatusBadge status={status} size="sm" />
        </div>

        {/* Title + description */}
        <h3 className="text-sm font-semibold text-white mb-0.5 leading-snug">{meta.name}</h3>
        <p className="text-xs text-gray-500 mb-4 leading-relaxed">{meta.description}</p>

        {/* Metric + mini progress bar */}
        <div className="mt-auto space-y-2">
          <div className="flex items-center justify-between text-xs">
            <span className="font-mono text-gray-200 font-semibold">{metric.value}</span>
            <span className="text-gray-500">{metric.label}</span>
          </div>

          {metric.pct !== undefined && report && report.status !== 'NOT_RUN' ? (
            <div className="h-1 bg-gray-800 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all duration-700 ${
                  status === 'PASS' ? 'bg-emerald-500' :
                  status === 'WARN' ? 'bg-amber-500'   :
                  status === 'FAIL' ? 'bg-red-500'     : 'bg-blue-500'
                }`}
                style={{ width: `${metric.pct * 100}%` }}
              />
            </div>
          ) : (
            <div className="h-1 bg-gray-800 rounded-full" />
          )}

          {/* Duration + timebox */}
          <div className="flex items-center justify-between text-xs pt-1">
            {report && report.duration_seconds > 0 ? (
              <span className="text-gray-400 font-mono">{formatDuration(report.duration_seconds)}</span>
            ) : (
              <span className="text-gray-600 font-mono">{meta.timebox} box</span>
            )}
            <span className="text-gray-600 group-hover:text-gray-300 transition-colors font-mono text-xs">
              view →
            </span>
          </div>
        </div>
      </div>
    </div>
  )
}
