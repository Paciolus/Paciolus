/**
 * Paciolus useTrends Hook
 * Sprint 34: Trend Visualization
 *
 * React hook for fetching historical trend data for a client.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Trend data is fetched from API and stored in React state (memory only)
 * - No financial data is persisted to localStorage or sessionStorage
 * - Only aggregate totals and ratios are processed
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiGet } from '@/utils';
import type { TrendDataPoint, TrendDirection } from '@/components/analytics/TrendSparkline';
import { METRIC_DISPLAY_NAMES, PERCENTAGE_METRICS, CURRENCY_METRICS } from '@/types/metrics';

// API Response Types
interface TrendPointAPI {
  period_date: string;
  value: number;
  change_from_previous: number | null;
  change_percent: number | null;
}

interface TrendSummaryAPI {
  metric_name: string;
  data_points: TrendPointAPI[];
  overall_direction: 'positive' | 'negative' | 'neutral';
  total_change: number;
  total_change_percent: number;
  periods_analyzed: number;
  average_value: number;
  min_value: number;
  max_value: number;
}

interface TrendAnalysisAPI {
  periods_analyzed: number;
  date_range: {
    start: string | null;
    end: string | null;
  };
  category_trends: Record<string, TrendSummaryAPI>;
  ratio_trends: Record<string, TrendSummaryAPI>;
}

interface ClientTrendsResponse {
  client_id: number;
  client_name: string;
  analysis: TrendAnalysisAPI | null;
  periods_analyzed: number;
  period_type_filter: string | null;
  error?: string;
  message?: string;
}

// Processed trend data for UI components
export interface TrendMetric {
  metricName: string;
  displayName: string;
  currentValue: string;
  dataPoints: TrendDataPoint[];
  direction: TrendDirection;
  totalChange: number;
  totalChangePercent: number;
  periodsAnalyzed: number;
  averageValue: number;
  minValue: number;
  maxValue: number;
  valuePrefix: string;
  valueSuffix: string;
}

interface UseTrendsOptions {
  /** Client ID to fetch trends for */
  clientId?: number;
  /** Period type filter (monthly, quarterly, annual) */
  periodType?: 'monthly' | 'quarterly' | 'annual';
  /** Maximum periods to analyze (default: 12) */
  limit?: number;
  /** Auto-fetch on mount (default: false - requires clientId) */
  autoFetch?: boolean;
}

interface UseTrendsReturn {
  /** Category trends (assets, liabilities, etc.) */
  categoryTrends: TrendMetric[];
  /** Ratio trends (current ratio, margins, etc.) */
  ratioTrends: TrendMetric[];
  /** Number of periods analyzed */
  periodsAnalyzed: number;
  /** Date range of analysis */
  dateRange: { start: string | null; end: string | null };
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Whether sufficient data exists for trend analysis */
  hasData: boolean;
  /** Fetch trends for a client */
  fetchTrends: (clientId: number, periodType?: string) => Promise<void>;
  /** Clear trend data */
  clearTrends: () => void;
}

/**
 * Hook for fetching and managing client trend data.
 *
 * Usage:
 * ```tsx
 * const { ratioTrends, isLoading, fetchTrends } = useTrends({ clientId: 123 });
 *
 * // Fetch trends for a specific client
 * await fetchTrends(123, 'quarterly');
 *
 * // Use trend data in components
 * {ratioTrends.map(trend => (
 *   <TrendSummaryCard
 *     key={trend.metricName}
 *     name={trend.displayName}
 *     currentValue={trend.currentValue}
 *     trendData={trend.dataPoints}
 *     direction={trend.direction}
 *     {...trend}
 *   />
 * ))}
 * ```
 */
