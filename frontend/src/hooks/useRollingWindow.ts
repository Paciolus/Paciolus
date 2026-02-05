/**
 * Paciolus useRollingWindow Hook
 * Sprint 37: Rolling Window Analysis
 * Sprint 41: Refactored to use useFetchData
 *
 * React hook for fetching rolling window analysis data for a client.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Rolling data is fetched from API and stored in React state (memory only)
 * - No financial data is persisted to localStorage or sessionStorage
 * - Only aggregate totals and calculated averages are processed
 */

'use client';

import { useCallback } from 'react';
import { useFetchData } from './useFetchData';

// Momentum types from backend
export type MomentumType = 'accelerating' | 'decelerating' | 'steady' | 'reversing';
export type TrendDirection = 'positive' | 'negative' | 'neutral';

// Rolling average for a specific window
export interface RollingAverage {
  window_months: number;
  value: number;
  data_points: number;
  start_date: string;
  end_date: string;
}

// Momentum indicator
export interface MomentumIndicator {
  momentum_type: MomentumType;
  rate_of_change: number;
  acceleration: number;
  confidence: number;
}

// Result for a single metric
export interface RollingWindowMetric {
  metric_name: string;
  rolling_averages: Record<string, RollingAverage>;
  momentum: MomentumIndicator;
  current_value: number;
  trend_direction: TrendDirection;
}

// Full analysis response
export interface RollingWindowAnalysis {
  periods_analyzed: number;
  supported_windows: number[];
  date_range: {
    start: string | null;
    end: string | null;
  };
  category_rolling: Record<string, RollingWindowMetric>;
  ratio_rolling: Record<string, RollingWindowMetric>;
}

// API response
export interface RollingWindowResponse {
  client_id: number;
  client_name: string;
  analysis: RollingWindowAnalysis | null;
  periods_analyzed: number;
  window_filter: number | null;
  period_type_filter: string | null;
  error?: string;
  message?: string;
}

interface UseRollingWindowOptions {
  /** Client ID to fetch analysis for */
  clientId?: number;
  /** Specific window size to fetch (3, 6, or 12) */
  window?: 3 | 6 | 12;
  /** Period type filter */
  periodType?: 'monthly' | 'quarterly' | 'annual';
  /** Auto-fetch on mount (default: false) */
  autoFetch?: boolean;
}

interface UseRollingWindowReturn {
  /** Rolling window analysis data */
  data: RollingWindowResponse | null;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Whether data has been fetched */
  hasData: boolean;
  /** Fetch rolling analysis */
  fetchAnalysis: (clientId: number, window?: number, periodType?: string) => Promise<void>;
  /** Clear analysis data */
  clearAnalysis: () => void;
}

// Params type for the fetch function
interface RollingWindowParams extends Record<string, string | number | undefined> {
  window?: number;
  period_type?: string;
}

/**
 * Hook for fetching and managing client rolling window analysis.
 *
 * Usage:
 * ```tsx
 * const { data, isLoading, fetchAnalysis } = useRollingWindow({ clientId: 123 });
 *
 * // Fetch analysis
 * await fetchAnalysis(123);
 *
 * // Fetch specific window
 * await fetchAnalysis(123, 6); // 6-month rolling
 * ```
 */
export function useRollingWindow(options: UseRollingWindowOptions = {}): UseRollingWindowReturn {
  const { clientId, window: windowSize, periodType, autoFetch = false } = options;

  const {
    data,
    isLoading,
    error,
    hasData,
    fetch,
    clear,
  } = useFetchData<RollingWindowResponse, RollingWindowResponse, RollingWindowParams>({
    buildUrl: (id, params) => {
      const searchParams = new URLSearchParams();
      if (params?.window) {
        searchParams.append('window', String(params.window));
      }
      if (params?.period_type) {
        searchParams.append('period_type', String(params.period_type));
      }
      const queryString = searchParams.toString();
      return `/clients/${id}/rolling-analysis${queryString ? `?${queryString}` : ''}`;
    },
    hasDataCheck: (data) => data !== null && data.analysis !== null,
    autoFetch,
    initialId: clientId,
    initialParams: {
      window: windowSize,
      period_type: periodType,
    },
  });

  // Wrapper to match the original interface signature
  const fetchAnalysis = useCallback(async (
    fetchClientId: number,
    fetchWindow?: number,
    fetchPeriodType?: string
  ) => {
    await fetch(fetchClientId, {
      window: fetchWindow,
      period_type: fetchPeriodType,
    });
  }, [fetch]);

  return {
    data,
    isLoading,
    error,
    hasData,
    fetchAnalysis,
    clearAnalysis: clear,
  };
}

export default useRollingWindow;
