'use client'

/**
 * PlanCard — Sprint 373 + Phase LIX billing refresh.
 *
 * Displays current subscription plan details with status badge.
 * Uses display names (Solo/Team/Organization) and trial-aware messaging.
 */

interface PlanCardProps {
  tier: string
  status: string
  interval: string | null
  periodEnd: string | null
  cancelAtPeriodEnd: boolean
}

const TIER_DISPLAY_NAMES: Record<string, string> = {
  free: 'Free',
  solo: 'Solo',
  professional: 'Solo',
  team: 'Team',
}

const STATUS_STYLES: Record<string, string> = {
  active: 'bg-sage-50 text-sage-700 border-sage-200',
  trialing: 'bg-sage-50 text-sage-700 border-sage-200',
  past_due: 'bg-clay-50 text-clay-700 border-clay-200',
  canceled: 'bg-oatmeal-200 text-content-secondary border-theme',
}

const STATUS_LABELS: Record<string, string> = {
  active: 'Active',
  trialing: 'Trialing',
  past_due: 'Past Due',
  canceled: 'Canceled',
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })
}

export function PlanCard({ tier, status, interval, periodEnd, cancelAtPeriodEnd }: PlanCardProps) {
  const statusStyle = STATUS_STYLES[status] ?? STATUS_STYLES.active
  const statusLabel = STATUS_LABELS[status] ?? status
  const displayName = TIER_DISPLAY_NAMES[tier] ?? tier

  return (
    <div className="bg-surface-card border border-theme rounded-lg p-6">
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="font-serif text-xl text-content-primary">{displayName}</h3>
          {interval && (
            <p className="text-sm text-content-secondary font-sans mt-1">
              Billed {interval === 'annual' ? 'annually' : 'monthly'}
            </p>
          )}
        </div>
        <span className={`text-xs font-sans font-medium px-2.5 py-1 rounded-full border ${statusStyle}`}>
          {statusLabel}
        </span>
      </div>

      {/* Trial countdown */}
      {status === 'trialing' && periodEnd && !cancelAtPeriodEnd && (
        <div className="bg-sage-50 border border-sage-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-sage-700 font-sans">
            Your 7-day free trial converts to a paid subscription on{' '}
            <span className="font-medium">{formatDate(periodEnd)}</span>.
          </p>
        </div>
      )}

      {/* Cancel-at-period-end warning */}
      {cancelAtPeriodEnd && periodEnd && (
        <div className="bg-clay-50 border border-clay-200 rounded-lg p-3 mb-4">
          <p className="text-sm text-clay-700 font-sans">
            Your subscription will end on{' '}
            <span className="font-medium">{formatDate(periodEnd)}</span>.
            {' '}You will lose access to paid features after this date.
          </p>
        </div>
      )}

      {/* Next billing date (active, not canceling, not trialing — trialing has its own block) */}
      {periodEnd && !cancelAtPeriodEnd && status !== 'trialing' && (
        <p className="text-sm text-content-muted font-sans">
          Next billing date:{' '}
          <span className="font-mono text-content-secondary">
            {formatDate(periodEnd)}
          </span>
        </p>
      )}
    </div>
  )
}
