'use client'

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import type { ReconciliationMatchData, MatchType } from '@/types/bankRec'
import { MATCH_TYPE_LABELS, MATCH_TYPE_COLORS, MATCH_TYPE_BORDER_COLORS } from '@/types/bankRec'

const ITEMS_PER_PAGE = 25

interface BankRecMatchTableProps {
  matches: ReconciliationMatchData[]
}

type SortField = 'date' | 'description' | 'bank_amount' | 'ledger_amount' | 'type'
type SortDir = 'asc' | 'desc'

const TYPE_ORDER: Record<MatchType, number> = { bank_only: 3, ledger_only: 2, matched: 1 }

function matchTypeBadge(type: MatchType) {
  return (
    <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium border ${MATCH_TYPE_COLORS[type]}`}>
      {MATCH_TYPE_LABELS[type]}
    </span>
  )
}

function getCategoryLabel(m: ReconciliationMatchData): { label: string; color: string } | null {
  if (m.match_type === 'matched') return null
  const amount = m.bank_txn?.amount ?? m.ledger_txn?.amount ?? 0
  if (m.match_type === 'bank_only') {
    return amount > 0
      ? { label: 'Outstanding Deposit', color: 'bg-sage-50 text-sage-700 border-sage-200' }
      : { label: 'Outstanding Check', color: 'bg-clay-50 text-clay-700 border-clay-200' }
  }
  // ledger_only
  return amount > 0
    ? { label: 'Deposit in Transit', color: 'bg-sage-50 text-sage-700 border-sage-200' }
    : { label: 'Unrecorded Check', color: 'bg-clay-50 text-clay-700 border-clay-200' }
}

function getDate(m: ReconciliationMatchData): string {
  return m.bank_txn?.date || m.ledger_txn?.date || ''
}

function getDescription(m: ReconciliationMatchData): string {
  return m.bank_txn?.description || m.ledger_txn?.description || ''
}

export function BankRecMatchTable({ matches }: BankRecMatchTableProps) {
  const [searchQuery, setSearchQuery] = useState('')
  const [typeFilter, setTypeFilter] = useState<MatchType | 'all'>('all')
  const [sortField, setSortField] = useState<SortField>('type')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [page, setPage] = useState(0)

  const filtered = useMemo(() => {
    let items = [...matches]

    if (typeFilter !== 'all') {
      items = items.filter(m => m.match_type === typeFilter)
    }

    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase()
      items = items.filter(m =>
        (m.bank_txn?.description || '').toLowerCase().includes(q) ||
        (m.ledger_txn?.description || '').toLowerCase().includes(q) ||
        (m.bank_txn?.reference || '').toLowerCase().includes(q) ||
        (m.ledger_txn?.reference || '').toLowerCase().includes(q)
      )
    }

    items.sort((a, b) => {
      let cmp = 0
      switch (sortField) {
        case 'type':
          cmp = TYPE_ORDER[a.match_type] - TYPE_ORDER[b.match_type]
          break
        case 'bank_amount':
          cmp = Math.abs(a.bank_txn?.amount || 0) - Math.abs(b.bank_txn?.amount || 0)
          break
        case 'ledger_amount':
          cmp = Math.abs(a.ledger_txn?.amount || 0) - Math.abs(b.ledger_txn?.amount || 0)
          break
        case 'date':
          cmp = getDate(a).localeCompare(getDate(b))
          break
        case 'description':
          cmp = getDescription(a).localeCompare(getDescription(b))
          break
      }
      return sortDir === 'desc' ? -cmp : cmp
    })

    return items
  }, [matches, typeFilter, searchQuery, sortField, sortDir])

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE)
  const paged = filtered.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE)

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    } else {
      setSortField(field)
      setSortDir('desc')
    }
    setPage(0)
  }

  const sortIndicator = (field: SortField) =>
    sortField === field ? (sortDir === 'desc' ? ' \u25BC' : ' \u25B2') : ''

  if (matches.length === 0) {
    return (
      <div className="bg-surface-card border border-theme rounded-xl p-8 text-center shadow-theme-card">
        <p className="font-sans text-content-tertiary">No transactions to display.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Filter Bar */}
      <div className="flex flex-wrap items-center gap-3 bg-surface-card border border-theme rounded-xl p-4 shadow-theme-card">
        <input
          type="text"
          placeholder="Search description, reference..."
          value={searchQuery}
          onChange={e => { setSearchQuery(e.target.value); setPage(0) }}
          className="flex-1 min-w-[200px] bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder-content-tertiary focus:outline-none focus:border-sage-500"
        />
        <select
          value={typeFilter}
          onChange={e => { setTypeFilter(e.target.value as MatchType | 'all'); setPage(0) }}
          className="bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary focus:outline-none focus:border-sage-500"
        >
          <option value="all">All Types</option>
          <option value="matched">Matched</option>
          <option value="bank_only">Bank Only</option>
          <option value="ledger_only">Ledger Only</option>
        </select>
        <span className="font-sans text-xs text-content-tertiary">
          {filtered.length} of {matches.length} items
        </span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto bg-surface-card border border-theme rounded-xl shadow-theme-card">
        <table className="w-full text-left">
          <thead>
            <tr className="border-b border-theme-divider">
              {([
                { field: 'date' as SortField, label: 'Date' },
                { field: 'description' as SortField, label: 'Description' },
                { field: 'bank_amount' as SortField, label: 'Bank Amount' },
                { field: 'ledger_amount' as SortField, label: 'Ledger Amount' },
                { field: 'type' as SortField, label: 'Type' },
              ]).map(col => (
                <th
                  key={col.field}
                  onClick={() => handleSort(col.field)}
                  className="px-4 py-3 font-serif text-xs text-content-secondary cursor-pointer hover:text-content-primary select-none"
                >
                  {col.label}{sortIndicator(col.field)}
                </th>
              ))}
              <th className="px-4 py-3 font-serif text-xs text-content-secondary select-none">Category</th>
            </tr>
          </thead>
          <tbody>
            {paged.map((m, i) => (
              <motion.tr
                key={`${m.match_type}-${m.bank_txn?.row_number || 0}-${m.ledger_txn?.row_number || 0}-${i}`}
                initial={false}
                className={`border-b border-theme-divider border-l-4 ${MATCH_TYPE_BORDER_COLORS[m.match_type]} hover:bg-surface-card-secondary transition-colors`}
              >
                <td className="px-4 py-3 font-mono text-xs text-content-tertiary">
                  {m.bank_txn?.date || m.ledger_txn?.date || '\u2014'}
                </td>
                <td className="px-4 py-3">
                  <span className="font-sans text-sm text-content-primary line-clamp-1">
                    {m.bank_txn?.description || m.ledger_txn?.description || '\u2014'}
                  </span>
                  <span className="flex items-center gap-2 mt-0.5">
                    {(m.bank_txn?.row_number || m.ledger_txn?.row_number) ? (
                      <span className="font-mono text-[10px] text-content-tertiary">
                        Row {m.bank_txn?.row_number || m.ledger_txn?.row_number}
                      </span>
                    ) : null}
                    {(m.bank_txn?.reference || m.ledger_txn?.reference) && (
                      <span className="font-mono text-[10px] text-content-tertiary">
                        Ref: {m.bank_txn?.reference || m.ledger_txn?.reference}
                      </span>
                    )}
                  </span>
                </td>
                <td className="px-4 py-3 font-mono text-sm text-content-primary text-right">
                  {m.bank_txn
                    ? `$${Math.abs(m.bank_txn.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                    : '\u2014'}
                </td>
                <td className="px-4 py-3 font-mono text-sm text-content-primary text-right">
                  {m.ledger_txn
                    ? `$${Math.abs(m.ledger_txn.amount).toLocaleString(undefined, { minimumFractionDigits: 2 })}`
                    : '\u2014'}
                </td>
                <td className="px-4 py-3">
                  {matchTypeBadge(m.match_type)}
                </td>
                <td className="px-4 py-3">
                  {(() => {
                    const cat = getCategoryLabel(m)
                    return cat ? (
                      <span className={`px-2 py-0.5 rounded text-[10px] font-sans font-medium border ${cat.color}`}>
                        {cat.label}
                      </span>
                    ) : null
                  })()}
                </td>
              </motion.tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 bg-surface-card border border-oatmeal-300 rounded-xl text-content-secondary font-sans text-sm disabled:opacity-30 hover:bg-surface-card-secondary transition-colors"
          >
            Previous
          </button>
          <span className="font-sans text-xs text-content-tertiary">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1.5 bg-surface-card border border-oatmeal-300 rounded-xl text-content-secondary font-sans text-sm disabled:opacity-30 hover:bg-surface-card-secondary transition-colors"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
