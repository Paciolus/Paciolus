'use client'

import { motion } from 'framer-motion'
import type { ThreeWayMatchSummaryData } from '@/types/threeWayMatch'
import { RISK_COLORS, RISK_BG_COLORS } from '@/types/threeWayMatch'

interface MatchSummaryCardProps {
  summary: ThreeWayMatchSummaryData
}

const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const pct = (n: number) => `${(n * 100).toFixed(1)}%`

export function MatchSummaryCard({ summary }: MatchSummaryCardProps) {
  const riskColor = RISK_COLORS[summary.risk_assessment] || 'text-oatmeal-400'
  const riskBg = RISK_BG_COLORS[summary.risk_assessment] || 'bg-obsidian-700/50 border-obsidian-500/30'

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-2xl p-6"
    >
      {/* Header + Risk Badge */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="font-serif text-lg text-oatmeal-200">Match Summary</h2>
        <div className={`px-3 py-1 rounded-full border text-sm font-sans font-medium ${riskBg} ${riskColor}`}>
          {summary.risk_assessment.toUpperCase()} RISK
        </div>
      </div>

      {/* Match Rate Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
        <div className="bg-obsidian-700/40 rounded-xl p-4 text-center">
          <p className="font-mono text-2xl text-sage-400">{summary.full_match_count}</p>
          <p className="font-sans text-xs text-oatmeal-500 mt-1">Full Matches</p>
          <p className="font-mono text-xs text-oatmeal-600 mt-0.5">{pct(summary.full_match_rate)}</p>
        </div>
        <div className="bg-obsidian-700/40 rounded-xl p-4 text-center">
          <p className="font-mono text-2xl text-oatmeal-300">{summary.partial_match_count}</p>
          <p className="font-sans text-xs text-oatmeal-500 mt-1">Partial Matches</p>
          <p className="font-mono text-xs text-oatmeal-600 mt-0.5">{pct(summary.partial_match_rate)}</p>
        </div>
        <div className="bg-obsidian-700/40 rounded-xl p-4 text-center">
          <p className="font-mono text-2xl text-clay-400">{summary.material_variances_count}</p>
          <p className="font-sans text-xs text-oatmeal-500 mt-1">Material Variances</p>
        </div>
        <div className="bg-obsidian-700/40 rounded-xl p-4 text-center">
          <p className={`font-mono text-2xl ${summary.net_variance === 0 ? 'text-sage-400' : 'text-clay-400'}`}>
            ${fmt(summary.net_variance)}
          </p>
          <p className="font-sans text-xs text-oatmeal-500 mt-1">Net Variance</p>
        </div>
      </div>

      {/* Amount Totals */}
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <p className="font-sans text-xs text-oatmeal-500 mb-1">Total PO Amount</p>
          <p className="font-mono text-sm text-oatmeal-300">${fmt(summary.total_po_amount)}</p>
          <p className="font-sans text-xs text-oatmeal-600">{summary.total_pos} POs</p>
        </div>
        <div className="text-center">
          <p className="font-sans text-xs text-oatmeal-500 mb-1">Total Invoice Amount</p>
          <p className="font-mono text-sm text-oatmeal-300">${fmt(summary.total_invoice_amount)}</p>
          <p className="font-sans text-xs text-oatmeal-600">{summary.total_invoices} Invoices</p>
        </div>
        <div className="text-center">
          <p className="font-sans text-xs text-oatmeal-500 mb-1">Total Receipt Amount</p>
          <p className="font-mono text-sm text-oatmeal-300">${fmt(summary.total_receipt_amount)}</p>
          <p className="font-sans text-xs text-oatmeal-600">{summary.total_receipts} Receipts</p>
        </div>
      </div>
    </motion.div>
  )
}
