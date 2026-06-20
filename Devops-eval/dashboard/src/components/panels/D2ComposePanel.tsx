// src/components/panels/D2ComposePanel.tsx
import type { D2Report } from '../../types'
import StatusBadge from '../StatusBadge'
import { formatDuration } from '../../data/loadReports'

interface Props { report: D2Report }

const TEST_LABELS = [
  'POST /jobs returns 201',
  'Worker picks up job within 10s',
  'GET /jobs/{id} shows status=processed',
  'Cross-service log line found',
  'Clean teardown (docker-compose down -v)',
]

export default function D2ComposePanel({ report }: Props) {
  const passed = report.tests_passed ?? 0
  const total  = report.tests_total  ?? 5
  const pct    = total > 0 ? Math.round((passed / total) * 100) : 0

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">🐳 D2 — Compose Stack</h2>
          <p className="text-sm text-gray-400 mt-0.5">{report.description}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={report.status} size="lg" />
          <span className="text-xs text-gray-500 font-mono">{formatDuration(report.duration_seconds)}</span>
        </div>
      </div>

      {/* Services */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Services</h3>
        <div className="flex gap-2">
          {(report.services ?? ['api', 'db', 'worker']).map(s => (
            <span key={s} className="px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-300 text-sm font-mono">
              {s}
            </span>
          ))}
        </div>
      </div>

      {/* Test progress */}
      <div>
        <div className="flex justify-between items-center mb-2">
          <h3 className="text-sm font-semibold text-gray-300">Test Results</h3>
          <span className="text-sm font-mono font-bold text-emerald-400">{passed}/{total} passed</span>
        </div>
        <div className="h-2 rounded-full bg-gray-700/60 overflow-hidden mb-3">
          <div className="h-full bg-emerald-500 rounded-full transition-all duration-700" style={{ width: `${pct}%` }} />
        </div>
        <div className="space-y-1.5">
          {TEST_LABELS.map((label, i) => (
            <div key={i} className={`flex items-center gap-2 text-sm px-3 py-2 rounded-lg ${i < passed ? 'bg-emerald-500/10 text-emerald-300' : 'bg-gray-700/30 text-gray-500'}`}>
              <span>{i < passed ? '✅' : '⬜'}</span>
              <span>{label}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Commands */}
      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-300">Quick commands</h3>
        {[
          { label: 'Teardown', cmd: report.teardown_command ?? 'docker-compose down -v' },
          { label: 'Clean re-up', cmd: report.clean_reup_command ?? 'docker-compose down -v && docker-compose up -d --build' },
        ].map(({ label, cmd }) => (
          <div key={label} className="flex items-center gap-3 p-3 rounded-lg bg-gray-800/50 border border-gray-700/40">
            <span className="text-xs text-gray-500 w-16">{label}</span>
            <code className="text-xs font-mono text-cyan-300 truncate">{cmd}</code>
          </div>
        ))}
      </div>
    </div>
  )
}
