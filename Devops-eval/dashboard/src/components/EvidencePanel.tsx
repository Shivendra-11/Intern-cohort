// src/components/EvidencePanel.tsx
import { useState } from 'react'

interface Props {
  title: string
  content: string
  defaultOpen?: boolean
}

export default function EvidencePanel({ title, content, defaultOpen = false }: Props) {
  const [open, setOpen] = useState(defaultOpen)

  const highlighted = content
    .split('\n')
    .map((line, i) => {
      let cls = 'text-gray-300'
      if (/PASS|SUCCESS|✓|passed|exit 0|validate.*valid/i.test(line)) cls = 'text-emerald-400'
      else if (/FAIL|ERROR|error|failed|exit [^0]/i.test(line)) cls = 'text-red-400'
      else if (/WARN|warning|skipped/i.test(line)) cls = 'text-amber-400'
      else if (/^#|^===/i.test(line)) cls = 'text-blue-300 font-semibold'
      return <span key={i} className={cls}>{line}{'\n'}</span>
    })

  return (
    <div className="rounded-lg border border-gray-700/60 overflow-hidden">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center justify-between px-4 py-3 bg-gray-800/60 hover:bg-gray-800 transition-colors text-left"
      >
        <span className="text-sm font-mono font-medium text-gray-300">{title}</span>
        <span className="text-gray-500 text-lg">{open ? '▲' : '▼'}</span>
      </button>
      {open && (
        <div className="bg-gray-950/80 p-4 overflow-x-auto">
          <pre className="text-xs font-mono leading-5 whitespace-pre-wrap break-words max-h-80 overflow-y-auto">
            {highlighted}
          </pre>
        </div>
      )}
    </div>
  )
}
