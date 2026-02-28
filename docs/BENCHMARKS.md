# Benchmark Framework RFC

> **Sprint 40 - Phase III Architecture Design**
> **Status:** RFC (Request for Comments)
> **Version:** 1.0.0
> **Date:** 2026-02-04

---

## Executive Summary

This RFC proposes a benchmark comparison framework for Paciolus that enables financial professionals to compare client trial balance metrics against industry standards. The framework maintains **Zero-Storage compliance** by treating benchmark data as reference data (not client data), while providing actionable insights for diagnostic assessments.

---

## 1. Problem Statement

### Current State
- Paciolus calculates 17 core ratios and 8 industry-specific ratios
- No comparison to industry standards or peer benchmarks
- Financial professionals must manually reference external sources
- No context for ratio values relative to industry benchmarks

### Desired State
- Automated comparison against industry benchmarks
- Percentile rankings (e.g., "75th percentile for retail")
- Health status informed by industry norms
- Historical trend context (industry direction)

---

## 2. Data Schema Design

### 2.1 Benchmark Data Model

```python
@dataclass
class IndustryBenchmark:
    """Industry benchmark for a specific ratio."""
    ratio_name: str              # e.g., "current_ratio"
    industry: IndustryType       # e.g., IndustryType.RETAIL
    fiscal_year: int             # e.g., 2025

    # Percentile distribution
    p10: float                   # 10th percentile
    p25: float                   # 25th percentile (Q1)
    p50: float                   # 50th percentile (median)
    p75: float                   # 75th percentile (Q3)
    p90: float                   # 90th percentile

    # Statistical measures
    mean: float
    std_dev: float
    sample_size: int             # Number of companies in sample

    # Metadata
    source: str                  # e.g., "RMA", "BLS", "SEC"
    last_updated: datetime
    notes: Optional[str]


@dataclass
class BenchmarkComparison:
    """Result of comparing a ratio to industry benchmark."""
    ratio_name: str
    client_value: float
    industry: IndustryType

    # Percentile position
    percentile: int              # 0-100
    percentile_label: str        # e.g., "75th percentile"

    # Comparison metrics
    vs_median: float             # Difference from median (%)
    vs_mean: float               # Difference from mean (%)

    # Contextual interpretation
    position: str                # "above_average", "average", "below_average"
    interpretation: str          # Human-readable explanation
    threshold_adjustment: str    # Suggested threshold status adjustment

    # Reference data
    benchmark: IndustryBenchmark


@dataclass
class BenchmarkSet:
    """Complete benchmark set for an industry."""
    industry: IndustryType
    fiscal_year: int
    benchmarks: Dict[str, IndustryBenchmark]
    source_attribution: str
    data_quality_score: float    # 0.0-1.0 confidence in data
```

### 2.2 Supported Ratios for Benchmarking

| Ratio | Key | Benchmark Availability |
|-------|-----|----------------------|
| Current Ratio | `current_ratio` | High |
| Quick Ratio | `quick_ratio` | High |
| Debt-to-Equity | `debt_to_equity` | High |
| Gross Margin | `gross_margin` | High |
| Net Profit Margin | `net_profit_margin` | High |
| Operating Margin | `operating_margin` | Medium |
| Return on Assets | `roa` | High |
| Return on Equity | `roe` | High |
| Inventory Turnover | `inventory_turnover` | Medium (Retail, Manufacturing) |
| Receivables Turnover | `receivables_turnover` | Medium |
| Asset Turnover | `asset_turnover` | Medium |

### 2.3 Industry Categories

Benchmarks will be organized by the existing `IndustryType` enum:

| Industry | NAICS Alignment | Benchmark Availability |
|----------|-----------------|----------------------|
| Technology | 51, 54 | High |
| Healthcare | 62 | High |
| Financial Services | 52 | High |
| Manufacturing | 31-33 | High |
| Retail | 44-45 | High |
| Professional Services | 54 | Medium |
| Real Estate | 53 | Medium |
| Construction | 23 | Medium |
| Hospitality | 72 | Medium |
| Transportation | 48-49 | Medium |
| Energy | 21, 22 | Medium |
| Non-Profit | Various | Low |

