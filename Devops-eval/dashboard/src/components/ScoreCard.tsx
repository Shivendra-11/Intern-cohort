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
    <div className={`flex flex-col items-center justify-center p-4 rounded-xl border ${bg} ${border} min-w-[100px]`}>
      <span className={`text-2xl font-bold font-mono ${color}`}>{value}</span>
      {sub && <span className={`text-xs font-mono ${color} opacity-70 mt-0.5`}>{sub}</span>}
      <span className="text-xs text-gray-400 mt-1.5 font-medium uppercase tracking-wider">{label}</span>
    </div>
  )
}

function CircleProgress({ pass, total }: { pass: number; total: number }) {
  const radius = 36
  const stroke = 7
  const normalizedRadius = radius - stroke / 2
  const circumference = 2 * Math.PI * normalizedRadius
  const pct = total > 0 ? pass / total : 0
  const offset = circumference * (1 - pct)

  const color = pct === 1 ? '#10b981' : pct >= 0.5 ? '#f59e0b' : '#ef4444'
  const glow  = pct === 1 ? 'drop-shadow(0 0 6px rgba(16,185,129,0.5))' : ''

  return (
    <div className="relative flex items-center justify-center w-24 h-24">
      <svg width="96" height="96" viewBox="0 0 96 96" style={{ filter: glow }}>
        {/* Track */}
        <circle
          cx="48" cy="48" r={normalizedRadius}
          fill="none"
          stroke="#1f2937"
          strokeWidth={stroke}
        />
        {/* Progress arc */}
        <circle
          cx="48" cy="48" r={normalizedRadius}
          fill="none"
          stroke={color}
          strokeWidth={stroke}
          strokeLinecap="round"
          strokeDasharray={`${circumference} ${circumference}`}
          strokeDashoffset={offset}
          style={{
            transform: 'rotate(-90deg)',
            transformOrigin: '48px 48px',
            transition: 'stroke-dashoffset 1s ease-out, stroke 0.5s ease',
          }}
        />
      </svg>
      {/* Center text */}
      <div className="absolute inset-0 flex flex-col items-center justify-center">
        <span className="text-2xl font-bold font-mono text-white leading-none">{pass}</span>
        <span className="text-xs font-mono text-gray-400 leading-none mt-0.5">/{total}</span>
      </div>
    </div>
  )
}

export default function ScoreCard({ reports }: Props) {
  const pass   = count(reports, 'PASS')
  const warn   = count(reports, 'WARN')
  const fail   = count(reports, 'FAIL')
  const notRun = count(reports, 'NOT_RUN')
  const total  = reports.length
  const ran    = pass + warn + fail

  const estimatedScore = total > 0
    ? Math.round((pass / total) * 85 + (warn / total) * 40)
    : 0

  const allPass = pass === total && total > 0

  return (
    <div className={`mb-8 p-5 rounded-2xl border backdrop-blur-sm animate-scale-in
      ${allPass
        ? 'bg-emerald-950/20 border-emerald-800/30 glow-green'
        : fail > 0
        ? 'bg-red-950/20 border-red-800/30'
        : 'bg-gray-800/40 border-gray-700/40'
      }`}>

      <div className="flex flex-wrap items-center gap-5">
        {/* Circular progress */}
        <div className="flex flex-col items-center gap-1.5">
          <CircleProgress pass={pass} total={total} />
          <span className="text-xs text-gray-400 font-medium uppercase tracking-widest">PASS</span>
        </div>

        {/* Stat chips */}
        <div className="flex flex-wrap gap-3">
          <StatChip label="Warn"    value={warn}   color="text-amber-400"   bg="bg-amber-500/10"   border="border-amber-500/20" />
          <StatChip label="Fail"    value={fail}   color="text-red-400"     bg="bg-red-500/10"     border="border-red-500/20"   />
          <StatChip label="Not Run" value={notRun} color="text-gray-400"    bg="bg-gray-700/30"    border="border-gray-600/30"  />
          {ran > 0 && (
            <StatChip
              label="Total Time"
              value={totalDuration(reports)}
              color="text-blue-300"
              bg="bg-blue-500/10"
              border="border-blue-500/20"
            />
          )}
          {total > 0 && (
            <StatChip
              label="Est. Score"
              value={`${estimatedScore}`}
              sub="/100"
              color={estimatedScore >= 80 ? 'text-emerald-300' : 'text-amber-300'}
              bg={estimatedScore >= 80 ? 'bg-emerald-500/10' : 'bg-amber-500/10'}
              border={estimatedScore >= 80 ? 'border-emerald-500/20' : 'border-amber-500/20'}
            />
          )}
        </div>

        {/* Progress bar + breakdown */}
        <div className="flex-1 min-w-[220px] space-y-2">
          <div className="flex justify-between text-xs text-gray-500 font-mono">
            <span>{ran}/{total} tasks run</span>
            <span>{total > 0 ? Math.round((pass / total) * 100) : 0}% passing</span>
          </div>
          <div className="h-3 bg-gray-800 rounded-full overflow-hidden flex gap-0.5">
            {pass  > 0 && <div className="bg-emerald-500 rounded-full transition-all duration-700" style={{ width: `${(pass /total)*100}%` }} />}
            {warn  > 0 && <div className="bg-amber-500  rounded-full transition-all duration-700" style={{ width: `${(warn /total)*100}%` }} />}
            {fail  > 0 && <div className="bg-red-500    rounded-full transition-all duration-700" style={{ width: `${(fail /total)*100}%` }} />}
            {notRun> 0 && <div className="bg-gray-700   rounded-full transition-all duration-700" style={{ width: `${(notRun/total)*100}%` }} />}
          </div>

          {/* Per-task dots */}
          <div className="flex gap-1.5 mt-2">
            {reports.map(r => {
              const dot = r.status === 'PASS' ? 'bg-emerald-500' :
                          r.status === 'WARN' ? 'bg-amber-500'   :
                          r.status === 'FAIL' ? 'bg-red-500'     :
                          r.status === 'IN_PROGRESS' ? 'bg-blue-500 animate-pulse' : 'bg-gray-700'
              return (
                <div
                  key={r.task}
                  title={`${r.task}: ${r.status}`}
                  className={`flex-1 h-1.5 rounded-full ${dot} transition-all duration-500`}
                />
              )
            })}
          </div>
          <div className="flex gap-1.5">
            {reports.map(r => (
              <div key={r.task} className="flex-1 text-center text-xs font-mono text-gray-600">{r.task}</div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
