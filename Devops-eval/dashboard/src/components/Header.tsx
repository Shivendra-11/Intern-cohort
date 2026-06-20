import { Link } from 'react-router-dom'
import type { AnyReport } from '../types'
import { totalDuration } from '../data/loadReports'

interface Props {
  reports: AnyReport[]
  onRefresh: () => void
}

export default function Header({ reports, onRefresh }: Props) {
  const latestTimestamp = reports
    .filter(r => r.timestamp)
    .sort((a, b) => b.timestamp.localeCompare(a.timestamp))[0]?.timestamp

  const formatted = latestTimestamp
    ? new Date(latestTimestamp).toLocaleString('en-US', {
        month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', timeZoneName: 'short'
      })
    : 'No runs yet'

  const linkClass =
    'flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all hover:scale-105'

  return (
    <header className="mb-8">
      <div className="flex items-start justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center gap-3 mb-1">
            <span className="text-3xl">🚀</span>
            <h1 className="text-3xl font-bold text-white tracking-tight">DevOps-Infra Eval</h1>
            <span className="px-2 py-0.5 rounded text-xs font-mono bg-blue-500/20 text-blue-300 border border-blue-500/30">
              v1.0
            </span>
          </div>
          <p className="text-gray-400 text-sm ml-12">
            Last run: <span className="text-gray-300 font-mono">{formatted}</span>
            {reports.some(r => r.duration_seconds > 0) && (
              <span className="ml-4 text-gray-500">
                Total time: <span className="text-gray-300">{totalDuration(reports)}</span>
              </span>
            )}
          </p>
        </div>

        <div className="flex items-center gap-3 flex-wrap">
          <Link
            to="/hub"
            className={`${linkClass} bg-violet-600/20 hover:bg-violet-600/30 border border-violet-500/30 text-violet-300 hover:text-violet-200`}
          >
            📋 All tasks
          </Link>
          <button
            onClick={onRefresh}
            className={`${linkClass} bg-gray-700/60 hover:bg-gray-700 border border-gray-600/40 text-gray-300 hover:text-white`}
            title="Refresh report data"
          >
            🔄 Refresh
          </button>
        </div>
      </div>

      <div className="mt-4 p-3 rounded-lg bg-gray-800/40 border border-gray-700/40 flex items-center gap-3 flex-wrap">
        <span className="text-gray-500 text-xs font-mono">Run:</span>
        <code className="text-xs font-mono text-cyan-400">/devopsinfra-eval --task all --mode build+verify</code>
      </div>
    </header>
  )
}
