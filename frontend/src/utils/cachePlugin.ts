/**
 * Cache & deduplication plugin for API client.
 *
 * Owns: in-memory LRU cache, stale-while-revalidate, in-flight deduplication,
 * cache telemetry, periodic sweep.
 */

import {
  DEFAULT_CACHE_TTL,
  MAX_CACHE_ENTRIES,
  minutes,
  hours,
} from '@/utils/constants'
import type { ApiResponse, ApiRequestOptions } from '@/utils/transport'
import {
  performFetch,
  isRetryableError,
  BASE_RETRY_DELAY,
  MAX_RETRIES,
  DEFAULT_REQUEST_TIMEOUT,
} from '@/utils/transport'

// =============================================================================
// TYPES
// =============================================================================

interface CacheEntry<T> {
  data: T;
  timestamp: number;
  ttl: number;
}

// =============================================================================
// STATE
// =============================================================================

const queryCache = new Map<string, CacheEntry<unknown>>();
const cacheTelemetry = { hits: 0, misses: 0, evictions: 0, staleReturns: 0 };
let sweepTimerId: ReturnType<typeof setInterval> | null = null;

/** Track in-flight requests to prevent duplicate concurrent calls */
export const inflightRequests = new Map<string, Promise<ApiResponse<unknown>>>();

/** Default cache TTL values by endpoint pattern (in milliseconds) */
const ENDPOINT_TTL_CONFIG: Record<string, number> = {
  '/clients/industries': hours(1),
  '/settings/practice': minutes(30),
  '/industry-ratios': minutes(30),
  '/trends': minutes(10),
  '/rolling-analysis': minutes(10),
  '/clients': minutes(10),
  '/activity/history': minutes(5),
  '/activity/recent': minutes(5),
  '/diagnostics/summary': minutes(10),
  '/dashboard/stats': minutes(1),
  '/engagements': minutes(2),
  '/periods': minutes(10),
};

// =============================================================================
// CACHE UTILITIES
// =============================================================================

export function getCacheKey(endpoint: string, options: ApiRequestOptions = {}): string {
  if (options.method && options.method !== 'GET') {
    return '';
  }
  const keyParts = [endpoint];
  if (options.headers) {
    keyParts.push(JSON.stringify(options.headers));
  }
  return keyParts.join('|');
}

export function getEndpointTtl(endpoint: string): number {
  for (const [pattern, ttl] of Object.entries(ENDPOINT_TTL_CONFIG)) {
    if (endpoint.includes(pattern)) {
      return ttl;
    }
  }
  return DEFAULT_CACHE_TTL;
}

function isCacheValid<T>(entry: CacheEntry<T>): boolean {
  return Date.now() - entry.timestamp < entry.ttl;
}

export function getCached<T>(key: string): T | null {
  if (!key) return null;

  const entry = queryCache.get(key) as CacheEntry<T> | undefined;
  if (entry && isCacheValid(entry)) {
    queryCache.delete(key);
    queryCache.set(key, entry);
    cacheTelemetry.hits++;
    return entry.data;
  }

  if (entry) {
    queryCache.delete(key);
  }
  cacheTelemetry.misses++;
  return null;
}

export function getCachedWithStale<T>(key: string): { data: T | null; isStale: boolean } {
  if (!key) return { data: null, isStale: false };

  const entry = queryCache.get(key) as CacheEntry<T> | undefined;
  if (!entry) {
    cacheTelemetry.misses++;
    return { data: null, isStale: false };
  }

  const isStale = !isCacheValid(entry);
  if (isStale) {
    cacheTelemetry.staleReturns++;
  } else {
    queryCache.delete(key);
    queryCache.set(key, entry);
    cacheTelemetry.hits++;
  }
  return { data: entry.data, isStale };
}

export function setCached<T>(key: string, data: T, ttl: number): void {
  if (!key) return;

  if (queryCache.has(key)) {
    queryCache.delete(key);
  }

  while (queryCache.size >= MAX_CACHE_ENTRIES) {
    const oldest = queryCache.keys().next().value;
    if (oldest !== undefined) {
      queryCache.delete(oldest);
      cacheTelemetry.evictions++;
    }
  }

  queryCache.set(key, {
    data,
    timestamp: Date.now(),
    ttl,
  });
}

export function invalidateCache(pattern?: string): void {
  if (!pattern) {
    queryCache.clear();
    return;
  }

  for (const key of queryCache.keys()) {
    if (key.includes(pattern)) {
      queryCache.delete(key);
    }
  }
}

export function invalidateRelatedCaches(endpoint: string): void {
  const basePath = endpoint.split('?')[0] ?? endpoint
  invalidateCache(basePath)
  const parentPath = basePath.split('/').slice(0, -1).join('/')
  if (parentPath) {
    invalidateCache(parentPath)
  }
}

export function getCacheStats(): { size: number; keys: string[] } {
  return {
    size: queryCache.size,
    keys: Array.from(queryCache.keys()),
  };
}

export function getCacheTelemetry(): { hits: number; misses: number; evictions: number; staleReturns: number } {
  return { ...cacheTelemetry };
}

export function resetCacheTelemetry(): void {
  cacheTelemetry.hits = 0;
  cacheTelemetry.misses = 0;
  cacheTelemetry.evictions = 0;
  cacheTelemetry.staleReturns = 0;
}

function sweepExpiredEntries(): void {
  for (const [key, entry] of queryCache.entries()) {
    if (!isCacheValid(entry as CacheEntry<unknown>)) {
      queryCache.delete(key);
    }
  }
}

export function startCacheSweep(): void {
  if (sweepTimerId !== null) return;
  if (typeof window === 'undefined') return;
  sweepTimerId = setInterval(sweepExpiredEntries, 60_000);
}

export function stopCacheSweep(): void {
  if (sweepTimerId !== null) {
    clearInterval(sweepTimerId);
    sweepTimerId = null;
  }
}

// Auto-start sweep in browser environments
if (typeof window !== 'undefined') {
  startCacheSweep();
}

export async function performBackgroundRevalidation<T>(
  endpoint: string,
  token: string | null,
  options: ApiRequestOptions,
  cacheKey: string,
  onRevalidate?: (response: ApiResponse<unknown>) => void
): Promise<void> {
  const {
    headers: customHeaders = {},
    timeout = DEFAULT_REQUEST_TIMEOUT,
    cacheTtl,
    retries = MAX_RETRIES,
  } = options;

  const headers: Record<string, string> = { ...customHeaders };
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  const { buildUrl } = await import('@/utils/transport');
  const url = buildUrl(endpoint);

  try {
    let lastError: ApiResponse<T> | null = null;

    for (let attempt = 0; attempt <= retries; attempt++) {
      const result = await performFetch<T>(url, headers, 'GET', undefined, timeout);

      if (result.ok) {
        const ttl = cacheTtl ?? getEndpointTtl(endpoint);
        setCached(cacheKey, result.data, ttl);

        if (onRevalidate) {
          onRevalidate({
            ...result,
            cached: false,
            stale: false,
          });
        }
        return;
      }

      lastError = result;

      if (!isRetryableError(result.status) || attempt === retries) {
        break;
      }

      const delay = BASE_RETRY_DELAY * Math.pow(2, attempt);
      await new Promise(resolve => setTimeout(resolve, delay));
    }

    console.warn(`Background revalidation failed for ${endpoint}:`, lastError?.error);
  } catch (err) {
    console.warn(`Background revalidation error for ${endpoint}:`, err);
  }
}
