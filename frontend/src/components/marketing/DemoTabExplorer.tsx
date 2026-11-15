'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { MechanicalGauge, MarginAnnotation } from '@/components/demo'
import { Reveal } from '@/components/ui/Reveal'
import { TOOL_LEDGER } from '@/content/tool-ledger'
import { AXIS } from '@/utils/marketingMotion'
import { SPRING } from '@/utils/themeUtils'

// Sprint 843: test counts come from the tool ledger (they had drifted — AP
// showed 13 of 14, Revenue 16 of 18, Payroll 11 of 13), and a demo result is
// "flagged / not flagged", never PASS.
const testCount = (id: string) => TOOL_LEDGER.find(t => t.id === id)?.testCount ?? 0
const DEMO_TESTS = [
  { tool: 'Journal Entry', tests: testCount('journal_entry_testing'), flagged: 3 },
  { tool: 'AP Payment', tests: testCount('ap_testing'), flagged: 1 },
  { tool: 'Revenue', tests: testCount('revenue_testing'), flagged: 2 },
  { tool: 'Payroll', tests: testCount('payroll_testing'), flagged: 0 },
]


/**
 * DemoTabExplorer — Sprint 448
 *
 * Expanded 5-tab interactive demo widget for the /demo page.
 * Replaces ProductPreview (3 tabs) with deeper content:
 * TB Diagnostics, Testing Suite, Workspace, Sample Reports.
 * (Sprint 861: the Standards tab was removed — no standard names on marketing
 * pages; citations live on /sources.)
 *
 * Guardian requirement: persistent "Synthetic data" disclaimer banner.
 * Uses layoutId="demo-tab-indicator" (distinct from ProductPreview's "preview-tab-indicator").
 */

type DemoTab = 'diagnostics' | 'testing' | 'workspace' | 'reports'

const TABS: Array<{ id: DemoTab; label: string }> = [
  { id: 'diagnostics', label: 'TB Diagnostics' },
  { id: 'testing',     label: 'Testing Suite' },
  { id: 'workspace',  label: 'Workspace' },
  { id: 'reports',    label: 'Sample Reports' },
]

/* ─── Tab content components ─────────────────────────────── */

function DiagnosticsTab() {
  return (
    // Sprint 707 — scanline overlay sweeps the TB diagnostic block once
    // on tab mount.
    // Reduced-motion skips the sweep; content renders immediately.
    <div>
      <div className="space-y-4">
        <div className="flex items-center gap-3 p-3 rounded-lg bg-sage-500/10 border border-sage-500/20">
          <div className="w-8 h-8 rounded-full bg-sage-500/20 flex items-center justify-center">
            <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          </div>
          <div className="flex-1">
            <p className="text-sage-400 text-sm font-serif font-semibold">Trial Balance: Balanced</p>
            <p className="text-oatmeal-500 text-xs font-sans">47 accounts analyzed · 1.2s runtime</p>
          </div>
          <span className="font-mono text-xs text-oatmeal-400">$12.4M total</span>
        </div>

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

        {/* Sprint 707 — Anomaly flags render as margin annotations
            (red-pen italic with caret glyph) rather than pill toasts.
            Matches the physical audit-review language. */}
        <div className="space-y-1">
          <p className="text-oatmeal-500 text-xs font-sans uppercase tracking-wide mb-2">Anomaly Flags</p>
          <MarginAnnotation severity="high">
            Suspense account detected: Account 9999
          </MarginAnnotation>
          <MarginAnnotation severity="moderate">
            Revenue concentration: 84% from top 3 accounts
          </MarginAnnotation>
          <MarginAnnotation severity="low">
            Rounding anomaly: 7 accounts with cents
          </MarginAnnotation>
        </div>
      </div>
    </div>
  )
}

