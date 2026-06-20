import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadAllReports } from '../data/loadReports'
import type { AnyReport } from '../types'
import { TASK_META, type TaskId } from '../types'
import StatusBadge from '../components/StatusBadge'
import { formatDuration } from '../data/loadReports'

const TASK_IDS: TaskId[] = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

export default function ServicesHubPage() {
  const [reports, setReports] = useState<AnyReport[]>([])

  useEffect(() => {
    loadAllReports().then(setReports)
  }, [])

  const byTask = Object.fromEntries(reports.map(r => [r.task, r]))
  const pass   = reports.filter(r => r.status === 'PASS').length
  const total  = reports.length

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 relative overflow-hidden">
      {/* Ambient blobs */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-32 -left-32 w-80 h-80 bg-violet-600/5 rounded-full blur-3xl" />
        <div className="absolute bottom-0 right-0 w-80 h-80 bg-blue-600/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 p-6 max-w-5xl mx-auto">
        <nav className="mb-6 animate-fade-in">
          <Link to="/" className="inline-flex items-center gap-2 text-gray-400 hover:text-white text-sm transition-colors">
            ← Back to dashboard
          </Link>
        </nav>

        <header className="mb-8 animate-slide-up">
          <div className="flex items-start justify-between flex-wrap gap-4">
            <div>
              <h1 className="text-3xl font-bold text-white flex items-center gap-3">
                <span className="w-10 h-10 rounded-xl bg-violet-500/20 border border-violet-500/30 flex items-center justify-center text-xl">📋</span>
                All Tasks
              </h1>
              <p className="text-gray-400 mt-2 text-sm">
                D1–D6 eval reports — click any task for status, proof, and artifacts.
              </p>
            </div>
            {total > 0 && (
              <div className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-sm font-mono font-bold">
                <span className="w-2 h-2 rounded-full bg-emerald-400" />
                {pass}/{total} passing
              </div>
            )}
          </div>
        </header>

        <div className="grid gap-3 sm:grid-cols-2">
          {TASK_IDS.map((tid, i) => {
            const r    = byTask[tid]
            const meta = TASK_META[tid]
            const status = r?.status ?? 'NOT_RUN'
            const accentColor =
              status === 'PASS'        ? 'border-l-emerald-500/50' :
              status === 'WARN'        ? 'border-l-amber-500/50'   :
              status === 'FAIL'        ? 'border-l-red-500/50'     :
              status === 'IN_PROGRESS' ? 'border-l-blue-500/50'    : 'border-l-gray-700/50'

            return (
              <Link
                key={tid}
                to={`/task/${tid}`}
                className={`flex items-start gap-4 p-4 rounded-xl bg-gray-900/60 hover:bg-gray-800/60
                  border border-gray-700/30 border-l-2 ${accentColor}
                  transition-all duration-200 hover:-translate-y-0.5 hover:shadow-lg
                  animate-slide-up stagger-${i + 1}`}
              >
                <div className="w-10 h-10 rounded-xl bg-gray-800/80 border border-gray-700/40 flex items-center justify-center text-xl flex-shrink-0">
                  {meta.icon}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2 mb-0.5">
                    <span className="font-mono font-bold text-white text-sm">{tid}</span>
                    <StatusBadge status={status} size="sm" />
                  </div>
                  <p className="text-sm text-gray-300 font-medium truncate">{meta.name}</p>
                  <p className="text-xs text-gray-500 mt-0.5 truncate">{meta.description}</p>
                  {r && r.duration_seconds > 0 && (
                    <p className="text-xs text-gray-600 font-mono mt-1.5">⏱ {formatDuration(r.duration_seconds)}</p>
                  )}
                </div>
              </Link>
            )
          })}
        </div>

        <footer className="mt-10 pt-5 border-t border-gray-800/40 text-center text-xs text-gray-600 font-mono">
          DevOps-Infra Eval · {pass}/{total} tasks passing
        </footer>
      </div>
    </div>
  )
}
