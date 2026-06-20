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

export default function DetailPage() {
  const { taskId } = useParams<{ taskId: string }>()
  const navigate = useNavigate()
  const [report, setReport] = useState<AnyReport | null>(null)
  const [loading, setLoading] = useState(true)

  const id = (taskId?.toUpperCase() as TaskId) ?? 'D1'
  const meta = TASK_META[id]

  useEffect(() => {
    if (!TASK_IDS.includes(id)) { navigate('/'); return }
    setLoading(true)
    loadReport(id).then(r => { setReport(r); setLoading(false) })
  }, [id, navigate])

  const idx = TASK_IDS.indexOf(id)
  const prev = idx > 0 ? TASK_IDS[idx - 1] : null
  const next = idx < TASK_IDS.length - 1 ? TASK_IDS[idx + 1] : null

  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-6 max-w-4xl mx-auto">
      {/* Breadcrumb nav */}
      <nav className="flex items-center gap-2 mb-6 text-sm">
        <button
          onClick={() => navigate('/')}
          className="text-gray-400 hover:text-white transition-colors flex items-center gap-1"
        >
          ← Dashboard
        </button>
        <span className="text-gray-700">/</span>
        <span className="text-gray-300 font-mono font-medium">{id}</span>
        {meta && <span className="text-gray-500">— {meta.name}</span>}
      </nav>

      {/* Task nav pills */}
      <div className="flex gap-1 mb-6 flex-wrap">
        {TASK_IDS.map(tid => (
          <button
            key={tid}
            onClick={() => navigate(`/task/${tid}`)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono font-medium transition-colors ${
              tid === id
                ? 'bg-blue-500/20 text-blue-300 border border-blue-500/30'
                : 'text-gray-500 hover:text-gray-300 hover:bg-gray-800/50'
            }`}
          >
            {tid}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="p-6 rounded-2xl bg-gray-800/40 border border-gray-700/40 backdrop-blur-sm">
        {loading ? (
          <div className="flex items-center justify-center h-64">
            <div className="text-center">
              <div className="text-3xl animate-spin mb-3">⚙️</div>
              <p className="text-gray-400 text-sm">Loading {id}...</p>
            </div>
          </div>
        ) : report ? (
          renderPanel(report)
        ) : (
          <div className="text-center py-16">
            <div className="text-4xl mb-4">⬜</div>
            <h3 className="text-xl font-semibold text-gray-300 mb-2">Task not run yet</h3>
            <p className="text-gray-500 text-sm mb-6">
              Run <code className="font-mono text-cyan-400">/devopsinfra-eval --task {id} --mode build+verify</code>
            </p>
            <StatusBadge status="NOT_RUN" size="lg" />
          </div>
        )}
      </div>

      {/* Prev / Next */}
      <div className="flex justify-between mt-6">
        <button
          onClick={() => prev && navigate(`/task/${prev}`)}
          disabled={!prev}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/60 border border-gray-700/40 text-gray-400 hover:text-white text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed"
        >
          ← {prev ? `${prev} ${TASK_META[prev].name}` : ''}
        </button>
        <button
          onClick={() => next && navigate(`/task/${next}`)}
          disabled={!next}
          className="flex items-center gap-2 px-4 py-2 rounded-lg bg-gray-800/50 hover:bg-gray-700/60 border border-gray-700/40 text-gray-400 hover:text-white text-sm transition-all disabled:opacity-30 disabled:cursor-not-allowed"
        >
          {next ? `${next} ${TASK_META[next].name}` : ''} →
        </button>
      </div>
    </div>
  )
}
