/**
 * Analytics Components - Sprint 19 + Sprint 34 + Sprint 36 + Sprint 37
 *
 * Key Metrics, Trend visualization, Industry-specific ratios, and Rolling Window analysis.
 */

export { MetricCard } from './MetricCard'
export { RATIO_FORMULAS } from '@/types/metrics'
export { KeyMetricsSection } from './KeyMetricsSection'
// Sprint 34: Trend Visualization
export {
  TrendSparkline,
  TrendSparklineMini,
  type TrendDataPoint,
  type TrendDirection,
} from './TrendSparkline'
export { TrendSummaryCard, TrendSummaryCardSkeleton } from './TrendSummaryCard'
export { TrendSection } from './TrendSection'
// Sprint 36: Industry Metrics
export {
  IndustryMetricsSection,
  type IndustryRatioResult,
  type IndustryRatiosData,
} from './IndustryMetricsSection'
// Sprint 37: Rolling Window Analysis
export { RollingWindowSection } from './RollingWindowSection'
