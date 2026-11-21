/* Presents a model's inventory record and review stage evidence. */
import { useState } from 'react'
import type { ReactNode } from 'react'
import { AlertCircle, FileCode2, Play } from 'lucide-react'
import { apiMode } from '../api/client'
import type { Evidence, InventoryRecord, Run } from '../api/types'
import { formatDate } from '../formatting/formatDates'
import { NOT_DISCOVERED } from '../formatting/statusStyles'
import { EvidenceDrawer } from '../components/EvidenceDrawer'
import { EmptyState } from '../components/EmptyState'
import { GateReviewPanel } from '../components/GateReviewPanel'
import { StageStepper } from '../components/StageStepper'
import { TierBadge } from '../components/TierBadge'
import { StatusBadge } from '../components/StatusBadge'

/** Renders the five stamps, tier rationale, and evidence-backed inventory. */
export function PassportTab({
  model,
  run,
  runLoading,
  onStartRun,
  startPending,
  startError,
}: {
  model: InventoryRecord
  run: Run | null
  runLoading: boolean
  onStartRun: () => void
  startPending: boolean
  startError: string | null
}) {
  const [evidence, setEvidence] = useState<Evidence | null>(null)
  const awaitingStage = run?.status === 'AWAITING_REVIEW' ? run.current_stage : null

  return (
    <div className="space-y-6">
      <section>
        <div className="mb-3 flex flex-wrap items-center justify-between gap-3">
          <div>
            <h3 className="font-semibold text-slate-900">Passport stages</h3>
            <p className="mt-1 text-sm text-slate-500">Each stage pauses for a human decision before the next begins.</p>
          </div>
          {!model.pipeline_status.discover || !run || ['COMPLETED', 'REJECTED', 'FAILED'].includes(run.status) ? (
            <button
              type="button"
              onClick={onStartRun}
              disabled={apiMode === 'snapshot' || startPending || runLoading}
              className="inline-flex items-center gap-2 rounded-lg bg-teal-800 px-4 py-2.5 text-sm font-semibold text-white hover:bg-teal-900 disabled:cursor-not-allowed disabled:opacity-50"
            >
              <Play size={16} aria-hidden="true" />
              {startPending ? 'Starting…' : 'Start run'}
            </button>
          ) : null}
        </div>
        {startError && <p className="mb-3 text-sm text-rose-800" role="alert">{startError}</p>}
        {apiMode === 'snapshot' && <p className="mb-3 text-xs text-amber-900">Recorded runs are read-only.</p>}
        {runLoading ? (
          <p className="py-4 text-sm text-slate-500" role="status">Loading current run…</p>
        ) : run ? (
          <StageStepper statuses={model.pipeline_status} run={run} />
        ) : (
          <StageStepper statuses={model.pipeline_status} run={null} />
        )}
      </section>

      {run && awaitingStage && (
        <GateReviewPanel runId={run.run_id} stage={awaitingStage} />
      )}

      <section className="grid gap-5 xl:grid-cols-2">
        <div className="space-y-5">
          <RecordSection title="Model purpose">
            <Field label="Purpose" value={model.purpose ?? NOT_DISCOVERED} evidence={model.field_evidence.purpose} onEvidence={setEvidence} />
            <Field label="Algorithm" value={model.algorithm ?? NOT_DISCOVERED} evidence={model.field_evidence.algorithm} onEvidence={setEvidence} />
            <Field label="Target variable" value={model.target_variable ?? 'Not recorded'} evidence={model.field_evidence.target_variable} onEvidence={setEvidence} />
            <Field label="Language" value={model.language} evidence={model.field_evidence.language} onEvidence={setEvidence} />
          </RecordSection>
          <RecordSection title="Inputs and outputs">
            {model.input_variables.length ? (
              <ul className="divide-y divide-slate-100">
                {model.input_variables.map((variable) => (
                  <li key={variable.name} className="py-3 first:pt-0 last:pb-0">
                    <p className="font-medium text-slate-800">{variable.name}</p>
                    <p className="mt-1 text-sm text-slate-600">{variable.description}</p>
                    <p className="mt-1 text-xs text-slate-500">Transformation: {variable.transformation ?? 'None recorded'}</p>
                  </li>
                ))}
              </ul>
            ) : <p className="text-sm text-slate-500">No input variables are recorded.</p>}
            <Field label="Outputs" value={model.outputs.join(', ')} evidence={model.field_evidence.outputs} onEvidence={setEvidence} />
          </RecordSection>
        </div>

        <div className="space-y-5">
          <RecordSection title="Risk tier">
            {model.tiering ? (<>
            <div className="flex items-center gap-3">
              <TierBadge tier={model.tiering.tier} />
              <span className="text-sm text-slate-600">
                Materiality {model.tiering.materiality_score} · Complexity {model.tiering.complexity_score}
              </span>
            </div>
            <ul className="mt-3 list-disc space-y-1 pl-5 text-sm text-slate-700">
              {model.tiering.rationale.map((reason) => <li key={reason}>{reason}</li>)}
            </ul>
            </>) : <p className="text-sm text-slate-500">{NOT_DISCOVERED}</p>}
          </RecordSection>
          <RecordSection title="Business and governance">
            <Field label="Business line" value={model.business_line ?? 'Not recorded'} evidence={model.field_evidence.business_line} onEvidence={setEvidence} />
            <Field label="Model owner" value={model.model_owner ?? 'Not recorded'} evidence={model.field_evidence.model_owner} onEvidence={setEvidence} />
            <Field label="Exposure" value={model.exposure_gbp_m == null ? 'Not recorded' : `GBP ${model.exposure_gbp_m.toLocaleString()}m`} evidence={model.field_evidence.exposure_gbp_m} onEvidence={setEvidence} />
            <Field label="Regulatory use" value={model.regulatory_use ?? 'Not recorded'} evidence={model.field_evidence.regulatory_use} onEvidence={setEvidence} />
            <Field label="Document status" value={model.doc_status ? <StatusBadge status={model.doc_status} /> : NOT_DISCOVERED} evidence={model.field_evidence.doc_status} onEvidence={setEvidence} />
            <Field label="Document last updated" value={formatDate(model.doc_last_updated)} evidence={model.field_evidence.doc_last_updated} onEvidence={setEvidence} />
          </RecordSection>
        </div>
      </section>

      <section className="grid gap-5 xl:grid-cols-2">
        <RecordSection title="Open questions">
          {model.open_questions.length ? (
            <ul className="space-y-2">
              {model.open_questions.map((question) => (
                <li key={question} className="flex gap-2 text-sm text-slate-700">
                  <AlertCircle size={16} className="mt-0.5 shrink-0 text-amber-700" aria-hidden="true" />
                  {question}
                </li>
              ))}
            </ul>
          ) : <EmptyState title="No open questions" description="No owner input is currently requested." />}
        </RecordSection>
        <RecordSection title="Source files">
          {model.source_files.length ? (
            <ul className="space-y-2">
              {model.source_files.map((file) => (
                <li key={file.path} className="flex items-start gap-2 text-sm">
                  <FileCode2 size={16} className="mt-0.5 text-slate-500" aria-hidden="true" />
                  <button
                    type="button"
                    className="break-all text-left font-medium text-teal-800 hover:underline"
                    onClick={() => setEvidence({ file: file.path, start_line: 1, end_line: 1, quote: 'Source file reference from the inventory.' })}
                  >
                    {file.path}
                  </button>
                  <span className="shrink-0 text-xs text-slate-500">{file.lines} lines</span>
                </li>
              ))}
            </ul>
          ) : <EmptyState title="No source files listed" description="No source file paths are included in this inventory record." />}
        </RecordSection>
      </section>

      <EvidenceDrawer evidence={evidence} onClose={() => setEvidence(null)} />
    </div>
  )
}

/** Groups related inventory fields in a bordered card. */
function RecordSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
      <h3 className="mb-4 font-semibold text-slate-900">{title}</h3>
      <div className="space-y-4">{children}</div>
    </section>
  )
}

/** Displays one inventory field and its verified evidence link. */
function Field({
  label,
  value,
  evidence,
  onEvidence,
}: {
  label: string
  value: ReactNode
  evidence?: Evidence
  onEvidence: (evidence: Evidence) => void
}) {
  return (
    <div className="grid grid-cols-[minmax(0,1fr)_auto] items-start gap-x-4 gap-y-1 border-b border-slate-100 pb-3 last:border-0 last:pb-0">
      <span className="col-span-2 text-xs font-medium text-slate-500">{label}</span>
      <span className="text-sm font-medium leading-6 text-slate-800">{value}</span>
      {evidence && (
        <button type="button" className="whitespace-nowrap text-xs font-semibold leading-6 text-teal-800 hover:underline" onClick={() => onEvidence(evidence)}>
          Evidence
        </button>
      )}
    </div>
  )
}
