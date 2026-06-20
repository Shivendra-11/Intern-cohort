// src/components/panels/D1TerraformPanel.tsx
import type { D1Report } from '../../types'
import StatusBadge from '../StatusBadge'
import EvidencePanel from '../EvidencePanel'
import { formatDuration } from '../../data/loadReports'

interface Props { report: D1Report }

function ExitCodeBadge({ code, label }: { code: number; label: string }) {
  const ok = code === 0
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-mono ${ok ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300' : 'bg-red-500/10 border border-red-500/20 text-red-300'}`}>
      <span>{ok ? '✅' : '❌'}</span>
      <span>{label}</span>
      <span className="ml-auto text-xs opacity-70">exit {code}</span>
    </div>
  )
}

export default function D1TerraformPanel({ report }: Props) {
  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">🏗️ D1 — Terraform Plan</h2>
          <p className="text-sm text-gray-400 mt-0.5">{report.description}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={report.status} size="lg" />
          <span className="text-xs text-gray-500 font-mono">{formatDuration(report.duration_seconds)}</span>
        </div>
      </div>

      {/* Exit codes */}
      <div className="grid grid-cols-2 gap-3">
        <ExitCodeBadge code={report.validate_exit_code ?? 0} label="terraform validate" />
        <ExitCodeBadge code={report.plan_exit_code ?? 0} label="terraform plan" />
      </div>

      {/* Resources */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2 flex items-center gap-2">
          Resources planned
          <span className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs border border-blue-500/20 font-mono">
            {report.resource_count ?? (report.resources?.length ?? 0)}
          </span>
        </h3>
        <div className="flex flex-wrap gap-2">
          {(report.resources ?? []).map(res => (
            <span key={res} className="px-2 py-1 rounded bg-gray-700/50 text-gray-300 text-xs font-mono border border-gray-600/30">
              {res}
            </span>
          ))}
        </div>
      </div>

      {/* Plan excerpt */}
      {report.proof_excerpt && (
        <div className="p-3 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
          <p className="text-xs text-gray-400 mb-1">Plan summary</p>
          <code className="text-sm text-emerald-300 font-mono">{report.proof_excerpt}</code>
        </div>
      )}

      {/* Artifacts */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Artifacts</h3>
        <div className="flex flex-wrap gap-2">
          {(report.artifacts ?? []).map(a => (
            <span key={a} className="px-2 py-1 rounded text-xs font-mono text-cyan-300 bg-cyan-500/10 border border-cyan-500/20">
              {a.split('/').pop()}
            </span>
          ))}
        </div>
      </div>

      {/* Evidence */}
      <EvidencePanel title="📋 Proof (validate + plan output)" content={report.proof_excerpt ?? 'No proof captured yet.'} />
    </div>
  )
}
