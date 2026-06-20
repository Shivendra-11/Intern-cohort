// src/components/TaskGrid.tsx
import type { AnyReport, TaskId } from '../types'
import TaskCard from './TaskCard'

const TASK_IDS: TaskId[] = ['D1', 'D2', 'D3', 'D4', 'D5', 'D6']

interface Props {
  reports: AnyReport[]
}

export default function TaskGrid({ reports }: Props) {
  const byTask = Object.fromEntries(reports.map(r => [r.task, r]))

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
      {TASK_IDS.map((taskId, i) => (
        <TaskCard key={taskId} taskId={taskId} report={byTask[taskId] ?? null} index={i} />
      ))}
    </div>
  )
}
