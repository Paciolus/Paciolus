'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { AXIS, VIEWPORT } from '@/utils/marketingMotion'
import { SPRING } from '@/utils/themeUtils'

/**
 * DemoTabExplorer — Sprint 448
 *
 * Expanded 5-tab interactive demo widget for the /demo page.
 * Replaces ProductPreview (3 tabs) with deeper content:
 * TB Diagnostics, Testing Suite, Workspace, Sample Reports, Audit Standards.
 *
 * Guardian requirement: persistent "Synthetic data" disclaimer banner.
 * Uses layoutId="demo-tab-indicator" (distinct from ProductPreview's "preview-tab-indicator").
 */

type DemoTab = 'diagnostics' | 'testing' | 'workspace' | 'reports' | 'standards'

const TABS: Array<{ id: DemoTab; label: string; icon: string }> = [
  { id: 'diagnostics', label: 'TB Diagnostics', icon: '📊' },
  { id: 'testing',     label: 'Testing Suite',  icon: '🔍' },
  { id: 'workspace',  label: 'Workspace',       icon: '📋' },
  { id: 'reports',    label: 'Sample Reports',  icon: '📄' },
  { id: 'standards',  label: 'Standards',       icon: '⚖️' },
]

/* ─── Tab content components ─────────────────────────────── */

