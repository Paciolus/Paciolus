/**
 * Analytics Components - Sprint 19 + Sprint 34 + Sprint 36
 *
 * Key Metrics, Trend visualization, and Industry-specific ratio components.
 */

export { MetricCard, RATIO_FORMULAS } from './MetricCard'
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