function TestingTab() {
  return (
    <div className="space-y-4">
      {/* Sprint 707 — Composite Diagnostic Score now rendered as a proper
          arc-style MechanicalGauge (180° sweep, hairline tick marks every
          10 units, needle eases to the score on mount). Replaces the
          flat circle-dial. Reduced-motion skips the needle animation. */}
      <div className="flex items-center gap-4 p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
        <div className="flex-shrink-0">
          <MechanicalGauge score={76} riskLevel="low" size={140} />
        </div>
        <div>
          <p className="text-oatmeal-200 text-sm font-serif font-semibold">Composite Diagnostic Score</p>
          <p className="text-sage-400 text-xs font-sans">Low flag density — {DEMO_TESTS.reduce((n, t) => n + t.flagged, 0)} items flagged across 4 tools</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {DEMO_TESTS.map((test) => (
          <div key={test.tool} className="p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
            <div className="flex items-center justify-between mb-2">
              <p className="text-oatmeal-300 text-xs font-sans font-medium">{test.tool}</p>
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

      <div className="flex items-center gap-2 p-2 rounded-lg bg-obsidian-700/30 border border-obsidian-500/20">
        <svg className="w-4 h-4 text-theme-success-text shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span className="text-oatmeal-500 text-xs font-sans">Every test cites its rule. See <Link href="/sources" className="text-sage-400 underline">Sources &amp; Methodology</Link>.</span>
      </div>
    </div>
  )
}

function WorkspaceTab() {
  return (
    <div className="space-y-4">
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

      <div className="grid grid-cols-3 gap-3">
        {[
          { label: 'Tools Run', value: '8', sub: 'of 18' },
          { label: 'Follow-ups', value: '5', sub: 'items' },
          { label: 'Exports', value: '12', sub: 'downloaded' },
        ].map((stat) => (
          <div key={stat.label} className="p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30 text-center">
            <p className="font-mono text-lg font-bold text-oatmeal-200">{stat.value}</p>
            <p className="text-oatmeal-600 text-[10px] font-sans">{stat.sub}</p>
            <p className="text-oatmeal-500 text-[10px] font-sans mt-1">{stat.label}</p>
          </div>
        ))}
      </div>

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

function ReportsTab() {
  return (
    <div className="space-y-4">
      <p className="text-oatmeal-500 text-xs font-sans uppercase tracking-wide">Available Export Formats</p>
      <p className="font-sans text-sm text-oatmeal-300">
        <a href="/samples/paciolus-sample-je-testing-memo.pdf" className="text-sage-400 hover:text-sage-300 underline">
          Download a sample Journal Entry Testing memo (PDF)
        </a>{' '}
        <span className="text-oatmeal-500">— default layout, synthetic data, marked SAMPLE on every page.</span>
      </p>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[
          {
            format: 'PDF Memo',
            desc: 'Memo of test results that cites the rule behind each test, for your review.',
            badge: 'PDF',
          },
          {
            format: 'Excel Workbook',
            desc: 'Multi-sheet workbook with the flagged items, ratio tables and a summary sheet.',
            badge: 'XLS / XLSX',
          },
          {
            format: 'Diagnostic Package ZIP',
            desc: 'One ZIP per engagement: an anomaly summary PDF, a workpaper index and a file manifest.',
            badge: 'Engagement',
          },
          {
            format: 'CSV Extract',
            desc: 'Flat file of flagged transactions for use in other software.',
            badge: 'CSV',
          },
        ].map((item) => (
          <div key={item.format} className="p-4 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
            <div className="flex items-start gap-3">
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <p className="font-sans text-sm font-medium text-oatmeal-200">{item.format}</p>
                  <span className="shrink-0 px-1.5 py-0.5 rounded font-mono text-[9px] text-sage-400 bg-sage-500/10 border border-sage-500/20">
                    {item.badge}
                  </span>
                </div>
                <p className="font-sans text-xs text-oatmeal-500 leading-relaxed">{item.desc}</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      <div className="p-3 rounded-lg bg-obsidian-700/30 border border-obsidian-500/20 flex items-center gap-2">
        <svg className="w-4 h-4 text-oatmeal-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="font-sans text-xs text-oatmeal-500">
          Exports are generated when you request them and sent to your browser. A report you share by link is stored for up to 24 hours (Professional) or 48 hours (Enterprise), then deleted. Analysis summaries are saved to your history.
        </span>
      </div>
    </div>
  )
}


const TAB_CONTENT: Record<DemoTab, React.ReactNode> = {
  diagnostics: <DiagnosticsTab />,
  testing:     <TestingTab />,
  workspace:   <WorkspaceTab />,
  reports:     <ReportsTab />,
}

/* ─── Main export ─────────────────────────────────────────── */

export function DemoTabExplorer() {
  const [activeTab, setActiveTab] = useState<DemoTab>('diagnostics')

  return (
    <Reveal>
      {/* Guardian requirement: persistent synthetic-data banner */}
      <div className="flex items-center justify-center gap-2 mb-4 px-4 py-2 rounded-lg bg-oatmeal-400/5 border border-oatmeal-400/15">
        <svg className="w-3.5 h-3.5 text-oatmeal-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="font-sans text-xs text-oatmeal-500">
          All data shown is synthetic — no client information is used or stored
        </span>
      </div>

      {/* Container (Sprint 864: opaque, no glass) */}
      <div className="rounded-lg border border-obsidian-500/30 bg-obsidian-800 overflow-hidden">
        {/* Tab bar — horizontal scroll on mobile */}
        <div className="flex border-b border-obsidian-500/30 overflow-x-auto scrollbar-none">
          {TABS.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex-shrink-0 flex items-center justify-center gap-2 px-4 py-3.5 text-sm font-sans font-medium transition-all relative ${
                activeTab === tab.id
                  ? 'text-oatmeal-100 bg-obsidian-700/50'
                  : 'text-oatmeal-500 hover:text-oatmeal-300 hover:bg-obsidian-700/20'
              }`}
            >
              <span className="whitespace-nowrap">{tab.label}</span>
              {activeTab === tab.id && (
                <motion.div
                  layoutId="demo-tab-indicator"
                  className="absolute bottom-0 left-0 right-0 h-0.5 bg-sage-500"
                  transition={SPRING.snappy}
                />
              )}
            </button>
          ))}
        </div>

        {/* Content */}
        <div className="p-5 min-h-[420px]">
          <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              {...AXIS.horizontal}
            >
              {TAB_CONTENT[activeTab]}
            </motion.div>
          </AnimatePresence>
        </div>
      </div>
    </Reveal>
  )
}
