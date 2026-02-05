/**
 * Paciolus useIndustryRatios Hook
 * Sprint 36: Industry Ratio Expansion
 *
 * React hook for fetching industry-specific ratios for a client.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Ratio data is fetched from API and stored in React state (memory only)
 * - No financial data is persisted to localStorage or sessionStorage
 * - Only aggregate totals and calculated ratios are processed
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiGet } from '@/utils';
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
  const { token, isAuthenticated } = useAuth();

  const [data, setData] = useState<IndustryRatiosData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch ratios from API
  const fetchRatios = useCallback(async (fetchClientId: number) => {
    if (!token) {
      setError('Authentication required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const url = `/clients/${fetchClientId}/industry-ratios`;

      const response = await apiGet<IndustryRatiosData>(url, token);

      if (!response.ok || response.error) {
        setError(response.error || 'Failed to fetch industry ratios');
        setData(null);
        return;
      }

      if (!response.data) {
        setError('No response data');
        setData(null);
        return;
      }

      setData(response.data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch industry ratios';
      setError(errorMessage);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  // Clear ratio data
  const clearRatios = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  // Auto-fetch on mount if clientId provided
  useEffect(() => {
    if (autoFetch && clientId && isAuthenticated) {
      fetchRatios(clientId);
    }
  }, [autoFetch, clientId, isAuthenticated, fetchRatios]);

  return {
    data,
    isLoading,
    error,
    hasData: data !== null && data.ratios !== null,
    fetchRatios,
    clearRatios,
  };
}

export default useIndustryRatios;
