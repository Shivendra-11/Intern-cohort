// src/components/panels/D6ObsPanel.tsx
import type { D6Report } from '../../types'
import StatusBadge from '../StatusBadge'
import { formatDuration } from '../../data/loadReports'

interface Props { report: D6Report }

function EndpointRow({ label, value }: { label: string; value?: string }) {
  if (!value) return null
  return (
    <div className="flex items-center gap-2 px-3 py-2 rounded-lg bg-gray-800/50 border border-gray-700/40 text-sm">
      <span className="font-medium text-gray-300">{label}</span>
      <span className="text-xs font-mono text-gray-500 ml-auto truncate">{value}</span>
    </div>
  )
}

export default function D6ObsPanel({ report }: Props) {
  const panels = report.dashboard_panels ?? ['Requests per second', 'p95 Latency (ms)']

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-white">📊 D6 — Observability</h2>
          <p className="text-sm text-gray-400 mt-0.5">{report.description}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          <StatusBadge status={report.status} size="lg" />
          <span className="text-xs text-gray-500 font-mono">{formatDuration(report.duration_seconds)}</span>
        </div>
      </div>

      <div className="space-y-2">
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Endpoints (from eval run)</h3>
        <EndpointRow label="Metrics" value={report.metrics_endpoint} />
        <EndpointRow label="Prometheus" value={report.prometheus_url} />
        <EndpointRow label="Grafana" value={report.grafana_url} />
      </div>

      <div>
        <h3 className="text-sm font-semibold text-gray-300 mb-2">Grafana dashboard panels</h3>
        <div className="space-y-2">
          {panels.map(panel => (
            <div key={panel} className="flex items-center gap-3 px-4 py-3 rounded-lg bg-orange-500/10 border border-orange-500/20">
              <span className="text-xl">📈</span>
              <div>
                <p className="text-sm font-medium text-orange-200">{panel}</p>
                {panel.toLowerCase().includes('request') && (
                  <code className="text-xs font-mono text-gray-400">rate(http_requests_total[1m])</code>
                )}
                {panel.toLowerCase().includes('latency') && (
                  <code className="text-xs font-mono text-gray-400">histogram_quantile(0.95, ...)</code>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>

      <div className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/20">
        <h3 className="text-sm font-semibold text-gray-300 mb-1">Load test</h3>
        <p className="text-xs text-gray-400">50 req/s × 30s = <span className="text-purple-300 font-mono">1,500 total requests</span></p>
        <code className="text-xs text-gray-500 font-mono mt-1 block">{report.load_script ?? 'd6-observability/load.sh'}</code>
      </div>

      <div className="flex items-center gap-2 text-sm">
        <span className="text-gray-400">Log format:</span>
        <span className="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300 border border-cyan-500/20 font-mono text-xs">
          {report.log_format ?? 'JSON structured (structlog)'}
        </span>
      </div>

      {report.screenshot && (
        <div className="p-4 rounded-lg bg-gray-800/40 border border-gray-700/40 border-dashed text-center">
          <span className="text-2xl">🖼️</span>
          <p className="text-xs text-gray-500 mt-1">Screenshot: {report.screenshot}</p>
        </div>
      )}
    </div>
  )
}
