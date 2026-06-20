// src/pages/DetailPage.tsx
import { useEffect, useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { loadReport } from '../data/loadReports'
import type { AnyReport, TaskId } from '../types'
import { TASK_META } from '../types'
import StatusBadge from '../components/StatusBadge'
import D1TerraformPanel from '../components/panels/D1TerraformPanel'
import D2ComposePanel   from '../components/panels/D2ComposePanel'
import D3CiPanel        from '../components/panels/D3CiPanel'
import D4KubernetesPanel from '../components/panels/D4KubernetesPanel'
import D5DevEnvPanel    from '../components/panels/D5DevEnvPanel'
import D6ObsPanel       from '../components/panels/D6ObsPanel'

const TASK_IDS: TaskId[] = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

function renderPanel(report: AnyReport) {
  switch (report.task) {
    case 'D1': return <D1TerraformPanel  report={report as any} />
    case 'D2': return <D2ComposePanel    report={report as any} />
    case 'D3': return <D3CiPanel         report={report as any} />
    case 'D4': return <D4KubernetesPanel report={report as any} />
    case 'D5': return <D5DevEnvPanel     report={report as any} />
    case 'D6': return <D6ObsPanel        report={report as any} />
    default:   return <div className="text-gray-400">Unknown task</div>
  }
}

const STATUS_ACCENT: Record<string, string> = {
  PASS:        'from-emerald-500/15 to-transparent border-emerald-700/30',
  WARN:        'from-amber-500/10 to-transparent border-amber-700/30',
  FAIL:        'from-red-500/10 to-transparent border-red-700/30',
  NOT_RUN:     'from-gray-700/10 to-transparent border-gray-700/30',
  IN_PROGRESS: 'from-blue-500/10 to-transparent border-blue-700/30',
}

export default function DetailPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<AnyReport | null>(null)
  const [loading, setLoading] = useState(true)

  const id   = (taskId?.toUpperCase() as TaskId) ?? 'D1'
  const meta = TASK_META[id]

  useEffect(() => {
    if (!TASK_IDS.includes(id)) { navigate('/'); return }
    setLoading(true)
    loadReport(id).then(r => { setReport(r); setLoading(false) })
  }, [id, navigate])

  const idx  = TASK_IDS.indexOf(id)
  const prev = idx > 0 ? TASK_IDS[idx - 1] : null
  const next = idx < TASK_IDS.length - 1 ? TASK_IDS[idx + 1] : null
  const status = report?.status ?? 'NOT_RUN'
  const accent = STATUS_ACCENT[status] ?? STATUS_ACCENT['NOT_RUN']

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 relative overflow-hidden">
      {/* Ambient blob */}
      <div className="pointer-events-none fixed inset-0 z-0 overflow-hidden">
        <div className="absolute -top-40 left-1/4 w-96 h-96 bg-blue-600/4 rounded-full blur-3xl" />
      </div>

      <div className="relative z-10 p-6 max-w-4xl mx-auto">
        {/* Breadcrumb */}
        <nav className="flex items-center gap-2 mb-5 text-sm animate-fade-in">
          <button
            onClick={() => navigate('/')}
            className="text-gray-400 hover:text-white transition-colors flex items-center gap-1 hover:gap-2 duration-200"
          >
            ← Dashboard
          </button>
          <span className="text-gray-700">/</span>
          <span className="text-gray-300 font-mono font-medium">{id}</span>
          {meta && <span className="text-gray-500">— {meta.name}</span>}
        </nav>

        {/* Task nav pills */}
        <div className="flex gap-1.5 mb-6 flex-wrap animate-fade-in">
          {TASK_IDS.map(tid => (
            <button
              key={tid}
              onClick={() => navigate(`/task/${tid}`)}
              className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-all duration-200 ${
                tid === id
                  ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30 scale-105'
                  : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/60 border border-transparent'
              }`}
            >
              {tid}
            </button>
          ))}
        </div>

        {/* Content card */}
        <div className={`rounded-2xl border bg-gradient-to-br ${accent} bg-gray-900/70 backdrop-blur-sm animate-scale-in`}>
          {/* Top bar */}
          {!loading && report && report.status !== 'NOT_RUN' && (
            <div className="px-6 pt-5 pb-0 flex items-center gap-3 mb-2">
              <span className="text-2xl">{meta?.icon}</span>
              <div className="flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <span className="font-mono font-bold text-white text-sm">{id}</span>
                  <StatusBadge status={status} size="md" />
                </div>
              </div>
            </div>
          )}

          <div className="p-6">
            {loading ? (
              <div className="flex items-center justify-center h-64">
                <div className="text-center animate-fade-in">
                  <div className="w-10 h-10 mx-auto mb-3 rounded-full border-2 border-blue-500/30 border-t-blue-500 animate-spin" />
                  <p className="text-gray-400 text-sm">Loading {id}…</p>
                </div>
              </div>
            ) : report ? (
              renderPanel(report)
            ) : (
              <div className="text-center py-16">
                <div className="text-5xl mb-4">⬜</div>
                <h3 className="text-xl font-semibold text-gray-300 mb-2">Task not run yet</h3>
                <p className="text-gray-500 text-sm mb-6">
                  Run <code className="font-mono text-cyan-400">/devopsinfra-eval --task {id} --mode build+verify</code>
                </p>
                <StatusBadge status="NOT_RUN" size="lg" />
              </div>
            )}
          </div>
        </div>

        {/* Prev / Next */}
        <div className="flex justify-between mt-6 animate-fade-in">
          <button
            onClick={() => prev && navigate(`/task/${prev}`)}
            disabled={!prev}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gray-800/50 hover:bg-gray-700/60
              border border-gray-700/40 text-gray-400 hover:text-white text-sm transition-all duration-200
              hover:-translate-x-0.5 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:translate-x-0"
          >
            ← {prev ? `${prev} · ${TASK_META[prev].name}` : ''}
          </button>
          <button
            onClick={() => next && navigate(`/task/${next}`)}
            disabled={!next}
            className="flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gray-800/50 hover:bg-gray-700/60
              border border-gray-700/40 text-gray-400 hover:text-white text-sm transition-all duration-200
              hover:translate-x-0.5 disabled:opacity-30 disabled:cursor-not-allowed disabled:hover:translate-x-0"
          >
            {next ? `${next} · ${TASK_META[next].name}` : ''} →
          </button>
        </div>
      </div>
    </div>
  )
}
