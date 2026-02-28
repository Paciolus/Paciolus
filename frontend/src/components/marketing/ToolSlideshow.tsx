'use client'

import { useState, useCallback, useEffect, useRef } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'
import { VIEWPORT } from '@/utils/marketingMotion'

/**
 * ToolSlideshow — Sprint 449
 *
 * Full-screen animated slideshow replacing the ToolShowcase grid.
 * Each of the 12 tools gets a dedicated slide with:
 * - Tool identity (icon, title, tier, cluster)
 * - Extended value proposition copy
 * - Rich mock preview of the tool's output (PDF memo / data table style)
 * - Key capabilities list
 * - Standards referenced
 * - CTA to try the tool
 *
 * Navigation: left/right arrows + clickable dot indicators + keyboard arrows.
 * Framer-motion AnimatePresence for smooth horizontal slide transitions.
 */

// ── Types ────────────────────────────────────────────────────────────

type ToolTier = 'solo' | 'team'

interface MockTest {
  name: string
  status: 'pass' | 'flag' | 'skip'
}

interface MockMetric {
  label: string
  value: string
  accent?: 'sage' | 'clay' | 'oatmeal'
}

interface ToolSlide {
  title: string
  shortTitle: string
  description: string
  valueProposition: string
  href: string
  icon: BrandIconName
  tier: ToolTier
  cluster: string
  tests?: number
  standards: string[]
  capabilities: string[]
  mockTests: MockTest[]
  mockMetrics: MockMetric[]
  mockMemoTitle: string
  mockMemoStandard: string
}

// ── Tool Data ────────────────────────────────────────────────────────

