// src/components/ScoreCard.tsx
import type { AnyReport, TaskStatus } from '../types'
import { totalDuration } from '../data/loadReports'

interface Props {
  reports: AnyReport[]
}

function count(reports: AnyReport[], status: TaskStatus) {
  return reports.filter(r => r.status === status).length
}

interface StatChipProps {
  label: string
  value: string | number
  sub?: string
  color: string
  bg: string
  border: string
}

function StatChip({ label, value, sub, color, bg, border }: StatChipProps) {
  return (
    <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${bg} ${border} min-w-[110px]`}>
      <span className={`text-3xl font-bold font-mono ${color}`}>{value}</span>
      {sub && <span className={`text-xs font-mono ${color} opacity-70`}>{sub}</span>}
      <span className="text-xs text-gray-400 mt-1 font-medium uppercase tracking-wide">{label}</span>
    </div>
  )
}

export default function ScoreCard({ reports: reports }: Props) {
  const pass = count(reports, 'PASS')
  const warn = count(reports, 'WARN')
  const fail = count(reports, 'FAIL')
  const notRun = count(reports, 'NOT_RUN')
  const total = reports.length
  const ran = pass + warn + fail

  const scoreColor = fail > 0
    ? 'text-red-400'
    : warn > 0
    ? 'text-amber-400'
    : pass === total
    ? 'text-emerald-400'
    : 'text-gray-400'

  return (
    <div className="mb-8 p-5 rounded-2xl bg-gray-800/40 border border-gray-700/40 backdrop-blur-sm">
      <div className="flex flex-wrap items-center gap-4">
        {/* Big score */}
        <div className="flex flex-col items-center justify-center w-28 h-24 rounded-xl bg-gray-900/60 border border-gray-700/60">
          <span className={`text-4xl font-bold font-mono ${scoreColor}`}>{pass}/{total}</span>
          <span className="text-xs text-gray-400 mt-1 font-medium uppercase tracking-widest">PASS</span>
        </div>

        <div className="flex flex-wrap gap-3">
          <StatChip label="Warn"    value={warn}   color="text-amber-400"   bg="bg-amber-500/10"   border="border-amber-500/20" />
          <StatChip label="Fail"    value={fail}   color="text-red-400"     bg="bg-red-500/10"     border="border-red-500/20"   />
          <StatChip label="Not Run" value={notRun} color="text-gray-400"    bg="bg-gray-700/30"    border="border-gray-600/30"  />
          {ran > 0 && <StatChip label="Total Time" value={totalDuration(reports)} color="text-blue-300" bg="bg-blue-500/10" border="border-blue-500/20" />}
        </div>

        {/* Progress bar */}
        <div className="flex-1 min-w-[200px]">
          <div className="flex justify-between text-xs text-gray-500 mb-1.5 font-mono">
            <span>{ran}/{total} tasks run</span>
            <span>{Math.round((pass/total)*100)}% passing</span>
          </div>
          <div className="h-2.5 bg-gray-700/60 rounded-full overflow-hidden flex">
            <div className="bg-emerald-500 transition-all duration-700" style={{ width: `${(pass/total)*100}%` }} />
            <div className="bg-amber-500 transition-all duration-700" style={{ width: `${(warn/total)*100}%` }} />
            <div className="bg-red-500 transition-all duration-700" style={{ width: `${(fail/total)*100}%` }} />
          </div>
        </div>
      </div>
    </div>
  )
}