---

## 3. Data Sources

### 3.1 Primary Sources (Public Data)

#### Risk Management Association (RMA)
- **Coverage:** All major industries, 800+ NAICS codes
- **Metrics:** Full financial statement ratios
- **Update Frequency:** Annual
- **Cost:** Subscription-based (organization license)
- **Data Quality:** High
- **Notes:** Industry standard for credit analysis

#### SEC EDGAR Filings
- **Coverage:** Public companies (10-K, 10-Q)
- **Metrics:** Derived from financial statements
- **Update Frequency:** Quarterly
- **Cost:** Free (public data)
- **Data Quality:** High (audited statements)
- **Notes:** Requires aggregation/calculation pipeline

#### Bureau of Labor Statistics (BLS)
- **Coverage:** Industry statistics
- **Metrics:** Labor costs, productivity
- **Update Frequency:** Quarterly
- **Cost:** Free
- **Data Quality:** High
- **Notes:** Useful for operating margin context

#### Federal Reserve Economic Data (FRED)
- **Coverage:** Economic indicators
- **Metrics:** Interest rates, inflation, sector indices
- **Update Frequency:** Varies by series
- **Cost:** Free
- **Data Quality:** High
- **Notes:** Macro context for trends

### 3.2 Secondary Sources

| Source | Coverage | Cost | Integration Effort |
|--------|----------|------|-------------------|
| Dun & Bradstreet | Private company benchmarks | Paid | Medium |
| IBISWorld | Industry reports | Paid | Medium |
| ProfitCents | Small business benchmarks | Paid | Low |
| Sageworks (Abrigo) | Private company data | Paid | Medium |
| BizMiner | Industry financial reports | Paid | Low |

### 3.3 Recommended Initial Implementation

**Phase III Tier 1: Free Public Data**
1. SEC EDGAR aggregation for public company benchmarks
2. FRED integration for economic context
3. BLS data for operating metrics

**Phase III Tier 2: Curated Static Data**
1. Pre-compiled benchmark tables by industry
2. Annual manual update process
3. Clear source attribution

**Phase III Tier 3: Premium Integration (Future)**
1. RMA direct integration
2. Real-time benchmark updates
3. Enhanced percentile granularity

---

## 4. Comparison Calculation Approach

### 4.1 Percentile Calculation

```python
def calculate_percentile(
    client_value: float,
    benchmark: IndustryBenchmark
) -> int:
    """
    Calculate client's percentile position using linear interpolation.

    Returns integer percentile (0-100).
    """
    # Known percentile points
    percentiles = [
        (10, benchmark.p10),
        (25, benchmark.p25),
        (50, benchmark.p50),
        (75, benchmark.p75),
        (90, benchmark.p90),
    ]

    # Handle edge cases
    if client_value <= benchmark.p10:
        return max(1, int(10 * (client_value / benchmark.p10))) if benchmark.p10 != 0 else 5
    if client_value >= benchmark.p90:
        return min(99, 90 + int(10 * ((client_value - benchmark.p90) / (benchmark.p90 * 0.5))))

    # Linear interpolation between known points
    for i in range(len(percentiles) - 1):
        low_pct, low_val = percentiles[i]
        high_pct, high_val = percentiles[i + 1]

        if low_val <= client_value <= high_val:
            ratio = (client_value - low_val) / (high_val - low_val) if high_val != low_val else 0.5
            return int(low_pct + ratio * (high_pct - low_pct))

    return 50  # Default to median if calculation fails
```

### 4.2 Threshold Status Adjustment

The benchmark comparison informs threshold status classification:

| Percentile Range | Position Label | Threshold Adjustment |
|------------------|----------------|----------------------|
| 90-100 | Excellent | Above threshold |
| 75-89 | Above Average | Above threshold |
| 50-74 | Average | At threshold |
| 25-49 | Below Average | At threshold |
| 10-24 | Lower Quartile | Below threshold |
| 0-9 | Bottom Decile | Below threshold |

