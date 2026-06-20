import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { loadAllReports } from '../data/loadReports'
import type { AnyReport } from '../types'
import { TASK_META, type TaskId } from '../types'
import StatusBadge from '../components/StatusBadge'

export default function ServicesHubPage() {
  const [reports, setReports] = useState<AnyReport[]>([])

  useEffect(() => {
    loadAllReports().then(setReports)
  }, [])

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 max-w-5xl mx-auto">
      <nav className="mb-6">
        <Link to="/" className="text-gray-400 hover:text-white text-sm">← Back to dashboard</Link>
      </nav>

      <header className="mb-8">
        <h1 className="text-3xl font-bold text-white flex items-center gap-3">
          <span>📋</span> All tasks
        </h1>
        <p className="text-gray-400 mt-2 text-sm">
          D1–D6 eval reports — open any task for status, proof, and artifacts.
        </p>
      </header>

      <section className="p-5 rounded-xl bg-gray-800/30 border border-gray-700/40">
        <div className="grid gap-3 sm:grid-cols-2">
          {(['D1', 'D2', 'D3', 'D4', 'D5', 'D6'] as TaskId[]).map(tid => {
            const r = reports.find(x => x.task === tid)
            const meta = TASK_META[tid]
            return (
              <Link
                key={tid}
                to={`/task/${tid}`}
                className="flex items-start gap-4 p-4 rounded-xl bg-gray-900/50 hover:bg-gray-800/60 border border-gray-700/30 transition-colors"
              >
                <span className="text-2xl">{meta.icon}</span>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between gap-2">
                    <span className="font-mono font-semibold text-white">{tid}</span>
                    {r ? <StatusBadge status={r.status} size="sm" /> : <StatusBadge status="NOT_RUN" size="sm" />}
                  </div>
                  <p className="text-sm text-gray-400 mt-0.5">{meta.name}</p>
                  <p className="text-xs text-gray-500 mt-1 truncate">{meta.description}</p>
                </div>
              </Link>
            )
          })}
        </div>
      </section>
    </div>
  )
}
