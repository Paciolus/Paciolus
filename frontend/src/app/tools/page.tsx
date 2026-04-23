'use client'

/**
 * Tools Catalog Page — Sprint 579
 *
 * Browsable catalog of all 12+ diagnostic tools grouped by category.
 * Shows descriptions, ISA/PCAOB references, tier badges, and
 * favorite/pin controls. Serves as the central tool discovery page.
 */

import { useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { Reveal } from '@/components/ui/Reveal'
import { apiGet, apiPut } from '@/utils/apiClient'
import { fadeUp, staggerContainerTight } from '@/lib/motion'

/* ─── Types ─────────────────────────────────────────────────────────── */

interface UserPreferences {
  favorite_tools: string[]
}

type Category = 'Core Analysis' | 'Testing Suite' | 'Advanced'

interface ToolDef {
  key: string
  label: string
  href: string
  description: string
  reference: string
  category: Category
  testCount?: number
}

/* ─── Tool Definitions ──────────────────────────────────────────────── */

const TOOLS: ToolDef[] = [
  // Core Analysis
  { key: 'trial_balance', label: 'TB Diagnostics', href: '/tools/trial-balance', description: 'Upload a trial balance for streaming diagnostic analysis — ratio analysis, anomaly detection, benchmarks, and lead sheet generation.', reference: 'ISA 520 Analytical Procedures', category: 'Core Analysis' },
  { key: 'multi_period', label: 'Multi-Period Analysis', href: '/tools/multi-period', description: 'Compare trial balances across reporting periods to identify trends, anomalies, and period-over-period changes.', reference: 'ISA 520 Trend Analysis', category: 'Core Analysis' },
  { key: 'bank_reconciliation', label: 'Bank Reconciliation', href: '/tools/bank-rec', description: 'Match bank statement entries against book records to identify reconciling items and discrepancies.', reference: 'ISA 500 External Confirmation', category: 'Core Analysis' },
  { key: 'three_way_match', label: 'Three-Way Match', href: '/tools/three-way-match', description: 'Match purchase orders, receiving reports, and vendor invoices to detect procurement anomalies.', reference: 'ISA 500 Substantive Testing', category: 'Core Analysis' },
  // Testing Suite
  { key: 'journal_entry_testing', label: 'Journal Entry Testing', href: '/tools/journal-entry-testing', description: "Upload a General Ledger extract for automated testing — Benford's Law, structural validation, and statistical anomaly detection.", reference: 'ISA 240 / PCAOB AS 2401', category: 'Testing Suite', testCount: 19 },
  { key: 'ap_testing', label: 'AP Payment Testing', href: '/tools/ap-testing', description: 'Test AP payment registers for duplicate payments, vendor anomalies, ghost vendors, and fraud indicators.', reference: 'ISA 500 Substantive Testing', category: 'Testing Suite', testCount: 13 },
  { key: 'revenue_testing', label: 'Revenue Testing', href: '/tools/revenue-testing', description: 'Analyze revenue GL extracts for recognition anomalies per ISA 240, ASC 606, and IFRS 15 contract standards.', reference: 'ISA 240 / ASC 606 / IFRS 15', category: 'Testing Suite', testCount: 16 },
  { key: 'ar_aging', label: 'AR Aging', href: '/tools/ar-aging', description: 'Analyze accounts receivable aging schedules for collectibility risks, concentration, and unusual patterns.', reference: 'ISA 540 Accounting Estimates', category: 'Testing Suite', testCount: 11 },
  { key: 'payroll_testing', label: 'Payroll Testing', href: '/tools/payroll-testing', description: 'Test payroll registers for ghost employees, rate anomalies, overtime spikes, and segregation issues.', reference: 'ISA 240 Fraud Indicators', category: 'Testing Suite', testCount: 11 },
  { key: 'fixed_asset_testing', label: 'Fixed Assets', href: '/tools/fixed-assets', description: 'Test fixed asset registers for depreciation accuracy, impairment indicators, disposals, and lease indicators.', reference: 'ISA 500 / IAS 16 / ASC 360', category: 'Testing Suite', testCount: 9 },
  { key: 'inventory_testing', label: 'Inventory Testing', href: '/tools/inventory-testing', description: 'Analyze inventory records for valuation anomalies, obsolescence indicators, and cutoff issues.', reference: 'ISA 501 / IAS 2 / ASC 330', category: 'Testing Suite', testCount: 9 },
  // Advanced
  { key: 'statistical_sampling', label: 'Statistical Sampling', href: '/tools/statistical-sampling', description: 'Design and evaluate audit samples using ISA 530 methodology — MUS, classical variables, and attribute sampling.', reference: 'ISA 530 Audit Sampling', category: 'Advanced' },
  { key: 'composite_risk', label: 'Composite Risk Scoring', href: '/tools/composite-risk', description: 'Record auditor-assessed inherent/control/fraud risk per account/assertion; combine via the ISA 315 RMM matrix with optional diagnostic integration.', reference: 'ISA 315 (Revised 2019) / ISA 330', category: 'Advanced' },
  { key: 'account_risk_heatmap', label: 'Account Risk Heatmap', href: '/tools/account-risk-heatmap', description: 'Aggregate per-account signals across diagnostic engines into a ranked triage-density view with priority tiers and CSV export.', reference: 'ISA 315 / ISA 520', category: 'Advanced' },
  { key: 'flux_analysis', label: 'Flux Analysis', href: '/flux', description: 'Account-level variance analysis comparing current and prior period balances with materiality-based flagging.', reference: 'ISA 520 Analytical Procedures', category: 'Advanced' },
  { key: 'loan_amortization', label: 'Loan Amortization', href: '/tools/loan-amortization', description: 'Generate period-by-period amortization schedules — standard, interest-only, and balloon loans with extra payments and book journal entry templates.', reference: 'Form input — no upload', category: 'Advanced' },
  { key: 'depreciation', label: 'Depreciation Calculator', href: '/tools/depreciation', description: 'Generate book and MACRS tax depreciation schedules — straight-line, declining balance, SYD, units of production; book vs tax timing reconciliation with deferred tax bridge.', reference: 'IRS Pub 946 / IAS 16 / ASC 360', category: 'Advanced' },
  { key: 'currency_rates', label: 'Multi-Currency Conversion', href: '/tools/multi-currency', description: 'Manage exchange-rate tables and manual rate entries for multi-currency trial balances — ISO 4217 validation, cohort-aware staleness detection, and defense-in-depth rate validation.', reference: 'IAS 21 / ASC 830', category: 'Advanced' },
]

const CATEGORIES: Category[] = ['Core Analysis', 'Testing Suite', 'Advanced']

/* ─── Component ─────────────────────────────────────────────────────── */

export default function ToolsCatalogPage() {
  const { token } = useAuthSession()
  const [favorites, setFavorites] = useState<string[]>([])

  useEffect(() => {
    if (!token) return
    apiGet<UserPreferences>('/settings/preferences', token)
      .then(res => { if (res.data?.favorite_tools) setFavorites(res.data.favorite_tools) })
      .catch(err => {
        // Sprint 693: preference load failures were swallowed silently;
        // log as a warning so regressions surface in the console and
        // downstream Sentry breadcrumbs without breaking the page.
        console.warn('[tools] preference load failed', err)
      })
  }, [token])

  const toggleFavorite = useCallback(
    async (toolKey: string) => {
      if (!token) return
      const next = favorites.includes(toolKey)
        ? favorites.filter(k => k !== toolKey)
        : [...favorites, toolKey]
      setFavorites(next)
      try {
        await apiPut('/settings/preferences', token, { favorite_tools: next })
      } catch {
        setFavorites(favorites)
      }
    },
    [token, favorites]
  )

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="h-[2px] bg-gradient-to-r from-transparent via-sage-500/20 to-transparent" />

      <div className="max-w-6xl mx-auto px-6 pt-8 pb-16">
        <Reveal>
          <div className="mb-8">
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
              Diagnostic Tools
            </h1>
            <p className="text-sm font-sans text-content-secondary mt-1.5">
              {TOOLS.length} tools across {CATEGORIES.length} categories. Pin your favorites for quick access on the dashboard.
            </p>
          </div>
        </Reveal>

        {CATEGORIES.map((category, catIdx) => {
          const categoryTools = TOOLS.filter(t => t.category === category)
          return (
            <Reveal key={category} delay={0.05 * (catIdx + 1)}>
              <div className="mb-10">
                <h2 className="font-serif text-lg font-bold text-content-primary mb-4">{category}</h2>
                <motion.div
                  variants={staggerContainerTight}
                  initial="hidden"
                  animate="visible"
                  className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4"
                >
                  {categoryTools.map(tool => (
                    <motion.div key={tool.key} variants={fadeUp} className="relative group">
                      <Link
                        href={tool.href}
                        className="theme-card p-5 flex flex-col h-full hover:shadow-theme-card-hover transition-all block"
                      >
                        <div className="flex items-center justify-between mb-2">
                          <h3 className="font-serif font-bold text-sm text-content-primary">{tool.label}</h3>
                        </div>
                        <p className="text-xs font-sans text-content-secondary flex-1 mb-3">{tool.description}</p>
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-sans text-content-tertiary uppercase tracking-wider">
                            {tool.reference}
                          </span>
                          {tool.testCount && (
                            <span className="text-[10px] font-mono text-sage-600 bg-sage-50 px-1.5 py-0.5 rounded border border-sage-200">
                              {tool.testCount} tests
                            </span>
                          )}
                        </div>
                      </Link>
                      <button
                        onClick={(e) => { e.preventDefault(); toggleFavorite(tool.key) }}
                        className="absolute top-3 right-3 w-7 h-7 flex items-center justify-center rounded-lg opacity-0 group-hover:opacity-100 focus-visible:opacity-100 transition-opacity hover:bg-oatmeal-100"
                        aria-label={favorites.includes(tool.key) ? 'Remove from favorites' : 'Pin to dashboard'}
                        title={favorites.includes(tool.key) ? 'Remove from favorites' : 'Pin to dashboard'}
                      >
                        <svg
                          className={`w-4 h-4 ${favorites.includes(tool.key) ? 'text-sage-600 fill-sage-600' : 'text-content-tertiary'}`}
                          fill={favorites.includes(tool.key) ? 'currentColor' : 'none'}
                          stroke="currentColor"
                          viewBox="0 0 24 24"
                        >
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11.48 3.499a.562.562 0 011.04 0l2.125 5.111a.563.563 0 00.475.345l5.518.442c.499.04.701.663.321.988l-4.204 3.602a.563.563 0 00-.182.557l1.285 5.385a.562.562 0 01-.84.61l-4.725-2.885a.563.563 0 00-.586 0L6.982 20.54a.562.562 0 01-.84-.61l1.285-5.386a.562.562 0 00-.182-.557l-4.204-3.602a.563.563 0 01.321-.988l5.518-.442a.563.563 0 00.475-.345L11.48 3.5z" />
                        </svg>
                      </button>
                    </motion.div>
                  ))}
                </motion.div>
              </div>
            </Reveal>
          )
        })}
      </div>
    </main>
  )
}