**Note:** Some ratios have inverted interpretation (e.g., Debt-to-Equity where lower is better).

### 4.3 Ratio Direction Mapping

```python
RATIO_DIRECTION = {
    # Higher is better
    "current_ratio": "higher_better",
    "quick_ratio": "higher_better",
    "gross_margin": "higher_better",
    "net_profit_margin": "higher_better",
    "operating_margin": "higher_better",
    "roa": "higher_better",
    "roe": "higher_better",
    "inventory_turnover": "higher_better",
    "receivables_turnover": "higher_better",
    "asset_turnover": "higher_better",

    # Lower is better
    "debt_to_equity": "lower_better",
    "days_sales_outstanding": "lower_better",
    "days_inventory_outstanding": "lower_better",
}
```

### 4.4 Interpretation Generation

```python
def generate_interpretation(
    comparison: BenchmarkComparison,
    ratio_direction: str
) -> str:
    """
    Generate human-readable interpretation of benchmark comparison.
    """
    pct = comparison.percentile
    industry = comparison.industry.value.replace("_", " ").title()

    if ratio_direction == "higher_better":
        if pct >= 75:
            return f"Strong performance: Ranks in top quartile of {industry} companies."
        elif pct >= 50:
            return f"Solid performance: Above median for {industry} sector."
        elif pct >= 25:
            return f"Below average: Lower half of {industry} benchmarks."
        else:
            return f"Underperforming: Bottom quartile for {industry}. Review recommended."
    else:  # lower_better
        if pct <= 25:
            return f"Strong position: Lower (better) than 75% of {industry} companies."
        elif pct <= 50:
            return f"Solid position: Below median for {industry} sector."
        elif pct <= 75:
            return f"Elevated: Higher than average for {industry}."
        else:
            return f"High exposure: Top quartile risk level for {industry}. Review recommended."
```

---

## 5. Zero-Storage Compliance

### 5.1 Benchmark Data Classification

Benchmark data is classified as **Reference Data**, not Client Data:

| Data Type | Classification | Storage | Rationale |
|-----------|---------------|---------|-----------|
| Industry Benchmarks | Reference | Persistent | Publicly available aggregate data |
| Percentile Tables | Reference | Persistent | Derived from public sources |
| Client Ratios | Client Data | Session-only | Zero-Storage policy applies |
| Comparison Results | Derived | Session-only | Combines client + reference |

### 5.2 Compliance Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    BENCHMARK FRAMEWORK                       │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌──────────────────┐      ┌──────────────────────────┐     │
│  │  REFERENCE DATA  │      │     CLIENT SESSION       │     │
│  │  (Persistent)    │      │     (Memory Only)        │     │
│  ├──────────────────┤      ├──────────────────────────┤     │
│  │ • Industry       │  +   │ • Uploaded Trial Balance │     │
│  │   Benchmarks     │──────│ • Calculated Ratios      │     │
│  │ • Percentile     │      │ • Comparison Results     │     │
│  │   Tables         │      │                          │     │
│  │ • Source         │      │ [Cleared on session end] │     │
│  │   Attribution    │      │                          │     │
│  └──────────────────┘      └──────────────────────────┘     │
│                                                              │
│  ✓ No client data persisted                                 │
│  ✓ Benchmarks are public aggregate data                     │
│  ✓ Comparisons computed in real-time, not stored            │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 Data Handling Rules

1. **Benchmark Loading:** Pre-loaded at application startup or lazy-loaded per industry
2. **Comparison Computation:** Real-time, in-memory only
3. **Result Display:** Rendered to UI, never persisted
4. **Audit Trail:** Only logs that benchmark was used, not client values

---

## 6. API Design

### 6.1 Benchmark Endpoints

