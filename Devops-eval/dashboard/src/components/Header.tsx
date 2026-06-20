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

  const pass    = reports.filter(r => r.status === 'PASS').length
  const fail    = reports.filter(r => r.status === 'FAIL').length
  const warn    = reports.filter(r => r.status === 'WARN').length
  const total   = reports.length
  const allPass = pass === total && total > 0

  const scorePct = total > 0 ? Math.round((pass / total) * 100) : 0

  const linkClass =
    'flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-all duration-200 hover:scale-105 active:scale-95'

  return (
    <header className="mb-8 animate-fade-in">
      {/* Hero gradient band */}
      <div className="relative rounded-2xl overflow-hidden mb-5">
        <div className="absolute inset-0 bg-gradient-to-br from-slate-900 via-gray-900 to-slate-900" />
        <div className="absolute inset-0 bg-gradient-to-r from-blue-600/10 via-transparent to-emerald-600/10" />
        <div className="absolute top-0 left-0 right-0 h-px bg-gradient-to-r from-transparent via-blue-500/40 to-transparent" />

        <div className="relative px-6 py-5 flex items-start justify-between flex-wrap gap-4">
          {/* Left: title + meta */}
          <div>
            <div className="flex items-center gap-3 mb-1.5">
              <div className="w-10 h-10 rounded-xl bg-blue-500/20 border border-blue-500/30 flex items-center justify-center text-xl">
                🚀
              </div>
              <div>
                <h1 className="text-2xl font-bold text-white tracking-tight leading-none">
                  DevOps-Infra Eval
                </h1>
                <p className="text-xs text-gray-400 font-mono mt-0.5">
                  Infrastructure evaluation · D1–D6
                </p>
              </div>
              <span className="px-2 py-0.5 rounded-md text-xs font-mono bg-blue-500/15 text-blue-300 border border-blue-500/25 ml-1">
                v1.0
              </span>
            </div>

            <div className="flex items-center gap-4 mt-3 text-xs text-gray-400 font-mono flex-wrap">
              {/* Live indicator */}
              <span className="flex items-center gap-1.5">
                <span className={`w-1.5 h-1.5 rounded-full ${allPass ? 'bg-emerald-400 animate-pulse' : 'bg-amber-400 animate-pulse'}`} />
                <span className={allPass ? 'text-emerald-400' : 'text-amber-400'}>
                  {allPass ? 'All systems green' : `${fail > 0 ? fail + ' failing' : warn + ' warning'}`}
                </span>
              </span>
              <span className="text-gray-600">|</span>
              <span>Last run: <span className="text-gray-300">{formatted}</span></span>
              {reports.some(r => r.duration_seconds > 0) && (
                <>
                  <span className="text-gray-600">|</span>
                  <span>Total time: <span className="text-gray-300">{totalDuration(reports)}</span></span>
                </>
              )}
            </div>
          </div>

          {/* Right: score pill + actions */}
          <div className="flex items-center gap-3 flex-wrap">
            {/* Score pill */}
            {total > 0 && (
              <div className={`flex items-center gap-2 px-4 py-2 rounded-xl border text-sm font-bold font-mono
                ${allPass
                  ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-300'
                  : fail > 0
                  ? 'bg-red-500/15 border-red-500/30 text-red-300'
                  : 'bg-amber-500/15 border-amber-500/30 text-amber-300'
                }`}>
                <span className={`w-2 h-2 rounded-full ${allPass ? 'bg-emerald-400' : fail > 0 ? 'bg-red-400' : 'bg-amber-400'}`} />
                {pass}/{total} PASS · {scorePct}%
              </div>
            )}

            <Link
              to="/hub"
              className={`${linkClass} bg-violet-600/15 hover:bg-violet-600/25 border border-violet-500/25 text-violet-300 hover:text-violet-200`}
            >
              📋 All tasks
            </Link>
            <button
              onClick={onRefresh}
              className={`${linkClass} bg-gray-700/50 hover:bg-gray-700/80 border border-gray-600/40 text-gray-300 hover:text-white`}
              title="Refresh report data"
            >
              🔄 Refresh
            </button>
          </div>
        </div>
      </div>

      {/* Command bar */}
      <div className="p-3 rounded-xl bg-gray-900/60 border border-gray-800/60 flex items-center gap-3 flex-wrap">
        <span className="text-gray-500 text-xs font-mono">Run:</span>
        <code className="text-xs font-mono text-cyan-400">/devopsinfra-eval --task all --mode build+verify</code>
        <span className="ml-auto text-xs text-gray-600 font-mono hidden sm:block">reads REPORT.json live</span>
      </div>
    </header>
  )
}
