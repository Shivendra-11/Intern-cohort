// src/pages/DashboardPage.tsx
import { useEffect, useState, useCallback } from 'react'
import { loadAllReports } from '../data/loadReports'
import type { AnyReport } from '../types'
import Header from '../components/Header'
import ScoreCard from '../components/ScoreCard'
import TaskGrid from '../components/TaskGrid'

export default function DashboardPage() {
  const [reports, setReports] = useState<AnyReport[]>([])
  const [loading, setLoading] = useState(true)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const data = await loadAllReports()
      setReports(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  useEffect(() => {
    const hasRunning = reports.some(r => r.status === 'IN_PROGRESS')
    if (!hasRunning) return
    const id = setInterval(refresh, 30_000)
    return () => clearInterval(id)
  }, [reports, refresh])

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 relative overflow-hidden">
      {/* Subtle ambient background blobs */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 -left-40 w-96 h-96 bg-blue-600/5 rounded-full blur-3xl" />
        <div className="absolute top-1/2 -right-40 w-96 h-96 bg-emerald-600/5 rounded-full blur-3xl" />
        <div className="absolute -bottom-40 left-1/3 w-96 h-96 bg-violet-600/5 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 p-6 max-w-7xl mx-auto">
        <Header reports={reports} onRefresh={refresh} />

        {loading && reports.length === 0 ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center animate-fade-in">
              <div className="w-12 h-12 mx-auto mb-4 rounded-full border-2 border-blue-500/30 border-t-blue-500 animate-spin" />
              <p className="text-gray-400 text-sm">Loading reports…</p>
            </div>
          </div>
        ) : (
          <>
            <ScoreCard reports={reports} />

            {/* Section header */}
            <div className="flex items-center gap-3 mb-4">
              <h2 className="text-sm font-semibold text-gray-300 uppercase tracking-wider">Tasks</h2>
              <div className="flex-1 h-px bg-gray-800" />
              <span className="text-xs text-gray-600 font-mono">D1 – D6</span>
            </div>

            <TaskGrid reports={reports} />
          </>
        )}

        {/* Footer */}
        <footer className="mt-12 pt-6 border-t border-gray-800/40 flex items-center justify-between flex-wrap gap-3 text-xs text-gray-600 font-mono">
          <span>DevOps-Infra Eval Dashboard · reads REPORT.json files live</span>
          <div className="flex items-center gap-4">
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-500/60" />
              {reports.filter(r => r.status === 'PASS').length} pass
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-amber-500/60" />
              {reports.filter(r => r.status === 'WARN').length} warn
            </span>
            <span className="flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500/60" />
              {reports.filter(r => r.status === 'FAIL').length} fail
            </span>
          </div>
        </footer>
      </div>
    </div>
  )
}
