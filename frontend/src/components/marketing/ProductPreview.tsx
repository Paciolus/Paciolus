'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { ENTER, VIEWPORT, AXIS } from '@/utils/marketingMotion'
import { SPRING } from '@/utils/themeUtils'

/**
 * ProductPreview — Sprint 322, motion migrated Sprint 337
 *
 * Interactive tabbed product preview for the homepage.
 * Shows 3 key views: TB Diagnostics, Testing Suite, Diagnostic Workspace.
 * Each tab renders a stylized, simplified version of the real UI.
 *
 * Glass-morphism container with shared-axis horizontal tab transitions.
 */

type PreviewTab = 'diagnostics' | 'testing' | 'workspace'

const TABS: Array<{ id: PreviewTab; label: string; icon: string }> = [
  { id: 'diagnostics', label: 'TB Diagnostics', icon: '📊' },
  { id: 'testing', label: 'Testing Suite', icon: '🔍' },
  { id: 'workspace', label: 'Workspace', icon: '📋' },
]

/** Stylized TB Diagnostics preview */
function DiagnosticsPreview() {
  return (
    <div className="space-y-4">
      {/* Balance Summary */}
      <div className="flex items-center gap-3 p-3 rounded-lg bg-sage-500/10 border border-sage-500/20">
        <div className="w-8 h-8 rounded-full bg-sage-500/20 flex items-center justify-center">
          <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <div className="flex-1">
          <p className="text-sage-400 text-sm font-serif font-semibold">Trial Balance: Balanced</p>
          <p className="text-oatmeal-500 text-xs font-sans">47 accounts analyzed in 1.2s</p>
        </div>
        <span className="font-mono text-xs text-oatmeal-400">$12.4M total</span>
      </div>

      {/* Ratio Cards */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Current Ratio', value: '1.82', status: 'good' },
          { label: 'Debt to Equity', value: '0.67', status: 'good' },
          { label: 'Quick Ratio', value: '1.24', status: 'neutral' },
        ].map((ratio) => (
          <div key={ratio.label} className="p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
            <p className="text-oatmeal-600 text-[10px] font-sans uppercase tracking-wide mb-1">{ratio.label}</p>
            <p className={`font-mono text-lg font-bold ${ratio.status === 'good' ? 'text-sage-400' : 'text-oatmeal-300'}`}>
              {ratio.value}
            </p>
          </div>
        ))}
      </div>

      {/* Anomaly Flags */}
      <div className="space-y-2">
        <p className="text-oatmeal-500 text-xs font-sans uppercase tracking-wide">Anomaly Flags</p>
        {[
          { text: 'Suspense account detected: Account 9999', severity: 'high' },
          { text: 'Revenue concentration: 84% from top 3 accounts', severity: 'medium' },
          { text: 'Rounding anomaly: 7 accounts with cents', severity: 'low' },
        ].map((flag, i) => (
          <div
            key={i}
            className={`flex items-center gap-2 p-2 rounded-lg border ${
              flag.severity === 'high'
                ? 'border-clay-500/30 bg-clay-500/5'
                : flag.severity === 'medium'
                ? 'border-oatmeal-400/30 bg-oatmeal-400/5'
                : 'border-obsidian-500/30 bg-obsidian-700/30'
            }`}
          >
            <div className={`w-1.5 h-1.5 rounded-full ${
              flag.severity === 'high' ? 'bg-clay-500' : flag.severity === 'medium' ? 'bg-oatmeal-400' : 'bg-oatmeal-600'
            }`} />
            <span className="text-oatmeal-300 text-xs font-sans">{flag.text}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

/** Stylized Testing Suite preview */
function TestingPreview() {
  return (
    <div className="space-y-4">
      {/* Score Overview */}
      <div className="flex items-center gap-4 p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
        <div className="relative w-14 h-14 flex-shrink-0">
          <svg viewBox="0 0 100 100" className="w-full h-full">
            <circle cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="4" className="text-obsidian-600" />
            <circle
              cx="50" cy="50" r="40" fill="none" stroke="currentColor" strokeWidth="4"
              className="text-sage-500"
              strokeLinecap="round"
              strokeDasharray={`${2 * Math.PI * 40}`}
              strokeDashoffset={2 * Math.PI * 40 * 0.24}
              transform="rotate(-90 50 50)"
            />
          </svg>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="font-mono text-sm font-bold text-sage-400">76</span>
          </div>
        </div>
        <div>
          <p className="text-oatmeal-200 text-sm font-serif font-semibold">Composite Risk Score</p>
          <p className="text-sage-400 text-xs font-sans">Low Risk — 18 tests passed</p>
        </div>
      </div>

      {/* Test Results Grid */}
      <div className="grid grid-cols-2 gap-3">
        {[
          { tool: 'Journal Entry', tests: 18, flagged: 3, status: 'pass' },
          { tool: 'AP Payment', tests: 13, flagged: 1, status: 'pass' },
          { tool: 'Revenue', tests: 12, flagged: 2, status: 'pass' },
          { tool: 'Payroll', tests: 11, flagged: 0, status: 'pass' },
        ].map((test) => (
          <div key={test.tool} className="p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
            <div className="flex items-center justify-between mb-2">
              <p className="text-oatmeal-300 text-xs font-sans font-medium">{test.tool}</p>
              <span className="text-sage-400 text-[10px] font-mono bg-sage-500/10 px-1.5 py-0.5 rounded">{test.status.toUpperCase()}</span>
            </div>
            <div className="flex items-baseline gap-1">
              <span className="font-mono text-lg text-oatmeal-200">{test.tests}</span>
              <span className="text-oatmeal-600 text-[10px] font-sans">tests</span>
              <span className="text-oatmeal-600 text-xs mx-1">/</span>
              <span className={`font-mono text-sm ${test.flagged > 0 ? 'text-clay-400' : 'text-sage-400'}`}>{test.flagged}</span>
              <span className="text-oatmeal-600 text-[10px] font-sans">flagged</span>
            </div>
          </div>
        ))}
      </div>

      {/* Standards badge */}
      <div className="flex items-center gap-2 p-2 rounded-lg bg-obsidian-700/30 border border-obsidian-500/20">
        <svg className="w-4 h-4 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span className="text-oatmeal-500 text-xs font-sans">ISA 240 / ISA 530 / PCAOB AS 2315 Compliant</span>
      </div>
    </div>
  )
}

/** Stylized Workspace preview */
function WorkspacePreview() {
  return (
    <div className="space-y-4">
      {/* Engagement Header */}
      <div className="p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
        <div className="flex items-center justify-between mb-2">
          <div>
            <p className="text-oatmeal-200 text-sm font-serif font-semibold">Acme Manufacturing Corp</p>
            <p className="text-oatmeal-500 text-xs font-sans">FY 2025 — Diagnostic Workspace</p>
          </div>
          <span className="text-sage-400 text-[10px] font-sans font-medium bg-sage-500/10 px-2 py-1 rounded-full border border-sage-500/20">Active</span>
        </div>
        <div className="flex items-center gap-4 text-xs text-oatmeal-500 font-sans">
          <span>Materiality: <span className="text-oatmeal-300 font-mono">$50,000</span></span>
          <span>Performance: <span className="text-oatmeal-300 font-mono">$37,500</span></span>
        </div>
      </div>

      {/* Tool Run Summary */}
      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Tools Run', value: '8', sub: 'of 12' },
          { label: 'Follow-ups', value: '5', sub: 'items' },
          { label: 'Workpapers', value: '12', sub: 'indexed' },
        ].map((stat) => (
          <div key={stat.label} className="p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30 text-center">
            <p className="font-mono text-lg font-bold text-oatmeal-200">{stat.value}</p>
            <p className="text-oatmeal-600 text-[10px] font-sans">{stat.sub}</p>
            <p className="text-oatmeal-500 text-[10px] font-sans mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

      {/* Recent Follow-ups */}
      <div>
        <p className="text-oatmeal-500 text-xs font-sans uppercase tracking-wide mb-2">Recent Follow-Up Items</p>
        <div className="space-y-2">
          {[
            { text: 'Investigate suspense account balance', priority: 'high' },
            { text: 'Confirm revenue recognition timing', priority: 'medium' },
            { text: 'Review depreciation schedule changes', priority: 'low' },
          ].map((item, i) => (
            <div key={i} className="flex items-center gap-2 p-2 rounded-lg bg-obsidian-700/30 border border-obsidian-500/20">
              <div className={`w-1.5 h-1.5 rounded-full ${
                item.priority === 'high' ? 'bg-clay-500' : item.priority === 'medium' ? 'bg-oatmeal-400' : 'bg-sage-500'
              }`} />
              <span className="text-oatmeal-300 text-xs font-sans flex-1">{item.text}</span>
              <span className="text-oatmeal-600 text-[10px] font-mono uppercase">{item.priority}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

const TAB_CONTENT: Record<PreviewTab, React.ReactNode> = {
  diagnostics: <DiagnosticsPreview />,
  testing: <TestingPreview />,
  workspace: <WorkspacePreview />,
}

export function ProductPreview() {
  const [activeTab, setActiveTab] = useState<PreviewTab>('diagnostics')

  return (
    <section className="py-24 px-6">
      <motion.div
        className="max-w-3xl mx-auto"
        variants={ENTER.fadeUp}
        initial="hidden"
        whileInView="visible"
        viewport={VIEWPORT.default}
      >
        {/* Section Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-4">
            <svg className="w-4 h-4 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
            <span className="text-sage-300 text-sm font-sans font-medium">Product Preview</span>
          </div>
          <h2 className="text-3xl font-serif font-bold text-oatmeal-200 mb-2">
            See Paciolus in Action
          </h2>
          <p className="text-oatmeal-400 font-sans text-sm">
            Explore the three pillars of audit diagnostic intelligence
          </p>
        </div>

        {/* Glass-morphism container */}
        <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/60 backdrop-blur-xl overflow-hidden shadow-2xl shadow-obsidian-900/50">
          {/* Tab Bar */}
          <div className="flex border-b border-obsidian-500/30">
            {TABS.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex-1 flex items-center justify-center gap-2 px-4 py-3.5 text-sm font-sans font-medium transition-all relative ${
                  activeTab === tab.id
                    ? 'text-oatmeal-100 bg-obsidian-700/50'
                    : 'text-oatmeal-500 hover:text-oatmeal-300 hover:bg-obsidian-700/20'
                }`}
              >
                <span className="text-base" role="img" aria-hidden="true">{tab.icon}</span>
                <span className="hidden sm:inline">{tab.label}</span>
                {activeTab === tab.id && (
                  <motion.div
                    layoutId="preview-tab-indicator"
                    className="absolute bottom-0 left-0 right-0 h-0.5 bg-sage-500"
                    transition={SPRING.snappy}
                  />
                )}
              </button>
            ))}
          </div>

          {/* Tab Content — shared-axis horizontal transition */}
          <div className="p-5 min-h-[380px]">
            <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                {...AXIS.horizontal}
              >
                {TAB_CONTENT[activeTab]}
              </motion.div>
            </AnimatePresence>
          </div>

          {/* Footer CTA */}
          <div className="px-5 py-4 border-t border-obsidian-500/30 bg-obsidian-800/40 flex items-center justify-between">
            <p className="text-oatmeal-600 text-xs font-sans">
              Sample data — Zero-Storage: nothing is saved
            </p>
            <Link
              href="/register"
              className="px-4 py-2 bg-sage-600 text-white text-sm font-sans font-medium rounded-lg hover:bg-sage-500 transition-colors shadow-md shadow-sage-600/20"
            >
              Try it yourself
            </Link>
          </div>
        </div>
      </motion.div>
    </section>
  )
}
