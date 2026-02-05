/**
 * Paciolus useBenchmarks Hook
 * Sprint 46: Benchmark Frontend Components
 *
 * React hook for fetching and comparing client ratios to industry benchmarks.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Benchmark reference data fetched from API (public aggregate data)
 * - Comparison results computed in real-time, never stored
 * - Client ratio data is ephemeral (session only)
 */

'use client';

import { useState, useCallback } from 'react';
import { useAuth } from '@/context/AuthContext';
import { apiGet, apiPost } from '@/utils';

// =============================================================================
// TYPES
// =============================================================================

/** Single benchmark data point from API */
export interface BenchmarkData {
  ratio_name: string;
  p10: number;
  p25: number;
  p50: number;
  p75: number;
  p90: number;
  mean: number;
  std_dev: number;
  sample_size: number;
  source: string;
  notes?: string | null;
}

/** Complete benchmark set for an industry */
export interface BenchmarkSet {
  industry: string;
  fiscal_year: number;
  benchmarks: Record<string, BenchmarkData>;
  source_attribution: string;
  data_quality_score: number;
  available_ratios: string[];
}

/** Result of comparing a single ratio to benchmark */
export interface BenchmarkComparisonResult {
  ratio_name: string;
  client_value: number;
  percentile: number;
  percentile_label: string;
  vs_median: number;
  vs_mean: number;
  position: 'excellent' | 'above_average' | 'average' | 'below_average' | 'concerning' | 'critical';
  interpretation: string;
  health_indicator: 'positive' | 'neutral' | 'negative';
  benchmark_median: number;
  benchmark_mean: number;
}

/** Response from benchmark comparison API */
export interface BenchmarkComparisonResponse {
  industry: string;
  fiscal_year: number;
  comparisons: BenchmarkComparisonResult[];
  overall_score: number;
  overall_health: 'strong' | 'moderate' | 'concerning';
  source_attribution: string;
  generated_at: string;
  disclaimer: string;
}

/** Benchmark source information */
export interface BenchmarkSourceInfo {
  name: string;
  description: string;
  url?: string;
  data_type: string;
  update_frequency?: string;
  note?: string;
}

/** Benchmark sources response */
export interface BenchmarkSourcesResponse {
  primary_sources: BenchmarkSourceInfo[];
  coverage: {
    industries: number;
    ratios_per_industry: number;
    fiscal_year: number;
  };
  disclaimer: string;
  last_updated: string;
  available_industries: string[];
}

// =============================================================================
// HOOK OPTIONS AND RETURN TYPES
// =============================================================================

interface UseBenchmarksOptions {
  /** Auto-fetch available industries on mount */
  autoFetchIndustries?: boolean;
}

interface UseBenchmarksReturn {
  /** List of available industries */
  availableIndustries: string[];
  /** Current benchmark set (for selected industry) */
  benchmarkSet: BenchmarkSet | null;
  /** Comparison results */
  comparisonResults: BenchmarkComparisonResponse | null;
  /** Source information */
  sources: BenchmarkSourcesResponse | null;
  /** Loading states */
  isLoadingIndustries: boolean;
  isLoadingBenchmarks: boolean;
  isLoadingComparison: boolean;
  isLoadingSources: boolean;
  /** Error message */
  error: string | null;
  /** Fetch available industries */
  fetchIndustries: () => Promise<void>;
  /** Fetch benchmarks for an industry */
  fetchBenchmarks: (industry: string, fiscalYear?: number) => Promise<void>;
  /** Compare ratios to benchmarks */
  compareToBenchmarks: (ratios: Record<string, number>, industry: string) => Promise<void>;
  /** Fetch source information */
  fetchSources: () => Promise<void>;
  /** Clear all data */
  clear: () => void;
}

// =============================================================================
// HOOK IMPLEMENTATION
// =============================================================================

/**
 * Hook for fetching and managing benchmark comparison data.
 *
 * Usage:
 * ```tsx
 * const {
 *   availableIndustries,
 *   comparisonResults,
 *   fetchBenchmarks,
 *   compareToBenchmarks,
 * } = useBenchmarks();
 *
 * // Get benchmarks for retail
 * await fetchBenchmarks('retail');
 *
 * // Compare client ratios
 * await compareToBenchmarks(
 *   { current_ratio: 1.8, gross_margin: 0.35 },
 *   'retail'
 * );
 * ```
 */
