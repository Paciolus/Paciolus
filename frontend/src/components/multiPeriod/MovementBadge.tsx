import { MOVEMENT_TYPE_LABELS, MOVEMENT_TYPE_COLORS } from './constants'

export function MovementBadge({ type }: { type: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-sans border ${MOVEMENT_TYPE_COLORS[type] || MOVEMENT_TYPE_COLORS.unchanged}`}>
      {MOVEMENT_TYPE_LABELS[type] || type}
    </span>
  )
}