const TOOLS: ToolSlide[] = [
  {
    title: 'Trial Balance Diagnostics',
    shortTitle: 'TB Diagnostics',
    description: 'Anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.',
    valueProposition: 'Upload a trial balance and receive a complete diagnostic workup in under three seconds. Twelve financial ratios, automated account classification, anomaly flagging, and full financial statement generation — all from a single file upload. The foundation of every engagement.',
    href: '/tools/trial-balance',
    icon: 'calculator',
    tier: 'solo',
    cluster: 'Analyze',
    standards: ['ISA 520', 'ISA 315', 'IAS 1'],
    capabilities: ['12 financial ratios', 'A-Z lead sheet mapping', 'Balance sheet & income statement', 'Anomaly detection engine', 'Classification validator'],
    mockTests: [
      { name: 'Balance Sheet Equilibrium', status: 'pass' },
      { name: 'Suspense Account Detection', status: 'flag' },
      { name: 'Sign Anomaly Check', status: 'pass' },
      { name: 'Duplicate Account Scan', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Current Ratio', value: '1.82', accent: 'sage' },
      { label: 'Accounts Analyzed', value: '47' },
      { label: 'Anomalies Flagged', value: '3', accent: 'clay' },
    ],
    mockMemoTitle: 'Trial Balance Diagnostic Report',
    mockMemoStandard: 'ISA 520 — Analytical Procedures',
  },
  {
    title: 'Multi-Period Comparison',
    shortTitle: 'Multi-Period',
    description: 'Compare up to three periods side-by-side with variance analysis and budget tracking.',
    valueProposition: 'Place two or three trial balance periods side by side and instantly surface account movements, significant variances, and budget deviations. Reclassification detection highlights accounts that shifted between periods — critical for identifying misstatement risk before fieldwork begins.',
    href: '/tools/multi-period',
    icon: 'trend-chart',
    tier: 'solo',
    cluster: 'Analyze',
    standards: ['ISA 520', 'ISA 315'],
    capabilities: ['2-way & 3-way comparison', 'Budget variance analysis', 'Reclassification detection', 'Material movement flags', 'Period-over-period trends'],
    mockTests: [
      { name: 'Material Movement Detection', status: 'flag' },
      { name: 'Reclassification Analysis', status: 'pass' },
      { name: 'New Account Detection', status: 'pass' },
      { name: 'Budget Variance Threshold', status: 'flag' },
    ],
    mockMetrics: [
      { label: 'Periods Compared', value: '3' },
      { label: 'Material Movements', value: '8', accent: 'clay' },
      { label: 'Variance > 10%', value: '12', accent: 'oatmeal' },
    ],
    mockMemoTitle: 'Multi-Period Comparison Memo',
    mockMemoStandard: 'ISA 520 — Analytical Procedures',
  },
  {
    title: 'Journal Entry Testing',
    shortTitle: 'JE Testing',
    description: "Benford's Law, structural validation, and statistical anomaly detection across the GL.",
    valueProposition: "Upload your general ledger extract and run a 19-test battery that covers everything from Benford's Law digit distribution to weekend/holiday posting detection. Stratified sampling isolates high-risk entries for focused review. Every flagged item traces to a specific ISA or PCAOB standard.",
    href: '/tools/journal-entry-testing',
    icon: 'shield-check',
    tier: 'solo',
    cluster: 'Detect',
    tests: 19,
    standards: ['ISA 240', 'ISA 240.A40', 'PCAOB AS 2401', 'ISA 530'],
    capabilities: ["Benford's Law analysis", 'Weekend & holiday posting', 'Round number concentration', 'Stratified sampling (ISA 530)', 'Duplicate entry detection'],
    mockTests: [
      { name: "Benford's Law Analysis", status: 'pass' },
      { name: 'Weekend / Holiday Posting', status: 'flag' },
      { name: 'Round Number Concentration', status: 'pass' },
      { name: 'Top-Strata Sampling', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Tests Passed', value: '16 / 19', accent: 'sage' },
      { label: 'Flagged Items', value: '3', accent: 'oatmeal' },
      { label: 'Risk Level', value: 'Low', accent: 'sage' },
    ],
    mockMemoTitle: 'Journal Entry Testing Memo',
    mockMemoStandard: 'ISA 240 / PCAOB AS 2401',
  },
  {
    title: 'Revenue Testing',
    shortTitle: 'Revenue',
    description: 'ISA 240 fraud risk plus ASC 606 / IFRS 15 recognition timing and cut-off analysis.',
    valueProposition: 'Revenue recognition is the highest fraud risk area on every engagement. Run 16 automated tests covering recognition timing, cut-off analysis, and contract mechanics. Optional ASC 606 / IFRS 15 contract columns unlock four additional tests — SSP allocation, obligation linkage, modification treatment, and recognition timing.',
    href: '/tools/revenue-testing',
    icon: 'currency-circle',
    tier: 'solo',
    cluster: 'Detect',
    tests: 16,
    standards: ['ISA 240', 'ASC 606', 'IFRS 15', 'ISA 240.A32'],
    capabilities: ['Recognition timing analysis', 'Cut-off risk detection', 'Contract-aware testing (optional)', 'SSP allocation validation', 'Fraud risk indicators'],
    mockTests: [
      { name: 'Recognition Timing', status: 'pass' },
      { name: 'Cut-off Analysis', status: 'flag' },
      { name: 'Revenue Concentration', status: 'pass' },
      { name: 'SSP Allocation', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Tests Passed', value: '14 / 16', accent: 'sage' },
      { label: 'Cut-off Items', value: '2', accent: 'clay' },
      { label: 'Contract Tests', value: '4 / 4', accent: 'sage' },
    ],
    mockMemoTitle: 'Revenue Testing Memo',
    mockMemoStandard: 'ISA 240 / ASC 606 / IFRS 15',
  },
  {
    title: 'AP Payment Testing',
    shortTitle: 'AP Testing',
    description: 'Duplicate detection, vendor concentration, and fraud indicators across payables.',
    valueProposition: 'Upload your AP payment register and surface duplicate payments, vendor concentration risks, and fraud indicators across 13 automated tests. Pattern matching catches near-duplicates that manual review misses — same vendor, same amount, different dates. Every finding maps to a specific PCAOB standard.',
    href: '/tools/ap-testing',
    icon: 'document-duplicate',
    tier: 'solo',
    cluster: 'Validate',
    tests: 13,
    standards: ['PCAOB AS 2401', 'ISA 240', 'ISA 500'],
    capabilities: ['Duplicate payment detection', 'Vendor concentration analysis', 'Round number patterns', 'Unusual timing flags', 'Fraud indicator scoring'],
    mockTests: [
      { name: 'Duplicate Payment Scan', status: 'flag' },
      { name: 'Vendor Concentration', status: 'pass' },
      { name: 'Round Number Analysis', status: 'pass' },
      { name: 'Timing Anomaly Detection', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Tests Passed', value: '11 / 13', accent: 'sage' },
      { label: 'Duplicate Pairs', value: '4', accent: 'clay' },
      { label: 'Top Vendor %', value: '23%', accent: 'oatmeal' },
    ],
    mockMemoTitle: 'AP Payment Testing Memo',
    mockMemoStandard: 'PCAOB AS 2401 — Fraud Risk',
  },
  {
    title: 'Bank Reconciliation',
    shortTitle: 'Bank Rec',
    description: 'Match bank transactions against the general ledger with automated reconciliation.',
    valueProposition: 'Upload both your bank statement and GL cash detail. The matching engine reconciles transactions by exact amount, auto-categorizes unmatched items, and produces a reconciliation bridge. Dual-file ingestion means no manual cross-referencing — the platform does the heavy lifting.',
    href: '/tools/bank-rec',
    icon: 'arrows-vertical',
    tier: 'solo',
    cluster: 'Validate',
    standards: ['ISA 500', 'ISA 505'],
    capabilities: ['Exact amount matching', 'Auto-categorization', 'Reconciliation bridge', 'Dual-file ingestion', 'Unmatched item flagging'],
    mockTests: [
      { name: 'Exact Match Analysis', status: 'pass' },
      { name: 'Timing Difference Check', status: 'pass' },
      { name: 'Outstanding Items', status: 'flag' },
      { name: 'Reconciliation Balance', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Match Rate', value: '94.2%', accent: 'sage' },
      { label: 'Unmatched', value: '12', accent: 'oatmeal' },
      { label: 'Bridge Balance', value: '$0.00', accent: 'sage' },
    ],
    mockMemoTitle: 'Bank Reconciliation Memo',
    mockMemoStandard: 'ISA 500 / ISA 505',
  },
  {
    title: 'Statistical Sampling',
    shortTitle: 'Sampling',
    description: 'ISA 530 / PCAOB AS 2315 compliant MUS and random sampling with Stringer bounds.',
    valueProposition: 'Design your sample using ISA 530-compliant parameters, then evaluate results with Stringer bound analysis. Two-phase workflow mirrors audit methodology — design and select first, evaluate exceptions second. Supports both monetary unit sampling (MUS) and random selection with 2-tier stratification.',
    href: '/tools/statistical-sampling',
    icon: 'bar-chart',
    tier: 'team',
    cluster: 'Analyze',
    standards: ['ISA 530', 'PCAOB AS 2315'],
    capabilities: ['Monetary unit sampling (MUS)', 'Random sampling', '2-tier stratification', 'Stringer bound evaluation', 'Two-phase workflow'],
    mockTests: [
      { name: 'Sample Size Adequacy', status: 'pass' },
      { name: 'Stratification Coverage', status: 'pass' },
      { name: 'Stringer Bound Evaluation', status: 'pass' },
      { name: 'Exception Rate Threshold', status: 'flag' },
    ],
    mockMetrics: [
      { label: 'Sample Size', value: '58', accent: 'sage' },
      { label: 'Exceptions Found', value: '2', accent: 'oatmeal' },
      { label: 'Conclusion', value: 'Pass', accent: 'sage' },
    ],
    mockMemoTitle: 'Statistical Sampling Design Memo',
    mockMemoStandard: 'ISA 530 / PCAOB AS 2315',
  },
  {
    title: 'Payroll Testing',
    shortTitle: 'Payroll',
    description: 'Ghost employee detection, duplicate payments, and payroll anomaly analysis.',
    valueProposition: 'Upload your payroll register and detect ghost employees, duplicate payments, and statistical anomalies across 11 automated tests. Pattern analysis surfaces employees with identical bank details, addresses, or tax identifiers — the most common indicators of payroll fraud schemes.',
    href: '/tools/payroll-testing',
    icon: 'users',
    tier: 'team',
    cluster: 'Detect',
    tests: 11,
    standards: ['ISA 240', 'PCAOB AS 2401'],
    capabilities: ['Ghost employee detection', 'Duplicate payment analysis', 'Shared bank detail flags', 'Statistical outlier detection', 'Address clustering'],
    mockTests: [
      { name: 'Ghost Employee Detection', status: 'pass' },
      { name: 'Duplicate Payment Scan', status: 'pass' },
      { name: 'Shared Bank Details', status: 'flag' },
      { name: 'Compensation Outliers', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Tests Passed', value: '9 / 11', accent: 'sage' },
      { label: 'Employees Flagged', value: '5', accent: 'oatmeal' },
      { label: 'Risk Level', value: 'Medium', accent: 'oatmeal' },
    ],
    mockMemoTitle: 'Payroll Testing Memo',
    mockMemoStandard: 'ISA 240 / PCAOB AS 2401',
  },
  {
    title: 'Three-Way Match',
    shortTitle: '3-Way Match',
    description: 'PO-Invoice-Receipt matching with exact PO# linkage and procurement variance analysis.',
    valueProposition: 'Upload purchase orders, invoices, and receiving reports. The matching engine links records by exact PO number with fuzzy fallback, then quantifies variances between authorized, billed, and received amounts. Exception reporting highlights procurement integrity failures that require investigation.',
    href: '/tools/three-way-match',
    icon: 'circle-check',
    tier: 'team',
    cluster: 'Validate',
    standards: ['ISA 500', 'PCAOB AS 2401'],
    capabilities: ['Exact PO# linkage', 'Fuzzy match fallback', 'Variance quantification', 'Exception reporting', 'Procurement integrity'],
    mockTests: [
      { name: 'PO-Invoice Match', status: 'pass' },
      { name: 'Invoice-Receipt Match', status: 'pass' },
      { name: 'Three-Way Variance', status: 'flag' },
      { name: 'Unmatched Document Scan', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Match Rate', value: '91.7%', accent: 'sage' },
      { label: 'Exceptions', value: '6', accent: 'clay' },
      { label: 'Total Variance', value: '$4,210', accent: 'oatmeal' },
    ],
    mockMemoTitle: 'Three-Way Match Memo',
    mockMemoStandard: 'ISA 500 — Audit Evidence',
  },
  {
    title: 'AR Aging Analysis',
    shortTitle: 'AR Aging',
    description: 'Receivables aging with concentration risk, stale balances, and allowance adequacy.',
    valueProposition: 'Analyze receivables aging across 11 automated tests. Surface concentration risk in your customer base, identify stale balances requiring write-off evaluation, and assess allowance adequacy. Optional sub-ledger upload enables granular customer-level analysis alongside TB-level diagnostics.',
    href: '/tools/ar-aging',
    icon: 'clock',
    tier: 'team',
    cluster: 'Assess',
    tests: 11,
    standards: ['ISA 540', 'ISA 500', 'ASC 326'],
    capabilities: ['Aging bucket analysis', 'Concentration risk detection', 'Stale balance identification', 'Allowance adequacy assessment', 'Dual-input (TB + sub-ledger)'],
    mockTests: [
      { name: 'Aging Distribution', status: 'pass' },
      { name: 'Customer Concentration', status: 'flag' },
      { name: 'Stale Balance Detection', status: 'pass' },
      { name: 'Allowance Adequacy', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Tests Passed', value: '9 / 11', accent: 'sage' },
      { label: 'Over 90 Days', value: '$42,100', accent: 'clay' },
      { label: 'Concentration', value: '34%', accent: 'oatmeal' },
    ],
    mockMemoTitle: 'AR Aging Analysis Memo',
    mockMemoStandard: 'ISA 540 / ASC 326',
  },
  {
    title: 'Fixed Asset Testing',
    shortTitle: 'Fixed Assets',
    description: 'PP&E depreciation, useful life, and residual value anomaly detection per IAS 16.',
    valueProposition: 'Upload your fixed asset register and run 9 automated tests covering depreciation accuracy, useful life reasonableness, and residual value anomalies. Pattern analysis catches assets with inconsistent depreciation methods, unusual capitalizations, and items that should have been fully depreciated but carry remaining book value.',
    href: '/tools/fixed-assets',
    icon: 'building',
    tier: 'team',
    cluster: 'Assess',
    tests: 9,
    standards: ['IAS 16', 'ASC 360', 'ISA 540'],
    capabilities: ['Depreciation accuracy check', 'Useful life analysis', 'Residual value anomalies', 'Capitalization threshold test', 'Fully depreciated asset scan'],
    mockTests: [
      { name: 'Depreciation Accuracy', status: 'pass' },
      { name: 'Useful Life Outliers', status: 'flag' },
      { name: 'Residual Value Check', status: 'pass' },
      { name: 'Capitalization Threshold', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Tests Passed', value: '7 / 9', accent: 'sage' },
      { label: 'Assets Flagged', value: '8', accent: 'oatmeal' },
      { label: 'Total PP&E', value: '$1.2M' },
    ],
    mockMemoTitle: 'Fixed Asset Testing Memo',
    mockMemoStandard: 'IAS 16 / ASC 360',
  },
  {
    title: 'Inventory Testing',
    shortTitle: 'Inventory',
    description: 'Unit cost outliers, slow-moving detection, and valuation anomalies per IAS 2.',
    valueProposition: 'Analyze your inventory register for valuation anomalies, slow-moving items, and obsolescence indicators across 9 automated tests. Unit cost outlier detection surfaces items priced significantly above or below category averages. Slow-moving analysis identifies carrying risk — the items most likely to require write-down.',
    href: '/tools/inventory-testing',
    icon: 'cube',
    tier: 'team',
    cluster: 'Assess',
    tests: 9,
    standards: ['IAS 2', 'ASC 330', 'ISA 501'],
    capabilities: ['Unit cost outlier detection', 'Slow-moving inventory flags', 'Obsolescence indicators', 'Valuation anomaly detection', 'NRV assessment signals'],
    mockTests: [
      { name: 'Unit Cost Outliers', status: 'flag' },
      { name: 'Slow-Moving Detection', status: 'pass' },
      { name: 'Obsolescence Indicators', status: 'pass' },
      { name: 'Valuation Consistency', status: 'pass' },
    ],
    mockMetrics: [
      { label: 'Tests Passed', value: '7 / 9', accent: 'sage' },
      { label: 'Items Flagged', value: '14', accent: 'clay' },
      { label: 'Slow-Moving %', value: '11%', accent: 'oatmeal' },
    ],
    mockMemoTitle: 'Inventory Testing Memo',
    mockMemoStandard: 'IAS 2 / ASC 330',
  },
]

// ── Animation Variants ───────────────────────────────────────────────

const slideVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 400 : -400,
    opacity: 0,
    scale: 0.95,
  }),
  center: {
    x: 0,
    opacity: 1,
    scale: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 400 : -400,
    opacity: 0,
    scale: 0.95,
  }),
}

const slideTransition = {
  x: { type: 'spring' as const, stiffness: 300, damping: 30 },
  opacity: { duration: 0.3 },
  scale: { duration: 0.3 },
}

// ── Mock Preview Component ───────────────────────────────────────────

function MockPreview({ tool }: { tool: ToolSlide }) {
  const isSolo = tool.tier === 'solo'

  return (
    <div className="rounded-2xl border border-obsidian-500/25 bg-obsidian-800/60 backdrop-blur-sm overflow-hidden">
      {/* Mock window chrome */}
      <div className="flex items-center gap-3 px-5 py-3 border-b border-obsidian-500/20 bg-obsidian-800/80">
        <div className="flex gap-1.5">
          <div className="w-2.5 h-2.5 rounded-full bg-clay-500/50" />
          <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-400/30" />
          <div className="w-2.5 h-2.5 rounded-full bg-sage-500/40" />
        </div>
        <span className="font-mono text-[11px] text-oatmeal-600">
          {tool.mockMemoTitle} — {tool.mockMemoStandard}
        </span>
        <div className="ml-auto flex items-center gap-2">
          <span className={`
            font-sans text-[9px] uppercase tracking-widest px-2 py-0.5 rounded border
            ${isSolo
              ? 'text-sage-500/70 bg-sage-500/10 border-sage-500/20'
              : 'text-oatmeal-400/70 bg-oatmeal-400/8 border-oatmeal-400/20'
            }
          `}>
            PDF Export
          </span>
        </div>
      </div>

      {/* Mock content */}
      <div className="px-5 py-4 grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Test Battery Column */}
        <div>
          <p className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700 mb-2.5">
            Key Capabilities
          </p>
          <div className="space-y-2">
            {tool.mockTests.map((test) => (
              <div key={test.name} className="flex items-center gap-2">
                <div className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                  test.status === 'pass' ? 'bg-sage-500' :
                  test.status === 'flag' ? 'bg-oatmeal-400' :
                  'bg-obsidian-500'
                }`} />
                <span className="font-sans text-[10px] text-oatmeal-500 leading-snug">
                  {test.name}
                </span>
              </div>
            ))}
          </div>
        </div>

        {/* Standards Column */}
        <div>
          <p className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700 mb-2.5">
            Standards Cited
          </p>
          <div className="space-y-2">
            {tool.standards.map((s) => (
              <div key={s} className="flex items-start gap-1.5">
                <span className="font-sans text-[10px] text-oatmeal-600 leading-snug">{s}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Summary Column */}
        <div>
          <p className="font-sans text-[9px] uppercase tracking-widest text-oatmeal-700 mb-2.5">
            Summary
          </p>
          <div className="space-y-2.5">
            {tool.mockMetrics.map((metric) => (
              <div key={metric.label} className="flex justify-between items-baseline">
                <span className="font-sans text-[10px] text-oatmeal-600">{metric.label}</span>
                <span className={`font-mono text-xs tabular-nums ${
                  metric.accent === 'sage' ? 'text-sage-400' :
                  metric.accent === 'clay' ? 'text-clay-400' :
                  metric.accent === 'oatmeal' ? 'text-oatmeal-300' :
                  'text-oatmeal-300'
                }`}>
                  {metric.value}
                </span>
              </div>
            ))}
          </div>
          <p className="font-sans text-[9px] text-oatmeal-700 italic mt-3 leading-snug">
            Synthetic data — no client information stored
          </p>
        </div>
      </div>
    </div>
  )
}

// ── Slide Content ────────────────────────────────────────────────────

function SlideContent({ tool }: { tool: ToolSlide }) {
  const isSolo = tool.tier === 'solo'

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 lg:gap-12 items-start">
      {/* Left: Tool Identity + Value Proposition */}
      <div className="space-y-6">
        {/* Header */}
        <div>
          <div className="flex items-center gap-3 mb-4">
            <div className={`
              w-12 h-12 rounded-xl flex items-center justify-center shrink-0
              ${isSolo
                ? 'bg-sage-500/15 text-sage-400 border border-sage-500/25'
                : 'bg-oatmeal-400/10 text-oatmeal-400 border border-oatmeal-400/20'
              }
            `}>
              <BrandIcon name={tool.icon} className="w-6 h-6" />
            </div>
            <div>
              <div className="flex items-center gap-2.5">
                <h3 className="font-serif text-2xl text-oatmeal-100">
                  {tool.title}
                </h3>
                <span className={`
                  px-2 py-0.5 rounded text-[9px] uppercase tracking-wider
                  font-sans font-semibold border shrink-0
                  ${isSolo
                    ? 'bg-sage-500/10 text-sage-400 border-sage-500/25'
                    : 'bg-oatmeal-400/8 text-oatmeal-500 border-oatmeal-400/20'
                  }
                `}>
                  {isSolo ? 'Solo' : 'Team'}
                </span>
              </div>
              <div className="flex items-center gap-2 mt-1">
                <span className="font-sans text-[10px] uppercase tracking-widest text-oatmeal-600">
                  {tool.cluster}
                </span>
                {tool.tests && (
                  <>
                    <span className="text-obsidian-500 text-[10px]">·</span>
                    <span className="font-mono text-[10px] text-oatmeal-600">
                      {tool.tests} automated tests
                    </span>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Value Proposition */}
          <p className="font-sans text-sm text-oatmeal-400 leading-relaxed">
            {tool.valueProposition}
          </p>
        </div>

        {/* CTA */}
        <div className="flex items-center gap-3 pt-2">
          <Link
            href={tool.href}
            className={`
              group inline-flex items-center gap-2 px-6 py-2.5 rounded-xl font-sans text-sm font-medium transition-all
              ${isSolo
                ? 'bg-sage-600 text-white hover:bg-sage-500 shadow-lg shadow-sage-600/20'
                : 'bg-oatmeal-400/10 text-oatmeal-300 border border-oatmeal-400/25 hover:bg-oatmeal-400/15 hover:border-oatmeal-400/40'
              }
            `}
          >
            Try This Tool
            <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            href="/pricing"
            className="font-sans text-xs text-oatmeal-600 hover:text-oatmeal-400 transition-colors"
          >
            View pricing
          </Link>
        </div>
      </div>

      {/* Right: Mock Preview */}
      <div className="relative">
        {/* Subtle glow behind preview */}
        <div className={`absolute -inset-4 rounded-3xl blur-2xl opacity-20 pointer-events-none ${
          isSolo ? 'bg-sage-500/30' : 'bg-oatmeal-400/20'
        }`} />
        <div className="relative">
          <MockPreview tool={tool} />

          {/* Export badges */}
          <div className="flex items-center gap-2 mt-3 justify-end">
            <span className="font-sans text-[9px] text-oatmeal-700 uppercase tracking-widest">
              Exports as
            </span>
            <div className="flex gap-1.5">
              {['PDF', 'XLSX', 'CSV'].map((fmt) => (
                <span
                  key={fmt}
                  className="px-2 py-0.5 rounded bg-obsidian-800/50 border border-obsidian-500/20 font-mono text-[9px] text-oatmeal-500"
                >
                  {fmt}
                </span>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

// ── Navigation Arrows ────────────────────────────────────────────────

function NavArrow({
  direction,
  onClick,
  disabled,
}: {
  direction: 'left' | 'right'
  onClick: () => void
  disabled: boolean
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={direction === 'left' ? 'Previous tool' : 'Next tool'}
      className={`
        absolute top-1/2 -translate-y-1/2 z-20
        w-12 h-12 rounded-full flex items-center justify-center
        bg-obsidian-800/70 border border-obsidian-500/30
        text-oatmeal-400 backdrop-blur-sm
        transition-all duration-200
        ${disabled
          ? 'opacity-20 cursor-not-allowed'
          : 'hover:bg-obsidian-700/80 hover:border-obsidian-500/50 hover:text-oatmeal-200 hover:scale-105'
        }
        ${direction === 'left' ? 'left-0 lg:-left-6' : 'right-0 lg:-right-6'}
      `}
    >
      <svg
        className={`w-5 h-5 ${direction === 'right' ? '' : 'rotate-180'}`}
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        strokeWidth={2}
      >
        <path strokeLinecap="round" strokeLinejoin="round" d="M9 5l7 7-7 7" />
      </svg>
    </button>
  )
}

// ── Dot Indicators ───────────────────────────────────────────────────

function DotIndicators({
  total,
  current,
  onSelect,
}: {
  total: number
  current: number
  onSelect: (index: number) => void
}) {
  return (
    <div className="flex items-center justify-center gap-2" role="tablist" aria-label="Tool slides">
      {Array.from({ length: total }).map((_, i) => {
        const tool = TOOLS[i]
        const isActive = i === current
        const isSolo = tool?.tier === 'solo'

        return (
          <button
            key={i}
            role="tab"
            aria-selected={isActive}
            aria-label={tool?.shortTitle ?? `Tool ${i + 1}`}
            onClick={() => onSelect(i)}
            className="group relative p-1.5"
          >
            <div className={`
              rounded-full transition-all duration-300
              ${isActive
                ? `w-8 h-2.5 ${isSolo ? 'bg-sage-400' : 'bg-oatmeal-300'}`
                : 'w-2.5 h-2.5 bg-obsidian-500/60 group-hover:bg-obsidian-400/80'
              }
            `} />

            {/* Tooltip on hover */}
            <div className={`
              absolute bottom-full left-1/2 -translate-x-1/2 mb-2
              px-2.5 py-1 rounded-md bg-obsidian-900 border border-obsidian-500/30
              font-sans text-[10px] text-oatmeal-400 whitespace-nowrap
              opacity-0 group-hover:opacity-100 transition-opacity duration-200
              pointer-events-none
            `}>
              {tool?.shortTitle}
            </div>
          </button>
        )
      })}
    </div>
  )
}

// ── Main Export ───────────────────────────────────────────────────────

export function ToolSlideshow() {
  const [[activeIndex, direction], setSlide] = useState([0, 0])
  const containerRef = useRef<HTMLDivElement>(null)

  const paginate = useCallback((newDirection: number) => {
    setSlide(([prev]) => {
      const next = prev + newDirection
      if (next < 0 || next >= TOOLS.length) return [prev, 0]
      return [next, newDirection]
    })
  }, [])

  const goTo = useCallback((index: number) => {
    setSlide(([prev]) => [index, index > prev ? 1 : -1])
  }, [])

  // Keyboard navigation
  useEffect(() => {
    const handleKey = (e: KeyboardEvent) => {
      // Only respond if this section is somewhat visible
      if (!containerRef.current) return
      const rect = containerRef.current.getBoundingClientRect()
      if (rect.bottom < 0 || rect.top > window.innerHeight) return

      if (e.key === 'ArrowLeft') paginate(-1)
      if (e.key === 'ArrowRight') paginate(1)
    }
    window.addEventListener('keydown', handleKey)
    return () => window.removeEventListener('keydown', handleKey)
  }, [paginate])

  const tool = TOOLS[activeIndex] as ToolSlide

  return (
    <section
      ref={containerRef}
      id="tools"
      className="relative z-10 py-20 px-6"
    >
      <div className="max-w-7xl mx-auto">
        {/* Section Header */}
        <motion.div
          className="text-center mb-14"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-200 mb-3">
            Twelve Tools. One Platform.
          </h2>
          <p className="font-sans text-oatmeal-500 text-sm max-w-lg mx-auto">
            Twelve purpose-built tools. Explore each one to see exactly what you get.
          </p>
        </motion.div>

        {/* Slideshow Container */}
        <div className="relative">
          {/* Navigation Arrows */}
          <NavArrow
            direction="left"
            onClick={() => paginate(-1)}
            disabled={activeIndex === 0}
          />
          <NavArrow
            direction="right"
            onClick={() => paginate(1)}
            disabled={activeIndex === TOOLS.length - 1}
          />

          {/* Slide Area */}
          <div className="overflow-hidden px-4 lg:px-12">
            <AnimatePresence mode="wait" custom={direction}>
              <motion.div
                key={activeIndex}
                custom={direction}
                variants={slideVariants}
                initial="enter"
                animate="center"
                exit="exit"
                transition={slideTransition}
              >
                <SlideContent tool={tool} />
              </motion.div>
            </AnimatePresence>
          </div>
        </div>

        {/* Dot Indicators */}
        <div className="mt-10">
          <DotIndicators
            total={TOOLS.length}
            current={activeIndex}
            onSelect={goTo}
          />
        </div>

        {/* Counter */}
        <div className="flex items-center justify-center mt-4">
          <span className="font-mono text-xs text-oatmeal-600 tabular-nums">
            {String(activeIndex + 1).padStart(2, '0')} / {String(TOOLS.length).padStart(2, '0')}
          </span>
        </div>

        {/* Plan CTA Strip */}
        <motion.div
          className="mt-12 grid grid-cols-1 sm:grid-cols-2 gap-3"
          initial={{ opacity: 0, y: 16 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ delay: 0.2, duration: 0.5 }}
        >
          {/* Solo */}
          <Link
            href="/pricing"
            className="group flex items-center gap-4 p-5 rounded-xl border border-l-[3px] border-l-sage-500/50 transition-all duration-200 bg-sage-500/[0.06] border-obsidian-500/20 hover:bg-sage-500/10 hover:border-sage-500/30"
          >
            <div className="w-10 h-10 rounded-lg bg-sage-500/15 text-sage-400 flex items-center justify-center shrink-0 group-hover:bg-sage-500/25 transition-colors">
              <BrandIcon name="shield-check" className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-baseline gap-2 mb-0.5">
                <span className="font-serif text-base text-oatmeal-100">Solo</span>
                <span className="font-mono text-sm text-sage-400">
                  $50<span className="font-sans text-xs text-oatmeal-600">/mo</span>
                </span>
              </div>
              <p className="font-sans text-xs text-oatmeal-500 truncate">
                6 tools · 20 diagnostics/mo · PDF &amp; Excel export
              </p>
            </div>
            <div className="flex items-center gap-1 text-sage-500 group-hover:text-sage-400 shrink-0 transition-colors">
              <span className="font-sans text-xs whitespace-nowrap">Start 7-day trial</span>
              <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </Link>

          {/* Team */}
          <Link
            href="/pricing"
            className="group flex items-center gap-4 p-5 rounded-xl border border-l-[3px] border-l-oatmeal-400/40 transition-all duration-200 bg-oatmeal-400/[0.04] border-obsidian-500/20 hover:bg-oatmeal-400/[0.07] hover:border-oatmeal-400/25"
          >
            <div className="w-10 h-10 rounded-lg bg-oatmeal-400/10 text-oatmeal-400 flex items-center justify-center shrink-0 group-hover:bg-oatmeal-400/16 transition-colors">
              <BrandIcon name="users" className="w-5 h-5" />
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-0.5">
                <span className="font-serif text-base text-oatmeal-100">Team</span>
                <span className="font-mono text-sm text-oatmeal-300">
                  $130<span className="font-sans text-xs text-oatmeal-600">/mo</span>
                </span>
                <span className="px-1.5 py-0.5 rounded text-[9px] font-sans bg-oatmeal-400/15 text-oatmeal-400 border border-oatmeal-400/25">
                  Most popular
                </span>
              </div>
              <p className="font-sans text-xs text-oatmeal-500 truncate">
                All 12 tools · Unlimited diagnostics · Workspace · 3 seats
              </p>
            </div>
            <div className="flex items-center gap-1 text-oatmeal-500 group-hover:text-oatmeal-400 shrink-0 transition-colors">
              <span className="font-sans text-xs whitespace-nowrap">Start 7-day trial</span>
              <BrandIcon name="chevron-right" className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
            </div>
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
