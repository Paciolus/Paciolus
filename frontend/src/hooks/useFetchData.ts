/**
 * Paciolus useFetchData Hook
 * Sprint 41: Performance Quick Wins - Shared Utilities
 *
 * Generic hook for fetching data from the API with authentication.
 * Extracts common pattern from useTrends, useIndustryRatios, useRollingWindow.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Data is stored in React state (memory only)
 * - No data is persisted to localStorage or sessionStorage
 */

'use client';

import { useState, useCallback, useEffect, useRef } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiGet } from '@/utils';

/**
 * Options for the useFetchData hook
 */
export interface UseFetchDataOptions<TResponse, TData = TResponse> {
  /**
   * Build the URL for the API request.
   * Receives the ID and any additional params passed to fetch().
   */
  buildUrl: (id: number, params?: Record<string, string | number | undefined>) => string;

  /**
   * Transform the API response into the data shape you need.
   * Optional - if not provided, the response is used as-is.
   */
  transform?: (response: TResponse) => TData;

  /**
   * Check if the transformed data is considered "has data".
   * Optional - defaults to checking if data is not null.
   */
  hasDataCheck?: (data: TData | null) => boolean;

  /**
   * Initial ID to fetch data for (enables auto-fetch).
   */
  initialId?: number;

  /**
   * Whether to auto-fetch when initialId is provided.
   * Default: false
   */
  autoFetch?: boolean;

  /**
   * Initial params for auto-fetch.
   */
  initialParams?: Record<string, string | number | undefined>;
}

/**
 * Return type for the useFetchData hook
 */
export interface UseFetchDataReturn<TData, TParams = Record<string, string | number | undefined>> {
  /** The fetched and transformed data */
  data: TData | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Whether data has been successfully fetched */
  hasData: boolean;
  /** Fetch data for a given ID with optional params */
  fetch: (id: number, params?: TParams) => Promise<void>;
  /** Clear all data and error state */
  clear: () => void;
  /** Refetch with the last used ID and params */
  refetch: () => Promise<void>;
}

/**
 * Generic hook for fetching data from the API with authentication.
 *
 * Handles the common pattern of:
 * - Authentication check
 * - Loading state management
 * - Error handling
 * - Data transformation
 * - Auto-fetch on mount
 *
 * @example
 * ```tsx
 * // Simple usage
 * const { data, isLoading, fetch } = useFetchData<UserResponse>({
 *   buildUrl: (id) => `/users/${id}`,
 * });
 *
 * // With transformation
 * const { data, isLoading, fetch } = useFetchData<APIResponse, ProcessedData>({
 *   buildUrl: (id, params) => `/clients/${id}/data?type=${params?.type}`,
 *   transform: (response) => processResponse(response),
 *   hasDataCheck: (data) => data !== null && data.items.length > 0,
 *   autoFetch: true,
 *   initialId: clientId,
 * });
 * ```
 */
export function useFetchData<
  TResponse,
  TData = TResponse,
  TParams extends Record<string, string | number | undefined> = Record<string, string | number | undefined>
>(
  options: UseFetchDataOptions<TResponse, TData>
): UseFetchDataReturn<TData, TParams> {
  const {
    buildUrl,
    transform,
    hasDataCheck,
    initialId,
    autoFetch = false,
    initialParams,
  } = options;

  const { token, isAuthenticated } = useAuth();

  const [data, setData] = useState<TData | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Track last fetch params for refetch
  const lastFetchRef = useRef<{ id: number; params?: TParams } | null>(null);

  // Fetch data from API
  const fetchData = useCallback(async (
    id: number,
    params?: TParams
  ) => {
    if (!token) {
      setError('Authentication required');
      return;
    }

    // Store for refetch
    lastFetchRef.current = { id, params };

    setIsLoading(true);
    setError(null);

    try {
      const url = buildUrl(id, params);
      const response = await apiGet<TResponse>(url, token);

      if (!response.ok || response.error) {
        setError(response.error || 'Failed to fetch data');
        setData(null);
        return;
      }

      if (!response.data) {
        setError('No response data');
        setData(null);
        return;
      }

      // Check for API-level error in response (common pattern in Paciolus API)
      const responseData = response.data as TResponse & { error?: string; message?: string };
      if (responseData.error) {
        setError(responseData.message || responseData.error);
        // Still set the data as some endpoints return partial data with error
      }

      // Transform if needed
      const transformedData = transform
        ? transform(response.data)
        : (response.data as unknown as TData);

      setData(transformedData);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch data';
      setError(errorMessage);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [token, buildUrl, transform]);

  // Clear data and error
  const clear = useCallback(() => {
    setData(null);
    setError(null);
    lastFetchRef.current = null;
  }, []);

  // Refetch with last params
  const refetch = useCallback(async () => {
    if (lastFetchRef.current) {
      await fetchData(lastFetchRef.current.id, lastFetchRef.current.params);
    }
  }, [fetchData]);

  // Auto-fetch on mount if configured
  useEffect(() => {
    if (autoFetch && initialId && isAuthenticated) {
      fetchData(initialId, initialParams as TParams);
    }
  }, [autoFetch, initialId, isAuthenticated, fetchData, initialParams]);

  // Determine hasData
  const hasData = hasDataCheck
    ? hasDataCheck(data)
    : data !== null;

  return {
    data,
    isLoading,
    error,
    hasData,
    fetch: fetchData,
    clear,
    refetch,
  };
}

export default useFetchData;
