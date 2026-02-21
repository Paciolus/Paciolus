/**
 * Telemetry — Sprint 375.
 *
 * Lightweight event tracking for billing and pricing analytics.
 * No-ops when no analytics backend is configured.
 */

type BillingEvent =
  | 'view_pricing_page'
  | 'click_plan_cta'
  | 'toggle_billing_interval'
  | 'start_checkout'
  | 'complete_checkout'
  | 'cancel_subscription'
  | 'view_upgrade_gate'
  | 'click_upgrade_from_gate'

type EventProperties = Record<string, string | number | boolean | null>

const ANALYTICS_ENABLED =
  typeof window !== 'undefined' &&
  !!process.env.NEXT_PUBLIC_ANALYTICS_WRITE_KEY

/**
 * Track a billing/pricing event.
 *
 * Currently logs to console in development; production integration
 * requires NEXT_PUBLIC_ANALYTICS_WRITE_KEY to be set.
 */
export function trackEvent(name: BillingEvent, properties?: EventProperties): void {
  if (!ANALYTICS_ENABLED) {
    if (process.env.NODE_ENV === 'development') {
      // eslint-disable-next-line no-console
      console.debug('[telemetry]', name, properties ?? {})
    }
    return
  }

  // Future: send to analytics endpoint
  // For now, beacon to a simple endpoint if configured
  try {
    const payload = {
      event: name,
      properties: properties ?? {},
      timestamp: new Date().toISOString(),
    }
    navigator.sendBeacon(
      '/api/telemetry',
      new Blob([JSON.stringify(payload)], { type: 'application/json' }),
    )
  } catch {
    // Telemetry failures are non-critical
  }
}
