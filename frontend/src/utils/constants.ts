/**
 * Centralized Constants — Sprint 161
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

/** Feature flag: enable bespoke multi-element icon definitions in BrandIcon registry */
export const USE_BESPOKE_ICONS = true