export function useTrends(options: UseTrendsOptions = {}): UseTrendsReturn {
  const { clientId, periodType, limit = 12, autoFetch = false } = options;
  const { token, isAuthenticated } = useAuth();

  const [categoryTrends, setCategoryTrends] = useState<TrendMetric[]>([]);
  const [ratioTrends, setRatioTrends] = useState<TrendMetric[]>([]);
  const [periodsAnalyzed, setPeriodsAnalyzed] = useState(0);
  const [dateRange, setDateRange] = useState<{ start: string | null; end: string | null }>({
    start: null,
    end: null,
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Convert API trend data to UI format
  const convertTrendSummary = (
    key: string,
    summary: TrendSummaryAPI
  ): TrendMetric => {
    // Format period dates for display
    const dataPoints: TrendDataPoint[] = summary.data_points.map(point => {
      const date = new Date(point.period_date);
      // Format as short month + year (e.g., "Mar '25")
      const period = date.toLocaleDateString('en-US', {
        month: 'short',
        year: '2-digit',
      }).replace(' ', " '");

      return {
        period,
        value: point.value,
        periodDate: point.period_date,
      };
    });

    // Determine formatting based on metric type
    const isPercentage = PERCENTAGE_METRICS.has(key);
    const isCurrency = CURRENCY_METRICS.has(key);

    // Get current value (last data point)
    const currentRawValue = dataPoints.length > 0
      ? dataPoints[dataPoints.length - 1].value
      : 0;

    // Format current value for display
    let currentValue: string;
    if (isPercentage) {
      currentValue = `${currentRawValue.toFixed(1)}%`;
    } else if (isCurrency) {
      currentValue = `$${currentRawValue.toLocaleString(undefined, {
        minimumFractionDigits: 0,
        maximumFractionDigits: 0,
      })}`;
    } else {
      currentValue = currentRawValue.toFixed(2);
    }

    return {
      metricName: key,
      displayName: METRIC_DISPLAY_NAMES[key] || summary.metric_name,
      currentValue,
      dataPoints,
      direction: summary.overall_direction as TrendDirection,
      totalChange: summary.total_change,
      totalChangePercent: summary.total_change_percent,
      periodsAnalyzed: summary.periods_analyzed,
      averageValue: summary.average_value,
      minValue: summary.min_value,
      maxValue: summary.max_value,
      valuePrefix: isCurrency ? '$' : '',
      valueSuffix: isPercentage ? '%' : '',
    };
  };

  // Fetch trends from API
  const fetchTrends = useCallback(async (
    fetchClientId: number,
    fetchPeriodType?: string
  ) => {
    if (!token) {
      setError('Authentication required');
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      // Build query params
      const params = new URLSearchParams();
      if (fetchPeriodType) {
        params.append('period_type', fetchPeriodType);
      }
      params.append('limit', limit.toString());

      const queryString = params.toString();
      const url = `/clients/${fetchClientId}/trends${queryString ? `?${queryString}` : ''}`;

      const response = await apiGet<ClientTrendsResponse>(url, token);

      if (!response.ok || response.error) {
        setError(response.error || 'Failed to fetch trends');
        setCategoryTrends([]);
        setRatioTrends([]);
        return;
      }

      const data = response.data;

      if (!data) {
        setError('No response data');
        setCategoryTrends([]);
        setRatioTrends([]);
        return;
      }

      // Check for insufficient data case (API returns error/message in data)
      if (data.error || data.message) {
        setError(data.message || data.error || 'Failed to fetch trends');
        setCategoryTrends([]);
        setRatioTrends([]);
        setPeriodsAnalyzed(data.periods_analyzed || 0);
        setDateRange({ start: null, end: null });
        return;
      }

      if (!data.analysis) {
        setError('No trend data available');
        setCategoryTrends([]);
        setRatioTrends([]);
        return;
      }

      const { analysis } = data;

      // Convert category trends
      const convertedCategories = Object.entries(analysis.category_trends).map(
        ([key, summary]) => convertTrendSummary(key, summary)
      );

      // Convert ratio trends
      const convertedRatios = Object.entries(analysis.ratio_trends).map(
        ([key, summary]) => convertTrendSummary(key, summary)
      );

      setCategoryTrends(convertedCategories);
      setRatioTrends(convertedRatios);
      setPeriodsAnalyzed(analysis.periods_analyzed);
      setDateRange(analysis.date_range);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch trends';
      setError(errorMessage);
      setCategoryTrends([]);
      setRatioTrends([]);
    } finally {
      setIsLoading(false);
    }
  }, [token, limit]);

  // Clear trend data
  const clearTrends = useCallback(() => {
    setCategoryTrends([]);
    setRatioTrends([]);
    setPeriodsAnalyzed(0);
    setDateRange({ start: null, end: null });
    setError(null);
  }, []);

  // Auto-fetch on mount if clientId provided
  useEffect(() => {
    if (autoFetch && clientId && isAuthenticated) {
      fetchTrends(clientId, periodType);
    }
  }, [autoFetch, clientId, periodType, isAuthenticated, fetchTrends]);

  return {
    categoryTrends,
    ratioTrends,
    periodsAnalyzed,
    dateRange,
    isLoading,
    error,
    hasData: categoryTrends.length > 0 || ratioTrends.length > 0,
    fetchTrends,
    clearTrends,
  };
}

export default useTrends;
