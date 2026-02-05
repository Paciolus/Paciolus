/**
 * Paciolus useRollingWindow Hook
 * Sprint 37: Rolling Window Analysis
 *
 * React hook for fetching rolling window analysis data for a client.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Rolling data is fetched from API and stored in React state (memory only)
 * - No financial data is persisted to localStorage or sessionStorage
 * - Only aggregate totals and calculated averages are processed
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiGet } from '@/utils';

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
  const { token, isAuthenticated } = useAuth();

  const [data, setData] = useState<RollingWindowResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchAnalysis = useCallback(async (
    fetchClientId: number,
    fetchWindow?: number,
    fetchPeriodType?: string
  ) => {
    if (!token) {
      setError('Authentication required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams();
      if (fetchWindow) {
        params.append('window', fetchWindow.toString());
      }
      if (fetchPeriodType) {
        params.append('period_type', fetchPeriodType);
      }

      const queryString = params.toString();
      const url = `/clients/${fetchClientId}/rolling-analysis${queryString ? `?${queryString}` : ''}`;

      const response = await apiGet<RollingWindowResponse>(url, token);

      if (!response.ok || response.error) {
        setError(response.error || 'Failed to fetch rolling analysis');
        setData(null);
        return;
      }

      if (!response.data) {
        setError('No response data');
        setData(null);
        return;
      }

      // Check for API-level error in response
      if (response.data.error) {
        setError(response.data.message || response.data.error);
      }

      setData(response.data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch rolling analysis';
      setError(errorMessage);
      setData(null);
    } finally {
      setIsLoading(false);
    }
  }, [token]);

  const clearAnalysis = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  // Auto-fetch on mount if clientId provided
  useEffect(() => {
    if (autoFetch && clientId && isAuthenticated) {
      fetchAnalysis(clientId, windowSize, periodType);
    }
  }, [autoFetch, clientId, windowSize, periodType, isAuthenticated, fetchAnalysis]);

  return {
    data,
    isLoading,
    error,
    hasData: data !== null && data.analysis !== null,
    fetchAnalysis,
    clearAnalysis,
  };
}

export default useRollingWindow;
