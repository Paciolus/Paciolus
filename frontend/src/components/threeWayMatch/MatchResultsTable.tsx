'use client'

import { useState, useMemo } from 'react'
import type { ThreeWayMatchData } from '@/types/threeWayMatch'
import { MATCH_TYPE_LABELS, MATCH_TYPE_COLORS, VARIANCE_SEVERITY_COLORS } from '@/types/threeWayMatch'

interface MatchResultsTableProps {
  fullMatches: ThreeWayMatchData[]
  partialMatches: ThreeWayMatchData[]
}

const fmt = (n: number) => n.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
const PAGE_SIZE = 25

type SortField = 'vendor' | 'po_amount' | 'inv_amount' | 'variance' | 'confidence' | 'match_type'
type SortDir = 'asc' | 'desc'
type FilterType = 'all' | 'exact_po' | 'fuzzy' | 'partial'

export function MatchResultsTable({ fullMatches, partialMatches }: MatchResultsTableProps) {
  const [page, setPage] = useState(0)
  const [sortField, setSortField] = useState<SortField>('confidence')
  const [sortDir, setSortDir] = useState<SortDir>('desc')
  const [filterType, setFilterType] = useState<FilterType>('all')
  const [search, setSearch] = useState('')

  const allMatches = useMemo(() => [...fullMatches, ...partialMatches], [fullMatches, partialMatches])

  const filtered = useMemo(() => {
    let items = allMatches
    if (filterType !== 'all') {
      items = items.filter(m => m.match_type === filterType)
    }
    if (search) {
      const q = search.toLowerCase()
      items = items.filter(m =>
        (m.po?.vendor || '').toLowerCase().includes(q) ||
        (m.po?.po_number || '').toLowerCase().includes(q) ||
        (m.invoice?.invoice_number || '').toLowerCase().includes(q) ||
        (m.receipt?.receipt_number || '').toLowerCase().includes(q)
      )
    }
    return items
  }, [allMatches, filterType, search])

  const sorted = useMemo(() => {
    const items = [...filtered]
    items.sort((a, b) => {
      let cmp = 0
      switch (sortField) {
        case 'vendor': cmp = (a.po?.vendor || '').localeCompare(b.po?.vendor || ''); break
        case 'po_amount': cmp = (a.po?.total_amount || 0) - (b.po?.total_amount || 0); break
        case 'inv_amount': cmp = (a.invoice?.total_amount || 0) - (b.invoice?.total_amount || 0); break
        case 'variance': {
          const av = a.variances.reduce((s, v) => s + v.variance_amount, 0)
          const bv = b.variances.reduce((s, v) => s + v.variance_amount, 0)
          cmp = av - bv
          break
        }
        case 'confidence': cmp = a.match_confidence - b.match_confidence; break
        case 'match_type': cmp = a.match_type.localeCompare(b.match_type); break
      }
      return sortDir === 'desc' ? -cmp : cmp
    })
    return items
  }, [filtered, sortField, sortDir])

  const paged = useMemo(() => sorted.slice(page * PAGE_SIZE, (page + 1) * PAGE_SIZE), [sorted, page])
  const totalPages = Math.ceil(sorted.length / PAGE_SIZE)

  const toggleSort = (field: SortField) => {
    if (sortField === field) setSortDir(d => d === 'asc' ? 'desc' : 'asc')
    else { setSortField(field); setSortDir('desc') }
    setPage(0)
  }

  const SortIcon = ({ field }: { field: SortField }) => (
    <span className="ml-1 text-oatmeal-600">{sortField === field ? (sortDir === 'asc' ? '↑' : '↓') : ''}</span>
  )

  if (allMatches.length === 0) {
    return (
      <div className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl p-8 text-center">
        <p className="font-sans text-sm text-oatmeal-500">No matches found.</p>
      </div>
    )
  }

  return (
    <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl overflow-hidden">
      {/* Filters */}
      <div className="flex flex-wrap items-center gap-3 p-4 border-b border-obsidian-600/20">
        <input
          type="text"
          placeholder="Search vendor, PO#, invoice#..."
          value={search}
          onChange={e => { setSearch(e.target.value); setPage(0) }}
          className="flex-1 min-w-[200px] bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg px-3 py-2 text-sm font-sans text-oatmeal-300 placeholder:text-oatmeal-600 focus:outline-none focus:border-sage-500/50"
        />
        <select
          value={filterType}
          onChange={e => { setFilterType(e.target.value as FilterType); setPage(0) }}
          className="bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg px-3 py-2 text-sm font-sans text-oatmeal-300 focus:outline-none focus:border-sage-500/50"
        >
          <option value="all">All Types</option>
          <option value="exact_po">Exact PO#</option>
          <option value="fuzzy">Fuzzy Match</option>
          <option value="partial">Partial Match</option>
        </select>
        <span className="text-xs font-sans text-oatmeal-600">{sorted.length} of {allMatches.length} matches</span>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-obsidian-600/20 text-left">
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400 cursor-pointer" onClick={() => toggleSort('vendor')}>
                Vendor<SortIcon field="vendor" />
              </th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400">PO#</th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400">Invoice#</th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400">Receipt#</th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400 text-right cursor-pointer" onClick={() => toggleSort('po_amount')}>
                PO Amt<SortIcon field="po_amount" />
              </th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400 text-right cursor-pointer" onClick={() => toggleSort('inv_amount')}>
                Inv Amt<SortIcon field="inv_amount" />
              </th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400 text-right cursor-pointer" onClick={() => toggleSort('variance')}>
                Variance<SortIcon field="variance" />
              </th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400 cursor-pointer" onClick={() => toggleSort('match_type')}>
                Type<SortIcon field="match_type" />
              </th>
              <th className="px-4 py-3 font-sans font-medium text-oatmeal-400 text-right cursor-pointer" onClick={() => toggleSort('confidence')}>
                Conf<SortIcon field="confidence" />
              </th>
            </tr>
          </thead>
          <tbody>
            {paged.map((match, idx) => {
              const totalVariance = match.variances.reduce((s, v) => s + v.variance_amount, 0)
              const maxSeverity = match.variances.length > 0
                ? match.variances.reduce((max, v) => v.severity === 'high' ? 'high' : (v.severity === 'medium' && max !== 'high' ? 'medium' : max), 'low' as string)
                : null
              return (
                <tr
                  key={idx}
                  className="border-b border-obsidian-600/10 hover:bg-obsidian-700/20 transition-colors"
                >
                  <td className="px-4 py-3 font-sans text-oatmeal-300">
                    {match.po?.vendor || match.invoice?.vendor || '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-oatmeal-400 text-xs">
                    {match.po?.po_number || '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-oatmeal-400 text-xs">
                    {match.invoice?.invoice_number || '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-oatmeal-400 text-xs">
                    {match.receipt?.receipt_number || '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-oatmeal-300 text-right">
                    {match.po ? `$${fmt(match.po.total_amount)}` : '—'}
                  </td>
                  <td className="px-4 py-3 font-mono text-oatmeal-300 text-right">
                    {match.invoice ? `$${fmt(match.invoice.total_amount)}` : '—'}
                  </td>
                  <td className={`px-4 py-3 font-mono text-right ${
                    maxSeverity === 'high' ? 'text-clay-400' :
                    maxSeverity === 'medium' ? 'text-oatmeal-400' :
                    'text-sage-400'
                  }`}>
                    {totalVariance > 0 ? `$${fmt(totalVariance)}` : '—'}
                  </td>
                  <td className="px-4 py-3">
                    <span className={`inline-block px-2 py-0.5 rounded text-xs font-sans border ${MATCH_TYPE_COLORS[match.match_type]}`}>
                      {MATCH_TYPE_LABELS[match.match_type]}
                    </span>
                  </td>
                  <td className="px-4 py-3 font-mono text-oatmeal-400 text-right text-xs">
                    {(match.match_confidence * 100).toFixed(0)}%
                  </td>
                </tr>
              )
            })}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between px-4 py-3 border-t border-obsidian-600/20">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1 bg-obsidian-700 border border-obsidian-500/30 rounded text-xs font-sans text-oatmeal-300 disabled:opacity-40"
          >
            Previous
          </button>
          <span className="text-xs font-sans text-oatmeal-500">
            Page {page + 1} of {totalPages}
          </span>
          <button
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            className="px-3 py-1 bg-obsidian-700 border border-obsidian-500/30 rounded text-xs font-sans text-oatmeal-300 disabled:opacity-40"
          >
            Next
          </button>
        </div>
      )}
    </div>
  )
}
