'use client'

import { useState } from 'react'
import type { UnmatchedDocumentData } from '@/types/threeWayMatch'

interface UnmatchedDocumentsPanelProps {
  unmatchedPOs: UnmatchedDocumentData[]
  unmatchedInvoices: UnmatchedDocumentData[]
  unmatchedReceipts: UnmatchedDocumentData[]
}

type Tab = 'pos' | 'invoices' | 'receipts'

const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

function DocumentRow({ doc }: { doc: UnmatchedDocumentData }) {
  const d = doc.document
  const vendor = (d.vendor as string) || '—'
  const amount = typeof d.total_amount === 'number' ? d.total_amount : 0
  const number = (d.po_number || d.invoice_number || d.receipt_number) as string | undefined

  return (
    <div className="flex items-center justify-between py-3 border-b border-obsidian-600/10 last:border-b-0">
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          {number && <span className="font-mono text-xs text-oatmeal-400">{number}</span>}
          <span className="font-sans text-sm text-oatmeal-300 truncate">{vendor}</span>
        </div>
        <p className="font-sans text-xs text-oatmeal-600 mt-0.5">{doc.reason}</p>
      </div>
      {amount !== 0 && (
        <span className="font-mono text-sm text-oatmeal-300 ml-4">${fmt(amount)}</span>
      )}
    </div>
  )
}

export function UnmatchedDocumentsPanel({ unmatchedPOs, unmatchedInvoices, unmatchedReceipts }: UnmatchedDocumentsPanelProps) {
  const total = unmatchedPOs.length + unmatchedInvoices.length + unmatchedReceipts.length
  const [activeTab, setActiveTab] = useState<Tab>('pos')
  const [expanded, setExpanded] = useState(false)

  if (total === 0) return null

  const tabs: { key: Tab; label: string; count: number }[] = [
    { key: 'pos', label: 'POs', count: unmatchedPOs.length },
    { key: 'invoices', label: 'Invoices', count: unmatchedInvoices.length },
    { key: 'receipts', label: 'Receipts', count: unmatchedReceipts.length },
  ]

  const activeItems = activeTab === 'pos' ? unmatchedPOs : activeTab === 'invoices' ? unmatchedInvoices : unmatchedReceipts

  return (
    <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setExpanded(e => !e)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-obsidian-700/20 transition-colors"
      >
        <div className="flex items-center gap-3">
          <h3 className="font-serif text-sm text-oatmeal-200">Unmatched Documents</h3>
          <span className="px-2 py-0.5 rounded-full bg-clay-500/15 border border-clay-500/30 text-xs font-sans text-clay-400">
            {total}
          </span>
        </div>
        <svg
          className={`w-5 h-5 text-oatmeal-500 transform transition-transform ${expanded ? 'rotate-180' : ''}`}
          fill="none" stroke="currentColor" viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {expanded && (
        <div className="border-t border-obsidian-600/20">
          {/* Tabs */}
          <div className="flex border-b border-obsidian-600/20">
            {tabs.map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`flex-1 px-4 py-3 text-sm font-sans transition-colors ${
                  activeTab === tab.key
                    ? 'text-sage-400 border-b-2 border-sage-400/50 bg-obsidian-700/20'
                    : 'text-oatmeal-500 hover:text-oatmeal-300'
                }`}
              >
                {tab.label} ({tab.count})
              </button>
            ))}
          </div>

          {/* Items */}
          <div className="px-6 py-2 max-h-[300px] overflow-y-auto">
            {activeItems.length === 0 ? (
              <p className="text-center text-sm font-sans text-oatmeal-600 py-4">
                No unmatched {activeTab}.
              </p>
            ) : (
              activeItems.map((doc, idx) => <DocumentRow key={idx} doc={doc} />)
            )}
          </div>
        </div>
      )}
    </div>
  )
}