```python
# GET /benchmarks/{industry}
# Returns benchmark set for an industry
@router.get("/benchmarks/{industry}")
async def get_industry_benchmarks(
    industry: IndustryType,
    fiscal_year: Optional[int] = None
) -> BenchmarkSet:
    """
    Retrieve industry benchmark data.

    Public reference data - no authentication required.
    """
    pass


# POST /benchmarks/compare
# Compare client ratios to benchmarks
@router.post("/benchmarks/compare")
async def compare_to_benchmarks(
    ratios: Dict[str, float],
    industry: IndustryType,
    token: str = Depends(get_current_user)
) -> List[BenchmarkComparison]:
    """
    Compare calculated ratios to industry benchmarks.

    - Ratios computed from client trial balance (session data)
    - Comparison is ephemeral (not stored)
    - Returns percentile rankings and interpretations
    """
    pass


# GET /benchmarks/sources
# Returns data source attribution
@router.get("/benchmarks/sources")
async def get_benchmark_sources() -> Dict[str, Any]:
    """
    Retrieve benchmark data source information.

    Includes attribution, update dates, and data quality scores.
    """
    pass
```

### 6.2 Response Models

```python
class BenchmarkComparisonResponse(BaseModel):
    """API response for benchmark comparison."""
    industry: str
    fiscal_year: int
    comparisons: List[BenchmarkComparison]
    overall_score: float          # Composite percentile score
    overall_health: str           # "upper_quartile", "mid_range", "lower_quartile"
    source_attribution: str
    generated_at: datetime

    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

---

## 7. Frontend Integration

### 7.1 BenchmarkCard Component

```tsx
interface BenchmarkCardProps {
  ratioName: string;
  clientValue: number;
  comparison: BenchmarkComparison;
}

function BenchmarkCard({ ratioName, clientValue, comparison }: BenchmarkCardProps) {
  return (
    <div className="bg-obsidian-800 rounded-xl p-4 border border-obsidian-600">
      {/* Ratio Name */}
      <h4 className="font-serif text-oatmeal-200">{ratioName}</h4>

      {/* Client Value */}
      <div className="font-mono text-2xl text-oatmeal-100">
        {formatRatio(clientValue)}
      </div>

      {/* Percentile Bar */}
      <div className="mt-3">
        <PercentileBar percentile={comparison.percentile} />
      </div>

      {/* Interpretation */}
      <p className="mt-2 text-sm text-oatmeal-400">
        {comparison.interpretation}
      </p>

      {/* Source Attribution */}
      <p className="mt-1 text-xs text-oatmeal-600">
        Source: {comparison.benchmark.source}
      </p>
    </div>
  );
}
```

### 7.2 PercentileBar Component

```tsx
interface PercentileBarProps {
  percentile: number;
  showLabels?: boolean;
}

