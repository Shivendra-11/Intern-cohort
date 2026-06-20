// src/components/panels/D3CiPanel.tsx
import type { D3Report } from '../../types'
import StatusBadge from '../StatusBadge'
import { formatDuration } from '../../data/loadReports'

interface Props { report: D3Report }

export default function D3CiPanel({ report }: Props) {
  const stages = report.stages ?? ['lint', 'test', 'build-image']
  const matrix = report.matrix ?? ['3.11', '3.12']

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">⚙️ D3 — CI Pipeline</h2>
          <p className="text-sm text-gray-400 mt-0.5">{report.description}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={report.status} size="lg" />
          <span className="text-xs text-gray-500 font-mono">{formatDuration(report.duration_seconds)}</span>
        </div>
      </div>

      {/* Pipeline diagram */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-3">Pipeline stages</h3>
        <div className="flex items-center gap-1">
          {stages.map((stage, i) => (
            <div key={stage} className="flex items-center gap-1">
              <div className={`px-4 py-2 rounded-lg text-sm font-mono font-medium ${report.status === 'PASS' ? 'bg-emerald-500/15 text-emerald-300 border border-emerald-500/30' : 'bg-gray-700/50 text-gray-300 border border-gray-600/40'}`}>
                ✅ {stage}
              </div>
              {i < stages.length - 1 && <span className="text-gray-600 text-lg">→</span>}
            </div>
          ))}
        </div>
      </div>

      {/* Matrix */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Test matrix</h3>
        <div className="flex gap-2">
          {matrix.map(ver => (
            <span key={ver} className="px-3 py-1.5 rounded-lg bg-purple-500/10 border border-purple-500/20 text-purple-300 text-sm font-mono">
              Python {ver} ✅
            </span>
          ))}
        </div>
      </div>

      {/* Cache */}
      <div className={`flex items-center gap-3 px-4 py-3 rounded-lg border ${report.cache_configured ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-300' : 'bg-gray-700/30 border-gray-600/40 text-gray-400'}`}>
        <span>{report.cache_configured ? '✅' : '⬜'}</span>
        <span className="text-sm font-medium">pip cache configured (actions/cache)</span>
      </div>

      {/* Failure demo */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Failure demo</h3>
        <div className="p-3 rounded-lg bg-red-500/10 border border-red-500/20">
          <div className="flex items-center gap-2 text-sm text-red-300">
            <span>❌</span>
            <span className="font-mono">lint FAILED — ruff found syntax error in bad.py</span>
          </div>
          <div className="flex items-center gap-2 text-xs text-gray-400 mt-1.5">
            <span className="text-emerald-400">Exit code: 1 ✓ (expected failure)</span>
          </div>
        </div>
      </div>

      {/* Tool */}
      <div className="text-xs text-gray-500 font-mono p-2 rounded bg-gray-800/40 border border-gray-700/30">
        Pipeline tool: {report.pipeline_tool ?? 'GitHub Actions (act local runner)'}
      </div>
    </div>
  )
}
