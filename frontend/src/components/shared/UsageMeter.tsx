'use client'

/**
 * UsageMeter — Sprint 368.
 *
 * Progress bar showing usage against tier limits (diagnostics, clients).
 */

interface UsageMeterProps {
  /** Current usage count */
  used: number
  /** Limit (0 = unlimited) */
  limit: number
  /** Label for the meter */
  label: string
}

export function UsageMeter({ used, limit, label }: UsageMeterProps) {
  const isUnlimited = limit === 0
  const percentage = isUnlimited ? 0 : Math.min((used / limit) * 100, 100)
  const isNearLimit = !isUnlimited && percentage >= 80
  const isAtLimit = !isUnlimited && used >= limit

  return (
    <div className="space-y-2">
      <div className="flex justify-between items-baseline">
        <span className="text-sm font-sans text-content-secondary">{label}</span>
        <span className="type-num-sm text-content-primary">
          {isUnlimited ? (
            <>{used} / <span className="text-sage-600">Unlimited</span></>
          ) : (
            <span className={isAtLimit ? 'text-clay-600' : isNearLimit ? 'text-amber-600' : ''}>
              {used} / {limit}
            </span>
          )}
        </span>
      </div>
      {!isUnlimited && (
        <div className="h-2 bg-oatmeal-200 rounded-full overflow-hidden">
          <div
            className={`h-full rounded-full transition-all duration-300 ${
              isAtLimit ? 'bg-clay-500' : isNearLimit ? 'bg-amber-500' : 'bg-sage-500'
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      )}
    </div>
  )
}