function PercentileBar({ percentile, showLabels = true }: PercentileBarProps) {
  const getColor = (pct: number) => {
    if (pct >= 75) return 'bg-sage-500';
    if (pct >= 50) return 'bg-oatmeal-500';
    if (pct >= 25) return 'bg-oatmeal-600';
    return 'bg-clay-500';
  };

  return (
    <div className="relative">
      {/* Track */}
      <div className="h-2 bg-obsidian-700 rounded-full">
        {/* Quartile markers */}
        <div className="absolute left-1/4 h-2 w-px bg-obsidian-500" />
        <div className="absolute left-1/2 h-2 w-px bg-obsidian-500" />
        <div className="absolute left-3/4 h-2 w-px bg-obsidian-500" />
      </div>

      {/* Indicator */}
      <div
        className={`absolute top-0 w-3 h-3 rounded-full ${getColor(percentile)} -mt-0.5`}
        style={{ left: `calc(${percentile}% - 6px)` }}
      />

      {/* Labels */}
      {showLabels && (
        <div className="flex justify-between mt-1 text-xs text-oatmeal-600">
          <span>0</span>
          <span>25</span>
          <span>50</span>
          <span>75</span>
          <span>100</span>
        </div>
      )}
    </div>
  );
}
```

---

## 8. Phase III Implementation Roadmap

### 8.1 Sprint Sequence

| Sprint | Focus | Deliverables |
|--------|-------|--------------|
| 41 | Benchmark Schema | Python models, database schema (if needed) |
| 42 | Static Benchmark Data | Curated benchmark tables for 6 priority industries |
| 43 | Comparison Engine | `benchmark_engine.py` with percentile calculation |
| 44 | API Integration | `/benchmarks/*` endpoints |
| 45 | Frontend Components | BenchmarkCard, PercentileBar, BenchmarkSection |
| 46 | Testing & Refinement | Unit tests, integration tests, UX polish |
| 47 | Data Pipeline (Optional) | SEC EDGAR aggregation, FRED integration |

### 8.2 Priority Industries

Initial benchmark coverage (Phase III Tier 1):

1. **Retail** - High volume, clear benchmarks
2. **Manufacturing** - Inventory-focused metrics
3. **Professional Services** - Service margin focus
4. **Technology** - R&D and growth metrics
5. **Healthcare** - Regulated sector benchmarks
6. **Financial Services** - Capital ratio focus

### 8.3 Success Metrics

| Metric | Target |
|--------|--------|
| Industry Coverage | 6+ industries at launch |
| Ratio Coverage | 17 core ratios benchmarked |
| Data Currency | Benchmarks within 2 years |
| Percentile Accuracy | ±5 percentile points |
| User Adoption | 50% of diagnostic sessions use benchmarks |

---

## 9. Risks and Mitigations

### 9.1 Data Quality Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Stale benchmark data | Misleading comparisons | Annual update process, date display |
| Sample size too small | Unreliable percentiles | Minimum sample threshold, warnings |
| Industry misclassification | Wrong benchmarks applied | User confirmation of industry |
| Source discontinuation | No updates | Multiple source strategy |

### 9.2 Technical Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Performance overhead | Slow comparisons | Lazy loading, caching |
| Data licensing issues | Legal exposure | Public data priority, clear attribution |
| Calculation errors | Bad advice | Comprehensive test suite |

### 9.3 User Experience Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| Over-reliance on benchmarks | Missed context | Clear disclaimers, professional judgment emphasis |
| Benchmark confusion | User frustration | Tooltips, help documentation |
| Information overload | Decision paralysis | Progressive disclosure |

---

## 10. Open Questions

1. **Benchmark Granularity:** Should we support sub-industry benchmarks (e.g., "Retail - Apparel" vs "Retail - Grocery")?

2. **Regional Benchmarks:** Should benchmarks vary by geography (US vs EU vs UK)?

3. **Size-Based Benchmarks:** Should we segment by company size (revenue bands)?

4. **Historical Trends:** Should we show benchmark trend over time (e.g., "Current ratio median has declined 5% YoY")?

5. **Custom Benchmarks:** Should users be able to define custom benchmark sets?

---

## 11. Appendix

### A. Sample Benchmark Data (Illustrative)

```json
{
  "industry": "retail",
  "fiscal_year": 2025,
  "benchmarks": {
    "current_ratio": {
      "p10": 0.95,
      "p25": 1.25,
      "p50": 1.65,
      "p75": 2.10,
      "p90": 2.85,
      "mean": 1.72,
      "std_dev": 0.65,
      "sample_size": 1250,
      "source": "RMA Annual Statement Studies"
    },
    "gross_margin": {
      "p10": 0.18,
      "p25": 0.25,
      "p50": 0.32,
      "p75": 0.42,
      "p90": 0.55,
      "mean": 0.33,
      "std_dev": 0.12,
      "sample_size": 1250,
      "source": "RMA Annual Statement Studies"
    }
  }
}
```

### B. Source Attribution Template

```
Benchmark data sourced from [SOURCE NAME], [YEAR].
Sample size: [N] companies in [INDUSTRY] sector.
Data represents [FISCAL_YEAR] fiscal year results.
Last updated: [DATE].

This data is provided for informational purposes only.
Actual industry conditions may vary.
```

### C. Disclaimer Text (UI)

> **Benchmark Comparison Notice**
>
> Industry benchmarks represent aggregate data from public sources and may not reflect your specific market segment, company size, or regional conditions. Benchmark comparisons are intended to provide context, not definitive guidance. Professional judgment should always be applied when interpreting financial metrics.

---

## Revision History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0.0 | 2026-02-04 | Sprint 40 | Initial RFC |

---

*End of RFC*
