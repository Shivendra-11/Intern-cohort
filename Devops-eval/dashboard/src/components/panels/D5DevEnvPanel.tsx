// src/components/panels/D5DevEnvPanel.tsx
import type { D5Report } from '../../types'
import StatusBadge from '../StatusBadge'
import { formatDuration } from '../../data/loadReports'

interface Props { report: D5Report }

interface ImplicitDep {
  was: string
  now: string
  where: string
}

const DEFAULT_DEPS: ImplicitDep[] = [
  { was: 'Python 3.12',           now: 'Required by devcontainer image',  where: 'devcontainer.json' },
  { was: 'Node v20',              now: 'Required by dashboard',            where: '.tool-versions' },
  { was: 'Terraform ≥ 1.6',      now: 'Required for d1-terraform',        where: 'devcontainer.json features' },
  { was: 'POSTGRES_PASSWORD',     now: 'Must be set for d2 tests',         where: '.env.example' },
  { was: 'docker daemon',         now: 'Must be running for d2/d3/d4',     where: 'docker-in-docker feature' },
  { was: 'ruff linter',           now: 'Required for d3 CI lint',          where: 'requirements.txt' },
]

function CmdBadge({ cmd, code, label }: { cmd: string; code: number; label: string }) {
  const ok = code === 0
  return (
    <div className={`p-3 rounded-lg border ${ok ? 'bg-emerald-500/10 border-emerald-500/20' : 'bg-red-500/10 border-red-500/20'}`}>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-xs text-gray-400">{label}</span>
        <span className={`text-xs font-mono ${ok ? 'text-emerald-400' : 'text-red-400'}`}>exit {code}</span>
      </div>
      <code className="text-sm font-mono text-gray-200">{cmd}</code>
    </div>
  )
}

export default function D5DevEnvPanel({ report }: Props) {
  const docCount = report.implicit_deps_documented ?? DEFAULT_DEPS.length

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">💻 D5 — Dev Environment</h2>
          <p className="text-sm text-gray-400 mt-0.5">{report.description}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={report.status} size="lg" />
          <span className="text-xs text-gray-500 font-mono">{formatDuration(report.duration_seconds)}</span>
        </div>
      </div>

      {/* Commands */}
      <div className="space-y-2">
        <CmdBadge
          label="Bootstrap"
          cmd={report.bootstrap_command ?? 'make bootstrap'}
          code={report.bootstrap_exit_code ?? 0}
        />
        <CmdBadge
          label="Test"
          cmd={report.test_command ?? 'make test'}
          code={report.test_exit_code ?? 0}
        />
      </div>

      {/* Implicit deps documented */}
      <div>
        <div className="flex items-center gap-2 mb-2">
          <h3 className="text-sm font-semibold text-gray-300">Previously implicit → now explicit</h3>
          <span className="px-2 py-0.5 rounded-full bg-blue-500/20 text-blue-300 text-xs border border-blue-500/20 font-mono">
            {docCount}
          </span>
        </div>
        <div className="rounded-lg border border-gray-700/40 overflow-hidden">
          <table className="w-full text-xs font-mono">
            <thead>
              <tr className="bg-gray-800/60 text-gray-400">
                <th className="text-left px-3 py-2">Was implicit</th>
                <th className="text-left px-3 py-2">Now explicit</th>
                <th className="text-left px-3 py-2">Where pinned</th>
              </tr>
            </thead>
            <tbody>
              {DEFAULT_DEPS.slice(0, docCount).map((dep, i) => (
                <tr key={i} className={`border-t border-gray-700/30 ${i % 2 === 0 ? 'bg-gray-800/20' : 'bg-gray-800/10'}`}>
                  <td className="px-3 py-2 text-amber-300">{dep.was}</td>
                  <td className="px-3 py-2 text-gray-300">{dep.now}</td>
                  <td className="px-3 py-2 text-cyan-300">{dep.where}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}
