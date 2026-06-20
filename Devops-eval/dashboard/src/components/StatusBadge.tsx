// src/components/StatusBadge.tsx
import type { TaskStatus } from '../types'

interface Props {
  status: TaskStatus
  size?: 'sm' | 'md' | 'lg'
}

const CONFIG: Record<TaskStatus, { emoji: string; label: string; classes: string }> = {
  PASS:        { emoji: '✅', label: 'PASS',     classes: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/40' },
  WARN:        { emoji: '⚠️', label: 'WARN',     classes: 'bg-amber-500/20  text-amber-400  border-amber-500/40'  },
  FAIL:        { emoji: '❌', label: 'FAIL',     classes: 'bg-red-500/20    text-red-400    border-red-500/40'    },
  NOT_RUN:     { emoji: '⬜', label: 'NOT RUN',  classes: 'bg-gray-700/40   text-gray-400   border-gray-600/40'   },
  IN_PROGRESS: { emoji: '⏳', label: 'RUNNING',  classes: 'bg-blue-500/20   text-blue-400   border-blue-500/40 animate-pulse'  },
}

const SIZE: Record<string, string> = {
  sm: 'text-xs px-2 py-0.5',
  md: 'text-sm px-3 py-1',
  lg: 'text-base px-4 py-1.5 font-semibold',
}

export default function StatusBadge({ status, size = 'md' }: Props) {
  const { emoji, label, classes } = CONFIG[status] ?? CONFIG['NOT_RUN']
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full border font-mono font-medium ${SIZE[size]} ${classes}`}>
      <span>{emoji}</span>
      <span>{label}</span>
    </span>
  )
}
