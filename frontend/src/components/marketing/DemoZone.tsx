'use client'

/**
 * DemoZone - Sprint 60: Homepage Demo Mode
 *
 * Interactive demo zone showing guests what Paciolus looks like with real data.
 * Uses hardcoded synthetic data ("Acme Manufacturing Corp") to render existing
 * UI components in read-only demo mode. No API calls, no storage.
 *
 * Oat & Obsidian theme compliance enforced throughout.
 */

import { motion } from 'framer-motion'
import Link from 'next/link'
import { RiskDashboard } from '@/components/risk/RiskDashboard'
import { KeyMetricsSection } from '@/components/analytics/KeyMetricsSection'
import { LeadSheetSection } from '@/components/leadSheet/LeadSheetSection'
import { BenchmarkSection } from '@/components/benchmark/BenchmarkSection'
import {
  DEMO_AUDIT_RESULT,
  DEMO_ANALYTICS,
  DEMO_LEAD_SHEETS,
  DEMO_BENCHMARKS,
  DEMO_FILENAME,
} from '@/data/demoData'
import type { AccountType } from '@/types/mapping'

const sectionVariants = {
  hidden: { opacity: 0, y: 30 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' as const } },
}

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.15, delayChildren: 0.2 },
  },
}

export function DemoZone() {
  return (
    <section className="py-24 px-6 bg-obsidian-700/50">
      <motion.div
        className="max-w-3xl mx-auto"
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-50px' }}
        variants={staggerContainer}
      >
        {/* Section Header */}
        <motion.div className="text-center mb-8" variants={sectionVariants}>
          <div className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-4">
            <svg className="w-4 h-4 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span className="text-sage-300 text-sm font-sans font-medium">Interactive Demo</span>
          </div>
          <h2 className="text-3xl font-serif font-bold text-oatmeal-200 mb-2">
            See Paciolus in Action
          </h2>
          <p className="text-oatmeal-400 font-sans">
            Explore a sample diagnostic for Acme Manufacturing Corp
          </p>
        </motion.div>

        {/* Demo Label Banner */}
        <motion.div
          className="mb-6 px-4 py-2.5 bg-sage-500/10 border border-sage-500/20 rounded-lg flex items-center justify-center gap-2"
          variants={sectionVariants}
        >
          <svg className="w-4 h-4 text-sage-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span className="text-sage-300 text-sm font-sans font-medium tracking-wide">
            SAMPLE DATA — {DEMO_FILENAME}
          </span>
        </motion.div>

        {/* Balance Summary */}
        <motion.div variants={sectionVariants}>
          <div className="space-y-4 mb-6">
            <div className="flex flex-col items-center">
              <div className="w-16 h-16 bg-sage-500/20 rounded-full flex items-center justify-center mx-auto">
                <svg className="w-10 h-10 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sage-400 text-xl font-serif font-semibold mt-2">Balanced</p>
            </div>

            <div className="bg-obsidian-800/70 rounded-xl p-4 text-left max-w-sm mx-auto">
              <div className="grid grid-cols-2 gap-2 text-sm font-sans">
                <span className="text-oatmeal-400">Total Debits:</span>
                <span className="text-oatmeal-200 text-right font-mono">${DEMO_AUDIT_RESULT.total_debits.toLocaleString()}</span>
                <span className="text-oatmeal-400">Total Credits:</span>
                <span className="text-oatmeal-200 text-right font-mono">${DEMO_AUDIT_RESULT.total_credits.toLocaleString()}</span>
                <span className="text-oatmeal-400">Difference:</span>
                <span className="text-sage-400 text-right font-mono">$0</span>
                <span className="text-oatmeal-400">Rows Analyzed:</span>
                <span className="text-oatmeal-200 text-right font-mono">{DEMO_AUDIT_RESULT.row_count}</span>
              </div>
            </div>
          </div>
        </motion.div>

        {/* Risk Dashboard */}
        <motion.div className="mt-4" variants={sectionVariants}>
          <RiskDashboard
            anomalies={DEMO_AUDIT_RESULT.abnormal_balances}
            riskSummary={DEMO_AUDIT_RESULT.risk_summary}
            materialityThreshold={DEMO_AUDIT_RESULT.materiality_threshold}
            disabled={true}
            getMappingForAccount={() => ({
              currentType: 'unknown' as AccountType,
              isManual: false,
            })}
            onTypeChange={() => {}}
          />
        </motion.div>

        {/* Key Metrics */}
        <motion.div className="mt-6" variants={sectionVariants}>
          <KeyMetricsSection
            analytics={DEMO_ANALYTICS}
            disabled={true}
          />
        </motion.div>

        {/* Benchmark Comparison */}
        <motion.div className="mt-6 p-4 bg-obsidian-800/70 rounded-xl border border-obsidian-600/50" variants={sectionVariants}>
          <div className="mb-4">
            <h4 className="font-serif text-sm font-medium text-oatmeal-200 mb-1">
              Industry Benchmark Comparison
            </h4>
            <p className="text-xs text-oatmeal-500">
              Comparing ratios against manufacturing industry benchmarks
            </p>
          </div>
          <BenchmarkSection
            data={DEMO_BENCHMARKS}
            industryDisplay="Manufacturing"
            disabled={true}
          />
        </motion.div>

        {/* Lead Sheet Grouping */}
        <motion.div variants={sectionVariants}>
          <LeadSheetSection
            data={DEMO_LEAD_SHEETS}
            disabled={true}
          />
        </motion.div>

        {/* Disclaimer */}
        <motion.div className="mt-4 p-3 bg-obsidian-700/50 border border-obsidian-500/40 rounded-lg" variants={sectionVariants}>
          <p className="text-oatmeal-500 text-xs font-sans text-center leading-relaxed">
            This is a demo using synthetic data for Acme Manufacturing Corp. Sign in to analyze your own trial balance.
            Your data is processed entirely in-memory and is never saved to any disk or server.
          </p>
        </motion.div>

        {/* CTA Card */}
        <motion.div
          className="mt-8 bg-obsidian-800/70 border border-obsidian-500/40 rounded-2xl p-8 text-center"
          variants={sectionVariants}
        >
          <div className="w-16 h-16 bg-sage-500/10 border border-sage-500/20 rounded-full flex items-center justify-center mx-auto mb-6">
            <svg className="w-8 h-8 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <h3 className="text-xl font-serif font-bold text-oatmeal-200 mb-2">
            Ready to analyze your own data?
          </h3>
          <p className="text-oatmeal-400 font-sans text-sm mb-6">
            Create a free account to access trial balance diagnostics, ratio analysis, benchmark comparisons, and professional exports.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
            <Link
              href="/login"
              className="w-full sm:w-auto px-6 py-3 bg-sage-500 text-obsidian-900 rounded-xl font-sans font-medium text-sm hover:bg-sage-400 transition-colors shadow-lg shadow-sage-500/20"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="w-full sm:w-auto px-6 py-3 bg-obsidian-700 border border-sage-500/30 text-sage-400 rounded-xl font-sans font-medium text-sm hover:bg-obsidian-600 hover:border-sage-500/50 transition-colors"
            >
              Create Account
            </Link>
          </div>
          <p className="text-oatmeal-500 text-xs font-sans mt-6">
            Zero-Storage Architecture. Your data is processed entirely in-memory and is never saved to any disk or server.
          </p>
        </motion.div>
      </motion.div>
    </section>
  )
}