function DiagnosticsTab() {
  return (
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

function TestingTab() {
  return (
    <div className="space-y-4">
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
          <p className="text-sage-400 text-xs font-sans">Low Risk — 54 tests passed across 4 tools</p>
        </div>
      </div>

      <div className="grid grid-cols-2 gap-3">
        {[
          { tool: 'Journal Entry', tests: 19, flagged: 3 },
          { tool: 'AP Payment',    tests: 13, flagged: 1 },
          { tool: 'Revenue',       tests: 16, flagged: 2 },
          { tool: 'Payroll',       tests: 11, flagged: 0 },
        ].map((test) => (
          <div key={test.tool} className="p-3 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
            <div className="flex items-center justify-between mb-2">
              <p className="text-oatmeal-300 text-xs font-sans font-medium">{test.tool}</p>
              <span className="text-sage-400 text-[10px] font-mono bg-sage-500/10 px-1.5 py-0.5 rounded-sm">PASS</span>
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
        <svg className="w-4 h-4 text-sage-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <span className="text-oatmeal-500 text-xs font-sans">ISA 240 / ISA 530 / PCAOB AS 2315 / ASC 606 / IFRS 15</span>
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

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
        {[
          {
            format: 'PDF Workpaper Memo',
            desc: 'Structured memo with test results, standards citations, and auditor sign-off block. Ready to attach to workpapers.',
            badge: 'PCAOB AS 1215',
            icon: '📄',
          },
          {
            format: 'Excel Workbook',
            desc: 'Multi-sheet output with raw flagged data, ratio tables, and a summary dashboard for further analysis.',
            badge: 'XLS / XLSX',
            icon: '📊',
          },
          {
            format: 'Diagnostic Package ZIP',
            desc: 'All outputs for an engagement bundled into a single downloadable archive — PDF memos, Excel, and index.',
            badge: 'Engagement',
            icon: '📦',
          },
          {
            format: 'CSV Extract',
            desc: 'Machine-readable flat file of flagged transactions for import into audit management software.',
            badge: 'CSV',
            icon: '📃',
          },
        ].map((item) => (
          <div key={item.format} className="p-4 rounded-lg bg-obsidian-700/50 border border-obsidian-500/30">
            <div className="flex items-start gap-3">
              <span className="text-xl">{item.icon}</span>
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
          All exports generated on-demand. No data is stored between sessions.
        </span>
      </div>
    </div>
  )
}

function StandardsTab() {
  const STANDARDS = [
    { code: 'ISA 240',        title: 'Auditor Responsibilities — Fraud',       tools: 'JE Testing, Revenue Testing' },
    { code: 'ISA 500',        title: 'Audit Evidence',                          tools: 'AR Aging, Fixed Assets' },
    { code: 'ISA 501',        title: 'Specific Considerations — Cutoff',        tools: 'TB Diagnostics (Cutoff Risk)' },
    { code: 'ISA 520',        title: 'Analytical Procedures',                   tools: 'TB Diagnostics, Multi-Period' },
    { code: 'ISA 530',        title: 'Audit Sampling',                          tools: 'Statistical Sampling, JE Testing' },
    { code: 'ISA 540',        title: 'Auditing Accounting Estimates',           tools: 'AR Aging, Fixed Assets' },
    { code: 'ISA 570',        title: 'Going Concern',                           tools: 'TB Diagnostics (Going Concern)' },
    { code: 'PCAOB AS 2315',  title: 'Audit Sampling',                          tools: 'Statistical Sampling' },
    { code: 'PCAOB AS 2401',  title: 'Fraud in a Financial Statement Audit',    tools: 'JE Testing, Revenue Testing' },
    { code: 'ASC 606',        title: 'Revenue from Contracts with Customers',   tools: 'Revenue Testing (RT-13 to RT-16)' },
    { code: 'IFRS 15',        title: 'Revenue from Contracts with Customers',   tools: 'Revenue Testing (contract-aware)' },
    { code: 'IAS 2',          title: 'Inventories',                             tools: 'Inventory Testing' },
    { code: 'IAS 16',         title: 'Property, Plant and Equipment',           tools: 'Fixed Asset Testing' },
    { code: 'IFRS 16 / ASC 842', title: 'Leases',                              tools: 'TB Diagnostics (Lease Diagnostic)' },
  ]

  return (
    <div className="space-y-3">
      <p className="text-oatmeal-500 text-xs font-sans uppercase tracking-wide">Standards Referenced in Platform Outputs</p>
      <div className="rounded-lg border border-obsidian-500/30 overflow-hidden">
        <table className="w-full text-xs">
          <thead>
            <tr className="bg-obsidian-700/60 border-b border-obsidian-500/30">
              <th className="text-left font-sans font-medium text-oatmeal-500 px-3 py-2 uppercase tracking-wide text-[10px]">Standard</th>
              <th className="text-left font-sans font-medium text-oatmeal-500 px-3 py-2 uppercase tracking-wide text-[10px] hidden sm:table-cell">Description</th>
              <th className="text-left font-sans font-medium text-oatmeal-500 px-3 py-2 uppercase tracking-wide text-[10px]">Used In</th>
            </tr>
          </thead>
          <tbody>
            {STANDARDS.map((row, i) => (
              <tr
                key={row.code}
                className={`border-b border-obsidian-500/20 ${i % 2 === 0 ? 'bg-obsidian-800/30' : 'bg-obsidian-700/20'}`}
              >
                <td className="px-3 py-2 font-mono text-[11px] text-sage-400 whitespace-nowrap">{row.code}</td>
                <td className="px-3 py-2 font-sans text-[11px] text-oatmeal-500 hidden sm:table-cell">{row.title}</td>
                <td className="px-3 py-2 font-sans text-[11px] text-oatmeal-400">{row.tools}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  )
}

const TAB_CONTENT: Record<DemoTab, React.ReactNode> = {
  diagnostics: <DiagnosticsTab />,
  testing:     <TestingTab />,
  workspace:   <WorkspaceTab />,
  reports:     <ReportsTab />,
  standards:   <StandardsTab />,
}

/* ─── Main export ─────────────────────────────────────────── */

export function DemoTabExplorer() {
  const [activeTab, setActiveTab] = useState<DemoTab>('diagnostics')

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={VIEWPORT.default}
      transition={{ duration: 0.5 }}
    >
      {/* Guardian requirement: persistent synthetic-data banner */}
      <div className="flex items-center justify-center gap-2 mb-4 px-4 py-2 rounded-lg bg-oatmeal-400/5 border border-oatmeal-400/15">
        <svg className="w-3.5 h-3.5 text-oatmeal-500 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <span className="font-sans text-xs text-oatmeal-500">
          All data shown is synthetic — no client information is used or stored
        </span>
      </div>

      {/* Glass container */}
      <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/60 backdrop-blur-xl overflow-hidden shadow-2xl shadow-obsidian-900/50">
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
              <span className="text-base" role="img" aria-hidden="true">{tab.icon}</span>
              <span className="hidden sm:inline whitespace-nowrap">{tab.label}</span>
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
    </motion.div>
  )
}
