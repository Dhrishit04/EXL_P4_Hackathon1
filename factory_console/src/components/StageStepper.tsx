/* Shows the five stage stamps, their statuses, timing, and human decisions. */
import { CheckCircle2 } from 'lucide-react'
import type { PipelineStatus, Run, StageName } from '../api/types'
import { formatDuration } from '../formatting/formatNumbers'
import { formatTimestamp } from '../formatting/formatDates'
import { StatusBadge } from './StatusBadge'

const stages: Array<{ name: StageName; title: string }> = [
  { name: 'discover', title: 'Discover' },
  { name: 'document', title: 'Document' },
  { name: 'redevelop', title: 'Redevelop' },
  { name: 'validate', title: 'Validate' },
  { name: 'monitor', title: 'Monitor' },
]

/** Renders a horizontal passport timeline with detailed stage stamps. */
export function StageStepper({ statuses, run }: { statuses: PipelineStatus; run: Run | null }) {
  return (
    <ol className="grid gap-3 lg:grid-cols-5" aria-label="Model passport stages">
      {stages.map(({ name, title }, index) => {
        const detail = run?.stages.find((stage) => stage.stage === name)
        const status = detail?.status ?? statuses[name]
        return (
          <li key={name} className="relative min-w-0 rounded-xl border border-slate-200 bg-white p-4 shadow-sm">
            <div className="flex flex-wrap items-start justify-between gap-2">
              <span className="flex items-center gap-2 text-sm font-semibold text-slate-900">
                <span className="grid h-7 w-7 shrink-0 place-items-center rounded-full bg-slate-100 text-xs text-slate-700">
                  {index + 1}
                </span>
                {title}
              </span>
              <StatusBadge status={status} />
            </div>
            <p className="mt-3 min-h-10 text-xs leading-5 text-slate-600">
              {detail?.summary ?? detail?.skip_reason ?? 'No run evidence recorded yet.'}
            </p>
            <p className="mt-2 text-xs text-slate-500">Duration: {formatDuration(detail?.duration_seconds)}</p>
            {detail?.gate && (
              <div className="mt-3 border-t border-slate-100 pt-3 text-xs text-slate-600">
                <p className="flex items-center gap-1 font-semibold text-emerald-800">
                  <CheckCircle2 size={14} aria-hidden="true" />
                  {detail.gate.decision} by {detail.gate.reviewer}
                </p>
                <p className="mt-1">{detail.gate.role} · {formatTimestamp(detail.gate.decided_at)}</p>
                {detail.gate.comment && <p className="mt-1 italic">“{detail.gate.comment}”</p>}
              </div>
            )}
            {detail?.error && <p className="mt-2 text-xs font-medium text-rose-800">{detail.error}</p>}
          </li>
        )
      })}
    </ol>
  )
}