export function useBenchmarks(options: UseBenchmarksOptions = {}): UseBenchmarksReturn {
  const { autoFetchIndustries = false } = options;
  const { token, isAuthenticated } = useAuth();

  // State
  const [availableIndustries, setAvailableIndustries] = useState<string[]>([]);
  const [benchmarkSet, setBenchmarkSet] = useState<BenchmarkSet | null>(null);
  const [comparisonResults, setComparisonResults] = useState<BenchmarkComparisonResponse | null>(null);
  const [sources, setSources] = useState<BenchmarkSourcesResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Loading states
  const [isLoadingIndustries, setIsLoadingIndustries] = useState(false);
  const [isLoadingBenchmarks, setIsLoadingBenchmarks] = useState(false);
  const [isLoadingComparison, setIsLoadingComparison] = useState(false);
  const [isLoadingSources, setIsLoadingSources] = useState(false);

  // Fetch available industries (public endpoint - no auth required)
  const fetchIndustries = useCallback(async () => {
    setIsLoadingIndustries(true);
    setError(null);

    try {
      // Public endpoint - pass null for token
      const response = await apiGet<string[]>('/benchmarks/industries', null);

      if (!response.ok || !response.data) {
        setError(response.error || 'Failed to fetch industries');
        return;
      }

      setAvailableIndustries(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch industries');
    } finally {
      setIsLoadingIndustries(false);
    }
  }, []);

  // Fetch benchmarks for an industry (public endpoint - no auth required)
  const fetchBenchmarks = useCallback(async (industry: string, fiscalYear: number = 2025) => {
    setIsLoadingBenchmarks(true);
    setError(null);

    try {
      const url = `/benchmarks/${industry.toLowerCase()}?fiscal_year=${fiscalYear}`;
      // Public endpoint - pass null for token
      const response = await apiGet<BenchmarkSet>(url, null);

      if (!response.ok || !response.data) {
        setError(response.error || 'Failed to fetch benchmarks');
        setBenchmarkSet(null);
        return;
      }

      setBenchmarkSet(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch benchmarks');
      setBenchmarkSet(null);
    } finally {
      setIsLoadingBenchmarks(false);
    }
  }, []);

  // Compare ratios to benchmarks (requires authentication)
  const compareToBenchmarks = useCallback(async (
    ratios: Record<string, number>,
    industry: string
  ) => {
    if (!token || !isAuthenticated) {
      setError('Authentication required for comparison');
      return;
    }

    setIsLoadingComparison(true);
    setError(null);

    try {
      const response = await apiPost<BenchmarkComparisonResponse>(
        '/benchmarks/compare',
        token,
        { ratios, industry: industry.toLowerCase() }
      );

      if (!response.ok || !response.data) {
        setError(response.error || 'Failed to compare ratios');
        setComparisonResults(null);
        return;
      }

      setComparisonResults(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to compare ratios');
      setComparisonResults(null);
    } finally {
      setIsLoadingComparison(false);
    }
  }, [token, isAuthenticated]);

  // Fetch source information (public endpoint - no auth required)
  const fetchSources = useCallback(async () => {
    setIsLoadingSources(true);
    setError(null);

    try {
      // Public endpoint - pass null for token
      const response = await apiGet<BenchmarkSourcesResponse>('/benchmarks/sources', null);

      if (!response.ok || !response.data) {
        setError(response.error || 'Failed to fetch sources');
        return;
      }

      setSources(response.data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch sources');
    } finally {
      setIsLoadingSources(false);
    }
  }, []);

  // Clear all data
  const clear = useCallback(() => {
    setBenchmarkSet(null);
    setComparisonResults(null);
    setSources(null);
    setError(null);
  }, []);

  // Auto-fetch industries on mount if configured
  // Note: Using useEffect with autoFetchIndustries dependency
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useState(() => {
    if (autoFetchIndustries) {
      fetchIndustries();
    }
  });

  return {
    availableIndustries,
    benchmarkSet,
    comparisonResults,
    sources,
    isLoadingIndustries,
    isLoadingBenchmarks,
    isLoadingComparison,
    isLoadingSources,
    error,
    fetchIndustries,
    fetchBenchmarks,
    compareToBenchmarks,
    fetchSources,
    clear,
  };
}

export default useBenchmarks;
