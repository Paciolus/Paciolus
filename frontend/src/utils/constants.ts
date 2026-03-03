/**
 * Centralized Constants
 *
 * Single source of truth for environment variables and shared magic numbers.
 * Import from here instead of re-declaring process.env.* locally.
 */

/** Backend API base URL (no trailing slash) */
export const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'

/** Default request timeout for API calls (ms) */
export const DEFAULT_REQUEST_TIMEOUT = 30_000

/** Extended timeout for file downloads (ms) */
export const DOWNLOAD_TIMEOUT = 60_000

/** Maximum retry attempts for transient failures */
export const MAX_RETRIES = 3

/** Base delay for exponential backoff (ms) — doubles each retry */
export const BASE_RETRY_DELAY = 1_000

/** Default cache TTL for unlisted endpoints (ms) */
export const DEFAULT_CACHE_TTL = 5 * 60 * 1_000

/** TTL helper: convert minutes to milliseconds */
export const minutes = (n: number): number => n * 60 * 1_000

/** TTL helper: convert hours to milliseconds */
export const hours = (n: number): number => n * 60 * 60 * 1_000

/** Maximum entries in the API response cache before LRU eviction */
export const MAX_CACHE_ENTRIES = 100

// ── Performance SLA ─────────────────────────────────────────────────
// Canonical source: docs/02-technical/DEPLOYMENT_ARCHITECTURE.md
//   - p95 alert threshold: >3 seconds (§9.2, line 689)
//   - Scale trigger: p95 >2 seconds (§11.1, line 767)
//   - Verification target: TB analysis <5 seconds for 10K rows (§16.3, line 987)

/** p95 analysis runtime target in seconds — alert fires above this */
export const ANALYSIS_TYPICAL_SECONDS = 3

/** Maximum verified analysis time for the stated row ceiling */
export const ANALYSIS_MAX_SECONDS = 5

/** Row count ceiling for the performance claim */
export const ANALYSIS_MAX_ROWS = 10_000

/** Short stat-badge label (e.g., evidence bands, hero speed indicators) */
export const ANALYSIS_LABEL_SHORT = `< ${ANALYSIS_TYPICAL_SECONDS}s`

/** Standard marketing label (mid-length) */
export const ANALYSIS_LABEL_STANDARD = 'under three seconds'

/** Fully qualified, auditable claim for detailed copy */
export const ANALYSIS_LABEL_QUALIFIED = `typically under three seconds for files up to ${ANALYSIS_MAX_ROWS.toLocaleString()} rows`
