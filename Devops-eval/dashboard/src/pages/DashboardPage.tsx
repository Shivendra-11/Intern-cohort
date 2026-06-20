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

  // Auto-refresh every 30s while any task is IN_PROGRESS
  useEffect(() => {
    const hasRunning = reports.some(r => r.status === 'IN_PROGRESS')
    if (!hasRunning) return
    const id = setInterval(refresh, 30_000)
    return () => clearInterval(id)
  }, [reports, refresh])

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 max-w-7xl mx-auto">
      <Header reports={reports} onRefresh={refresh} />

      {loading && reports.length === 0 ? (
        <div className="flex items-center justify-center h-64">
          <div className="text-center">
            <div className="text-4xl mb-4 animate-spin">⚙️</div>
            <p className="text-gray-400">Loading reports...</p>
          </div>
        </div>
      ) : (
        <>
          <ScoreCard reports={reports} />
          <TaskGrid reports={reports} />
        </>
      )}

      {/* Footer */}
      <footer className="mt-12 pt-6 border-t border-gray-800/60 text-center text-xs text-gray-600 font-mono">
        DevOps-Infra Eval Dashboard · reads REPORT.json files live ·{' '}
        <a
          href="https://github.com"
          className="text-gray-500 hover:text-gray-300 transition-colors"
          target="_blank"
          rel="noopener noreferrer"
        >
          /devopsinfra-eval
        </a>
      </footer>
    </div>
  )
}
