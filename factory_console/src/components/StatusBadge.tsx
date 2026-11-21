/* Displays a status with both a text label and an identifying icon. */
import { statusPresentation } from '../formatting/statusStyles'

/** Shows the status of a stage, document, or workflow item. */
export function StatusBadge({ status }: { status: string }) {
  const { label, className, Icon } = statusPresentation(status)
  return (
    <span className={`inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-2.5 py-1 text-xs font-semibold ${className}`}>
      <Icon size={14} aria-hidden="true" />
      {label}
    </span>
  )
}
