/**
 * Paciolus useIndustryRatios Hook
 * Sprint 36: Industry Ratio Expansion
 * Sprint 41: Refactored to use useFetchData
 *
 * React hook for fetching industry-specific ratios for a client.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Ratio data is fetched from API and stored in React state (memory only)
 * - No financial data is persisted to localStorage or sessionStorage
 * - Only aggregate totals and calculated ratios are processed
 */

'use client';

import { useFetchData } from './useFetchData';
import type { IndustryRatiosData } from '@/components/analytics/IndustryMetricsSection';

interface UseIndustryRatiosOptions {
  /** Client ID to fetch ratios for */
  clientId?: number;
  /** Auto-fetch on mount (default: false - requires clientId) */
  autoFetch?: boolean;
}

interface UseIndustryRatiosReturn {
  /** Industry ratios data */
  data: IndustryRatiosData | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Whether data has been fetched */
  hasData: boolean;
  /** Fetch ratios for a client */
  fetchRatios: (clientId: number) => Promise<void>;
  /** Clear ratio data */
  clearRatios: () => void;
}

/**
 * Hook for fetching and managing client industry ratio data.
 *
 * Usage:
 * ```tsx
 * const { data, isLoading, fetchRatios } = useIndustryRatios({ clientId: 123 });
 *
 * // Fetch ratios for a specific client
 * await fetchRatios(123);
 *
 * // Use data in components
 * <IndustryMetricsSection data={data} isLoading={isLoading} />
 * ```
 */
export function useIndustryRatios(options: UseIndustryRatiosOptions = {}): UseIndustryRatiosReturn {
  const { clientId, autoFetch = false } = options;

  const {
    data,
    isLoading,
    error,
    hasData,
    fetch,
    clear,
  } = useFetchData<IndustryRatiosData>({
    buildUrl: (id) => `/clients/${id}/industry-ratios`,
    hasDataCheck: (data) => data !== null && data.ratios !== null,
    autoFetch,
    initialId: clientId,
  });

  return {
    data,
    isLoading,
    error,
    hasData,
    fetchRatios: fetch,
    clearRatios: clear,
  };
}

export default useIndustryRatios;
