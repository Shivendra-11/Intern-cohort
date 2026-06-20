// src/components/panels/D4KubernetesPanel.tsx
import type { D4Report } from '../../types'
import StatusBadge from '../StatusBadge'
import { formatDuration } from '../../data/loadReports'

interface Props { report: D4Report }

function ExitBadge({ code, label }: { code: number; label: string }) {
  const ok = code === 0
  return (
    <div className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm ${ok ? 'bg-emerald-500/10 border border-emerald-500/20 text-emerald-300' : 'bg-red-500/10 border border-red-500/20 text-red-300'}`}>
      <span>{ok ? '✅' : '❌'}</span>
      <span className="font-mono text-xs">{label}</span>
      <span className="ml-auto text-xs opacity-60 font-mono">exit {code}</span>
    </div>
  )
}

export default function D4KubernetesPanel({ report }: Props) {
  const manifests = report.manifest_files ?? ['deployment.yaml', 'service.yaml', 'configmap.yaml', 'ingress.yaml']
  const replicas = report.replicas_ready ?? 0

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">☸️ D4 — Kubernetes</h2>
          <p className="text-sm text-gray-400 mt-0.5">{report.description}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={report.status} size="lg" />
          <span className="text-xs text-gray-500 font-mono">{formatDuration(report.duration_seconds)}</span>
        </div>
      </div>

      {/* Cluster info */}
      <div className="grid grid-cols-2 gap-3">
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/40">
          <span className="text-xs text-gray-500">Cluster</span>
          <p className="text-sm font-mono text-gray-200 mt-0.5">{report.cluster_tool ?? 'kind'} — devops-eval</p>
        </div>
        <div className="p-3 rounded-lg bg-gray-800/50 border border-gray-700/40">
          <span className="text-xs text-gray-500">Namespace</span>
          <p className="text-sm font-mono text-gray-200 mt-0.5">{report.namespace ?? 'devops-eval'}</p>
        </div>
      </div>

      {/* Exit codes */}
      <div className="space-y-2">
        <ExitBadge code={report.dry_run_exit_code ?? 0} label="kubectl apply --dry-run=client" />
        <ExitBadge code={report.apply_exit_code ?? 0} label="kubectl apply -f manifests/" />
      </div>

      {/* Replica gauge */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Replica readiness</h3>
        <div className="flex items-center gap-3">
          <div className="flex gap-2">
            {[0, 1].map(i => (
              <div key={i} className={`w-10 h-10 rounded-full flex items-center justify-center border-2 text-sm font-bold ${i < replicas ? 'border-emerald-500 bg-emerald-500/20 text-emerald-300' : 'border-gray-600 bg-gray-700/30 text-gray-500'}`}>
                {i < replicas ? '✓' : '○'}
              </div>
            ))}
          </div>
          <span className="text-sm font-mono text-gray-300">{replicas}/2 pods ready</span>
        </div>
      </div>

      {/* Curl proof */}
      {report.curl_status_code && (
        <div className="p-3 rounded-lg bg-gray-900/60 border border-gray-700/40">
          <div className="flex items-center gap-2 mb-2">
            <span className="text-xs text-gray-500">curl proof</span>
            <span className={`text-xs font-mono px-2 py-0.5 rounded ${report.curl_status_code === 200 ? 'bg-emerald-500/20 text-emerald-300' : 'bg-red-500/20 text-red-300'}`}>
              HTTP {report.curl_status_code}
            </span>
          </div>
          <code className="text-xs font-mono text-gray-300">{report.curl_response_excerpt ?? 'Welcome to nginx!'}</code>
        </div>
      )}

      {/* Manifests */}
      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Manifest files</h3>
        <div className="flex flex-wrap gap-2">
          {manifests.map(m => (
            <span key={m} className="px-2 py-1 rounded bg-gray-700/50 text-gray-300 text-xs font-mono border border-gray-600/30">
              {m}
            </span>
          ))}
        </div>
      </div>
    </div>
  )
}
