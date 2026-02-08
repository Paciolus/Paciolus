'use client'

import { useState, useCallback, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import { VerificationBanner } from '@/components/auth'
import { ToolNav } from '@/components/shared'
import { useMultiPeriodComparison, type AccountMovement, type MovementSummaryResponse } from '@/hooks'

const API_URL = process.env.NEXT_PUBLIC_API_URL
if (!API_URL) {
  throw new Error('Required environment variable NEXT_PUBLIC_API_URL is not set.')
}

// =============================================================================
// TYPES
// =============================================================================

type AuditStatus = 'idle' | 'loading' | 'success' | 'error'

interface PeriodState {
  file: File | null
  status: AuditStatus
  result: Record<string, unknown> | null
  error: string | null
}

// =============================================================================
// CONSTANTS
// =============================================================================

const MOVEMENT_TYPE_LABELS: Record<string, string> = {
  new_account: 'New',
  closed_account: 'Closed',
  sign_change: 'Sign Change',
  increase: 'Increase',
  decrease: 'Decrease',
  unchanged: 'Unchanged',
}

const MOVEMENT_TYPE_COLORS: Record<string, string> = {
  new_account: 'bg-sage-500/20 text-sage-300 border-sage-500/30',
  closed_account: 'bg-clay-500/20 text-clay-300 border-clay-500/30',
  sign_change: 'bg-clay-500/20 text-clay-300 border-clay-500/30',
  increase: 'bg-sage-500/10 text-sage-400 border-sage-500/20',
  decrease: 'bg-clay-500/10 text-clay-400 border-clay-500/20',
  unchanged: 'bg-obsidian-600/30 text-oatmeal-500 border-obsidian-500/30',
}

const SIGNIFICANCE_COLORS: Record<string, string> = {
  material: 'text-clay-400 font-bold',
  significant: 'text-oatmeal-300 font-medium',
  minor: 'text-oatmeal-500',
}

const fadeIn = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { duration: 0.4, ease: 'easeOut' as const } },
}

const stagger = {
  hidden: { opacity: 0 },
  visible: { opacity: 1, transition: { staggerChildren: 0.06 } },
}

const formatCurrency = (val: number) => {
  const abs = Math.abs(val)
  const formatted = abs >= 1000 ? `$${(abs / 1000).toFixed(1)}K` : `$${abs.toFixed(0)}`
  return val < 0 ? `-${formatted}` : formatted
}

// =============================================================================
// SUB-COMPONENTS
// =============================================================================

function FileDropZone({ label, period, onFileSelect, disabled }: {
  label: string
  period: PeriodState
  onFileSelect: (file: File) => void
  disabled: boolean
}) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }, [disabled, onFileSelect])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFileSelect(file)
  }, [onFileSelect])

  return (
    <div className="flex-1 min-w-0">
      <label className="block text-sm font-sans font-medium text-oatmeal-300 mb-2">{label}</label>
      <div
        className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer ${
          disabled ? 'opacity-50 cursor-not-allowed border-obsidian-600/30' :
          isDragging ? 'border-sage-500/60 bg-sage-500/5' :
          period.file ? 'border-sage-500/30 bg-sage-500/5' :
          'border-obsidian-500/40 hover:border-oatmeal-400/40 hover:bg-obsidian-700/30'
        }`}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={() => {
          if (!disabled) {
            const input = document.createElement('input')
            input.type = 'file'
            input.accept = '.csv,.xlsx,.xls'
            input.onchange = (e) => handleFileInput(e as unknown as React.ChangeEvent<HTMLInputElement>)
            input.click()
          }
        }}
      >
        {period.status === 'loading' ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 border-2 border-sage-500/40 border-t-sage-400 rounded-full animate-spin" />
            <span className="text-sm font-sans text-oatmeal-400">Auditing...</span>
          </div>
        ) : period.status === 'success' ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 bg-sage-500/20 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span className="text-sm font-sans text-sage-400">{period.file?.name}</span>
            <span className="text-xs font-sans text-oatmeal-500">Audit complete</span>
          </div>
        ) : period.status === 'error' ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 bg-clay-500/20 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <span className="text-sm font-sans text-clay-400">{period.error || 'Audit failed'}</span>
          </div>
        ) : period.file ? (
          <div className="flex flex-col items-center gap-2">
            <span className="text-sm font-sans text-oatmeal-300">{period.file.name}</span>
            <span className="text-xs font-sans text-oatmeal-500">Ready to audit</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <svg className="w-8 h-8 text-oatmeal-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="text-sm font-sans text-oatmeal-400">Drop CSV or Excel file</span>
            <span className="text-xs font-sans text-oatmeal-600">or click to browse</span>
          </div>
        )}
      </div>
    </div>
  )
}

function MovementBadge({ type }: { type: string }) {
  return (
    <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-sans border ${MOVEMENT_TYPE_COLORS[type] || MOVEMENT_TYPE_COLORS.unchanged}`}>
      {MOVEMENT_TYPE_LABELS[type] || type}
    </span>
  )
}

function MovementSummaryCards({ comparison }: { comparison: MovementSummaryResponse }) {
  const cards = [
    { key: 'new_account', label: 'New Accounts', icon: '+', color: 'sage' },
    { key: 'closed_account', label: 'Closed Accounts', icon: '-', color: 'clay' },
    { key: 'sign_change', label: 'Sign Changes', icon: '~', color: 'clay' },
    { key: 'increase', label: 'Increases', icon: '\u2191', color: 'sage' },
    { key: 'decrease', label: 'Decreases', icon: '\u2193', color: 'clay' },
    { key: 'unchanged', label: 'Unchanged', icon: '=', color: 'oatmeal' },
  ]

  return (
    <motion.div className="grid grid-cols-3 md:grid-cols-6 gap-3" variants={stagger} initial="hidden" animate="visible">
      {cards.map(({ key, label, icon, color }) => (
        <motion.div
          key={key}
          className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-3 text-center"
          variants={fadeIn}
        >
          <div className={`text-2xl font-mono font-bold ${color === 'sage' ? 'text-sage-400' : color === 'clay' ? 'text-clay-400' : 'text-oatmeal-400'}`}>
            {comparison.movements_by_type[key] || 0}
          </div>
          <div className="text-xs font-sans text-oatmeal-500 mt-1">{label}</div>
        </motion.div>
      ))}
    </motion.div>
  )
}

function BudgetSummaryCards({ comparison }: { comparison: MovementSummaryResponse }) {
  if (!comparison.budget_label) return null
  return (
    <div className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl p-4">
      <h3 className="font-serif text-sm text-oatmeal-300 mb-3">
        Budget Variance: {comparison.current_label} vs {comparison.budget_label}
      </h3>
      <div className="grid grid-cols-3 gap-4">
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-sage-400">{comparison.accounts_over_budget || 0}</div>
          <div className="text-xs font-sans text-oatmeal-500">Over Budget</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-clay-400">{comparison.accounts_under_budget || 0}</div>
          <div className="text-xs font-sans text-oatmeal-500">Under Budget</div>
        </div>
        <div className="text-center">
          <div className="text-xl font-mono font-bold text-oatmeal-400">{comparison.accounts_on_budget || 0}</div>
          <div className="text-xs font-sans text-oatmeal-500">On Budget</div>
        </div>
      </div>
    </div>
  )
}

function AccountMovementTable({ movements, filter, hasBudget }: {
  movements: AccountMovement[]
  filter: { type: string; significance: string; search: string }
  hasBudget: boolean
}) {
  const [sortKey, setSortKey] = useState<string>('change_amount')
  const [sortDesc, setSortDesc] = useState(true)

  const filtered = useMemo(() => {
    let result = movements
    if (filter.type !== 'all') result = result.filter(m => m.movement_type === filter.type)
    if (filter.significance !== 'all') result = result.filter(m => m.significance === filter.significance)
    if (filter.search) {
      const q = filter.search.toLowerCase()
      result = result.filter(m => m.account_name.toLowerCase().includes(q))
    }
    return [...result].sort((a, b) => {
      const aVal = sortKey === 'change_amount' ? Math.abs(a.change_amount) :
                   sortKey === 'account_name' ? a.account_name.toLowerCase() :
                   sortKey === 'change_percent' ? Math.abs(a.change_percent || 0) :
                   sortKey === 'budget_variance' ? Math.abs(a.budget_variance?.variance_amount || 0) :
                   Math.abs(a.change_amount)
      const bVal = sortKey === 'change_amount' ? Math.abs(b.change_amount) :
                   sortKey === 'account_name' ? b.account_name.toLowerCase() :
                   sortKey === 'change_percent' ? Math.abs(b.change_percent || 0) :
                   sortKey === 'budget_variance' ? Math.abs(b.budget_variance?.variance_amount || 0) :
                   Math.abs(b.change_amount)
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortDesc ? bVal.localeCompare(aVal) : aVal.localeCompare(bVal)
      }
      return sortDesc ? (bVal as number) - (aVal as number) : (aVal as number) - (bVal as number)
    })
  }, [movements, filter, sortKey, sortDesc])

  const handleSort = (key: string) => {
    if (sortKey === key) setSortDesc(!sortDesc)
    else { setSortKey(key); setSortDesc(true) }
  }

  const SortHeader = ({ label, field }: { label: string; field: string }) => (
    <th
      className="px-3 py-2 text-left text-xs font-sans font-medium text-oatmeal-400 cursor-pointer hover:text-oatmeal-200 select-none"
      onClick={() => handleSort(field)}
    >
      {label} {sortKey === field ? (sortDesc ? '\u25BC' : '\u25B2') : ''}
    </th>
  )

  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead className="border-b border-obsidian-600/40">
          <tr>
            <SortHeader label="Account" field="account_name" />
            <th className="px-3 py-2 text-right text-xs font-sans font-medium text-oatmeal-400">Prior</th>
            <th className="px-3 py-2 text-right text-xs font-sans font-medium text-oatmeal-400">Current</th>
            <SortHeader label="Change" field="change_amount" />
            <SortHeader label="%" field="change_percent" />
            {hasBudget && (
              <>
                <th className="px-3 py-2 text-right text-xs font-sans font-medium text-oatmeal-400">Budget</th>
                <SortHeader label="Bgt Var" field="budget_variance" />
              </>
            )}
            <th className="px-3 py-2 text-center text-xs font-sans font-medium text-oatmeal-400">Movement</th>
            <th className="px-3 py-2 text-center text-xs font-sans font-medium text-oatmeal-400">Significance</th>
          </tr>
        </thead>
        <tbody>
          {filtered.slice(0, 100).map((m, i) => (
            <tr key={`${m.account_name}-${i}`} className="border-b border-obsidian-700/30 hover:bg-obsidian-700/20 transition-colors">
              <td className="px-3 py-2 font-sans text-oatmeal-200 max-w-[200px] truncate" title={m.account_name}>
                {m.account_name}
                {m.is_dormant && <span className="ml-1 text-xs text-oatmeal-600">(dormant)</span>}
              </td>
              <td className="px-3 py-2 text-right font-mono text-oatmeal-400">{formatCurrency(m.prior_balance)}</td>
              <td className="px-3 py-2 text-right font-mono text-oatmeal-400">{formatCurrency(m.current_balance)}</td>
              <td className={`px-3 py-2 text-right font-mono ${m.change_amount > 0 ? 'text-sage-400' : m.change_amount < 0 ? 'text-clay-400' : 'text-oatmeal-500'}`}>
                {m.change_amount > 0 ? '+' : ''}{formatCurrency(m.change_amount)}
              </td>
              <td className={`px-3 py-2 text-right font-mono ${(m.change_percent || 0) > 0 ? 'text-sage-400' : (m.change_percent || 0) < 0 ? 'text-clay-400' : 'text-oatmeal-500'}`}>
                {m.change_percent !== null ? `${m.change_percent > 0 ? '+' : ''}${m.change_percent.toFixed(1)}%` : '--'}
              </td>
              {hasBudget && (
                <>
                  <td className="px-3 py-2 text-right font-mono text-oatmeal-400">
                    {m.budget_variance ? formatCurrency(m.budget_variance.budget_balance) : '--'}
                  </td>
                  <td className={`px-3 py-2 text-right font-mono ${
                    m.budget_variance
                      ? m.budget_variance.variance_amount > 0 ? 'text-sage-400' : m.budget_variance.variance_amount < 0 ? 'text-clay-400' : 'text-oatmeal-500'
                      : 'text-oatmeal-600'
                  }`}>
                    {m.budget_variance
                      ? `${m.budget_variance.variance_amount > 0 ? '+' : ''}${formatCurrency(m.budget_variance.variance_amount)}`
                      : '--'}
                  </td>
                </>
              )}
              <td className="px-3 py-2 text-center"><MovementBadge type={m.movement_type} /></td>
              <td className={`px-3 py-2 text-center text-xs font-sans capitalize ${SIGNIFICANCE_COLORS[m.significance] || ''}`}>
                {m.significance}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
      {filtered.length > 100 && (
        <p className="text-center text-xs text-oatmeal-500 font-sans mt-2">
          Showing 100 of {filtered.length} accounts
        </p>
      )}
      {filtered.length === 0 && (
        <p className="text-center text-sm text-oatmeal-500 font-sans py-8">No accounts match filters</p>
      )}
    </div>
  )
}

function CategoryMovementSection({ comparison, hasBudget }: { comparison: MovementSummaryResponse; hasBudget: boolean }) {
  const [expandedLS, setExpandedLS] = useState<Set<string>>(new Set())

  const toggleLS = (ls: string) => {
    setExpandedLS(prev => {
      const next = new Set(prev)
      if (next.has(ls)) next.delete(ls)
      else next.add(ls)
      return next
    })
  }

  return (
    <div className="space-y-2">
      {comparison.lead_sheet_summaries.map(ls => (
        <div key={ls.lead_sheet} className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-lg overflow-hidden">
          <button
            className="w-full px-4 py-3 flex items-center justify-between hover:bg-obsidian-700/30 transition-colors"
            onClick={() => toggleLS(ls.lead_sheet)}
          >
            <div className="flex items-center gap-3">
              <span className="w-7 h-7 bg-obsidian-600/50 rounded flex items-center justify-center text-xs font-mono font-bold text-oatmeal-300">
                {ls.lead_sheet}
              </span>
              <span className="font-sans text-sm text-oatmeal-200">{ls.lead_sheet_name}</span>
              <span className="text-xs font-sans text-oatmeal-500">({ls.account_count} accounts)</span>
            </div>
            <div className="flex items-center gap-4">
              <span className={`font-mono text-sm ${ls.net_change > 0 ? 'text-sage-400' : ls.net_change < 0 ? 'text-clay-400' : 'text-oatmeal-500'}`}>
                {ls.net_change > 0 ? '+' : ''}{formatCurrency(ls.net_change)}
              </span>
              {hasBudget && ls.budget_variance != null && (
                <span className={`font-mono text-xs ${ls.budget_variance > 0 ? 'text-sage-400/70' : ls.budget_variance < 0 ? 'text-clay-400/70' : 'text-oatmeal-600'}`}>
                  Bgt: {ls.budget_variance > 0 ? '+' : ''}{formatCurrency(ls.budget_variance)}
                </span>
              )}
              <svg className={`w-4 h-4 text-oatmeal-500 transition-transform ${expandedLS.has(ls.lead_sheet) ? 'rotate-180' : ''}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </div>
          </button>
          <AnimatePresence>
            {expandedLS.has(ls.lead_sheet) && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2 }}
                className="overflow-hidden"
              >
                <div className="px-4 pb-3 border-t border-obsidian-700/30">
                  <table className="w-full text-xs mt-2">
                    <thead>
                      <tr className="text-oatmeal-500 font-sans">
                        <th className="text-left py-1 px-2">Account</th>
                        <th className="text-right py-1 px-2">Prior</th>
                        <th className="text-right py-1 px-2">Current</th>
                        <th className="text-right py-1 px-2">Change</th>
                        {hasBudget && <th className="text-right py-1 px-2">Bgt Var</th>}
                        <th className="text-center py-1 px-2">Type</th>
                      </tr>
                    </thead>
                    <tbody>
                      {ls.movements.map((m, i) => (
                        <tr key={i} className="border-b border-obsidian-700/20">
                          <td className="py-1 px-2 font-sans text-oatmeal-300 max-w-[180px] truncate">{m.account_name}</td>
                          <td className="py-1 px-2 text-right font-mono text-oatmeal-400">${Math.abs(m.prior_balance).toLocaleString()}</td>
                          <td className="py-1 px-2 text-right font-mono text-oatmeal-400">${Math.abs(m.current_balance).toLocaleString()}</td>
                          <td className={`py-1 px-2 text-right font-mono ${m.change_amount > 0 ? 'text-sage-400' : m.change_amount < 0 ? 'text-clay-400' : 'text-oatmeal-500'}`}>
                            {m.change_amount > 0 ? '+' : ''}{formatCurrency(m.change_amount)}
                          </td>
                          {hasBudget && (
                            <td className={`py-1 px-2 text-right font-mono ${
                              m.budget_variance
                                ? m.budget_variance.variance_amount > 0 ? 'text-sage-400' : m.budget_variance.variance_amount < 0 ? 'text-clay-400' : 'text-oatmeal-500'
                                : 'text-oatmeal-600'
                            }`}>
                              {m.budget_variance ? `${m.budget_variance.variance_amount > 0 ? '+' : ''}${formatCurrency(m.budget_variance.variance_amount)}` : '--'}
                            </td>
                          )}
                          <td className="py-1 px-2 text-center"><MovementBadge type={m.movement_type} /></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      ))}
    </div>
  )
}

// =============================================================================
// MAIN PAGE
// =============================================================================

export default function MultiPeriodPage() {
  const { user, isAuthenticated, isLoading: authLoading, logout, token } = useAuth()
  // Sprint 103: Engagement integration
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.activeEngagement?.id ?? null
  const { comparison, isComparing, isExporting, error: compareError, compareResults, exportCsv, clear } = useMultiPeriodComparison(engagementId)

  // Sprint 70: Verification gate for diagnostic zone
  const isVerified = user?.is_verified !== false

  // Period state
  const [priorLabel, setPriorLabel] = useState('Prior Period')
  const [currentLabel, setCurrentLabel] = useState('Current Period')
  const [budgetLabel, setBudgetLabel] = useState('Budget')
  const [materialityThreshold, setMaterialityThreshold] = useState(500)
  const [showBudget, setShowBudget] = useState(false)

  const [prior, setPrior] = useState<PeriodState>({ file: null, status: 'idle', result: null, error: null })
  const [current, setCurrent] = useState<PeriodState>({ file: null, status: 'idle', result: null, error: null })
  const [budget, setBudget] = useState<PeriodState>({ file: null, status: 'idle', result: null, error: null })

  // Filters
  const [filterType, setFilterType] = useState('all')
  const [filterSignificance, setFilterSignificance] = useState('all')
  const [filterSearch, setFilterSearch] = useState('')

  const auditFile = useCallback(async (file: File, setPeriod: React.Dispatch<React.SetStateAction<PeriodState>>) => {
    setPeriod(prev => ({ ...prev, file, status: 'loading', result: null, error: null }))

    const formData = new FormData()
    formData.append('file', file)
    formData.append('materiality_threshold', materialityThreshold.toString())

    // Sprint 103: Link to engagement workspace if active
    if (engagementId) {
      formData.append('engagement_id', engagementId.toString())
    }

    try {
      const response = await fetch(`${API_URL}/audit/trial-balance`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: formData,
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => null)
        const msg = typeof errorData?.detail === 'string' ? errorData.detail :
                    typeof errorData?.detail === 'object' ? errorData.detail.message :
                    `Audit failed (${response.status})`
        setPeriod(prev => ({ ...prev, status: 'error', error: msg }))
        return
      }

      const result = await response.json()
      setPeriod(prev => ({ ...prev, status: 'success', result }))
    } catch {
      setPeriod(prev => ({ ...prev, status: 'error', error: 'Network error during audit' }))
    }
  }, [token, materialityThreshold, engagementId])

  const handlePriorFile = useCallback((file: File) => {
    clear()
    auditFile(file, setPrior)
  }, [auditFile, clear])

  const handleCurrentFile = useCallback((file: File) => {
    clear()
    auditFile(file, setCurrent)
  }, [auditFile, clear])

  const handleBudgetFile = useCallback((file: File) => {
    clear()
    auditFile(file, setBudget)
  }, [auditFile, clear])

  const canCompare = prior.status === 'success' && current.status === 'success' && prior.result && current.result
    && (!showBudget || (budget.status === 'success' && budget.result))
  const isProcessing = prior.status === 'loading' || current.status === 'loading' || budget.status === 'loading' || isComparing

  const hasBudgetData = !!comparison?.budget_label

  type AuditResultCast = { lead_sheet_grouping?: { summaries: Array<{ accounts: Array<{ account: string; debit: number; credit: number; type: string }> }> } }

  const handleCompare = useCallback(async () => {
    if (!prior.result || !current.result) return
    const success = await compareResults(
      prior.result as AuditResultCast,
      current.result as AuditResultCast,
      priorLabel,
      currentLabel,
      materialityThreshold,
      token,
      showBudget && budget.result ? budget.result as AuditResultCast : null,
      budgetLabel,
    )

    // Sprint 103: Trigger toast on successful comparison with engagement
    if (success && engagement?.activeEngagement) {
      engagement.refreshToolRuns()
      engagement.triggerLinkToast('Multi-Period Comparison')
    }
  }, [prior.result, current.result, budget.result, priorLabel, currentLabel, budgetLabel, materialityThreshold, token, showBudget, compareResults, engagement])

  const handleExportCsv = useCallback(async () => {
    if (!prior.result || !current.result) return
    await exportCsv(
      prior.result as AuditResultCast,
      current.result as AuditResultCast,
      priorLabel,
      currentLabel,
      materialityThreshold,
      token,
      showBudget && budget.result ? budget.result as AuditResultCast : null,
      budgetLabel,
    )
  }, [prior.result, current.result, budget.result, priorLabel, currentLabel, budgetLabel, materialityThreshold, token, showBudget, exportCsv])

  const handleReset = useCallback(() => {
    setPrior({ file: null, status: 'idle', result: null, error: null })
    setCurrent({ file: null, status: 'idle', result: null, error: null })
    setBudget({ file: null, status: 'idle', result: null, error: null })
    clear()
    setFilterType('all')
    setFilterSignificance('all')
    setFilterSearch('')
  }, [clear])

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      <ToolNav currentTool="multi-period" />

      <div className="pt-24 pb-16 px-6 max-w-6xl mx-auto">
        {/* Hero */}
        <motion.div className="text-center mb-10" initial="hidden" animate="visible" variants={stagger}>
          <motion.div
            className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-6"
            variants={fadeIn}
          >
            <span className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
            <span className="text-sage-300 text-sm font-sans font-medium">Multi-Period Comparison</span>
          </motion.div>
          <motion.h1 className="text-3xl md:text-4xl font-serif font-bold text-oatmeal-200 mb-3" variants={fadeIn}>
            Period-Over-Period Analysis
          </motion.h1>
          <motion.p className="text-oatmeal-400 font-sans max-w-xl mx-auto" variants={fadeIn}>
            Upload two or three trial balance files to compare account movements, detect variances, and analyze budget performance.
          </motion.p>
        </motion.div>

        {/* Sprint 70: Verification Banner for authenticated but unverified users */}
        {isAuthenticated && !isVerified && (
          <VerificationBanner />
        )}

        {!isAuthenticated ? (
          /* Guest CTA */
          <div className="max-w-md mx-auto bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-8 text-center">
            <h2 className="font-serif text-xl text-oatmeal-200 mb-3">Sign in to compare periods</h2>
            <p className="text-sm font-sans text-oatmeal-400 mb-6">
              Multi-Period Comparison requires a verified account for Zero-Storage processing.
            </p>
            <Link
              href="/login"
              className="inline-block px-6 py-3 bg-sage-500/20 border border-sage-500/40 rounded-lg text-sage-300 font-sans text-sm hover:bg-sage-500/30 transition-colors"
            >
              Sign In
            </Link>
          </div>
        ) : !isVerified ? (
          /* Authenticated but unverified CTA */
          <div className="max-w-lg mx-auto bg-obsidian-800/50 border border-obsidian-600/30 rounded-2xl p-10 text-center">
            <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-clay-500/10 border border-clay-500/20 flex items-center justify-center">
              <svg className="w-8 h-8 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h2 className="text-2xl font-serif font-bold text-oatmeal-200 mb-3">Verify Your Email</h2>
            <p className="text-oatmeal-400 font-sans mb-2">
              Multi-Period Comparison requires a verified account.
            </p>
            <p className="text-oatmeal-500 font-sans text-sm">
              Check your inbox for a verification link, or use the banner above to resend.
            </p>
          </div>
        ) : (
          <>
            {/* Upload Section */}
            <motion.section
              className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl p-6 mb-6"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.2 }}
            >
              {/* Period Labels */}
              <div className={`grid gap-4 mb-4 ${showBudget ? 'grid-cols-3' : 'grid-cols-2'}`}>
                <div>
                  <label className="block text-xs font-sans text-oatmeal-500 mb-1">Prior Period Label</label>
                  <input
                    type="text"
                    value={priorLabel}
                    onChange={(e) => setPriorLabel(e.target.value)}
                    className="w-full px-3 py-2 bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-sm font-sans text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:border-sage-500/40"
                    placeholder="e.g. FY2024"
                  />
                </div>
                <div>
                  <label className="block text-xs font-sans text-oatmeal-500 mb-1">Current Period Label</label>
                  <input
                    type="text"
                    value={currentLabel}
                    onChange={(e) => setCurrentLabel(e.target.value)}
                    className="w-full px-3 py-2 bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-sm font-sans text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:border-sage-500/40"
                    placeholder="e.g. FY2025"
                  />
                </div>
                {showBudget && (
                  <div>
                    <label className="block text-xs font-sans text-oatmeal-500 mb-1">Budget/Forecast Label</label>
                    <input
                      type="text"
                      value={budgetLabel}
                      onChange={(e) => setBudgetLabel(e.target.value)}
                      className="w-full px-3 py-2 bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-sm font-sans text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:border-sage-500/40"
                      placeholder="e.g. Budget 2025"
                    />
                  </div>
                )}
              </div>

              {/* File Upload */}
              <div className={`grid gap-4 mb-4 ${showBudget ? 'grid-cols-3' : 'grid-cols-2'}`}>
                <FileDropZone label="Prior Period" period={prior} onFileSelect={handlePriorFile} disabled={isProcessing} />
                <FileDropZone label="Current Period" period={current} onFileSelect={handleCurrentFile} disabled={isProcessing} />
                {showBudget && (
                  <FileDropZone label="Budget / Forecast" period={budget} onFileSelect={handleBudgetFile} disabled={isProcessing} />
                )}
              </div>

              {/* Actions */}
              <div className="flex items-center justify-between flex-wrap gap-3">
                <div className="flex items-center gap-4">
                  <div className="flex items-center gap-2">
                    <label className="text-xs font-sans text-oatmeal-500">Materiality $</label>
                    <input
                      type="number"
                      value={materialityThreshold}
                      onChange={(e) => setMaterialityThreshold(Number(e.target.value) || 0)}
                      className="w-24 px-2 py-1.5 bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-sm font-mono text-oatmeal-200 focus:outline-none focus:border-sage-500/40"
                      min={0}
                    />
                  </div>
                  <button
                    onClick={() => {
                      setShowBudget(!showBudget)
                      if (showBudget) setBudget({ file: null, status: 'idle', result: null, error: null })
                    }}
                    className={`px-3 py-1.5 text-xs font-sans rounded-lg border transition-all ${
                      showBudget
                        ? 'bg-sage-500/10 border-sage-500/30 text-sage-400'
                        : 'bg-obsidian-700/30 border-obsidian-500/30 text-oatmeal-500 hover:text-oatmeal-300'
                    }`}
                  >
                    {showBudget ? 'Remove Budget' : '+ Add Budget/Forecast'}
                  </button>
                </div>
                <div className="flex gap-3">
                  <button
                    onClick={handleReset}
                    className="px-4 py-2 text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
                  >
                    Reset
                  </button>
                  <button
                    onClick={handleCompare}
                    disabled={!canCompare || isProcessing}
                    className={`px-6 py-2 rounded-lg text-sm font-sans font-medium transition-all ${
                      canCompare && !isProcessing
                        ? 'bg-sage-500/20 border border-sage-500/40 text-sage-300 hover:bg-sage-500/30'
                        : 'bg-obsidian-600/30 border border-obsidian-500/20 text-oatmeal-600 cursor-not-allowed'
                    }`}
                  >
                    {isComparing ? 'Comparing...' : showBudget ? 'Compare 3 Periods' : 'Compare Periods'}
                  </button>
                </div>
              </div>

              {compareError && (
                <div className="mt-3 px-4 py-2 border-l-4 border-l-clay-500 bg-clay-500/5 rounded">
                  <span className="text-sm font-sans text-clay-400">{compareError}</span>
                </div>
              )}
            </motion.section>

            {/* Results */}
            <AnimatePresence>
              {comparison && (
                <motion.div
                  initial={{ opacity: 0, y: 30 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0 }}
                  transition={{ duration: 0.4 }}
                  className="space-y-6"
                >
                  {/* Summary Header + Export */}
                  <div className="flex items-center justify-between flex-wrap gap-3">
                    <div>
                      <h2 className="font-serif text-xl text-oatmeal-200">
                        {comparison.prior_label} vs {comparison.current_label}
                        {comparison.budget_label && ` vs ${comparison.budget_label}`}
                      </h2>
                      <p className="text-sm font-sans text-oatmeal-500">
                        {comparison.total_accounts} accounts analyzed
                        {comparison.dormant_accounts.length > 0 && ` \u00B7 ${comparison.dormant_accounts.length} dormant`}
                      </p>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-sans text-oatmeal-500">
                        {comparison.movements_by_significance.material || 0} material \u00B7 {comparison.movements_by_significance.significant || 0} significant
                      </span>
                      <button
                        onClick={handleExportCsv}
                        disabled={isExporting}
                        className="px-4 py-1.5 text-xs font-sans font-medium bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-oatmeal-300 hover:bg-obsidian-700/70 hover:text-oatmeal-200 transition-all disabled:opacity-50"
                      >
                        {isExporting ? 'Exporting...' : 'Export CSV'}
                      </button>
                    </div>
                  </div>

                  {/* Movement Summary Cards */}
                  <MovementSummaryCards comparison={comparison} />

                  {/* Budget Summary (Sprint 63) */}
                  <BudgetSummaryCards comparison={comparison} />

                  {/* Filters + Movement Table */}
                  <section className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl overflow-hidden">
                    <div className="px-4 py-3 border-b border-obsidian-600/20 flex flex-wrap items-center gap-3">
                      <select
                        value={filterType}
                        onChange={(e) => setFilterType(e.target.value)}
                        className="px-3 py-1.5 bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-xs font-sans text-oatmeal-300 focus:outline-none"
                      >
                        <option value="all">All Types</option>
                        {Object.entries(MOVEMENT_TYPE_LABELS).map(([k, v]) => (
                          <option key={k} value={k}>{v}</option>
                        ))}
                      </select>
                      <select
                        value={filterSignificance}
                        onChange={(e) => setFilterSignificance(e.target.value)}
                        className="px-3 py-1.5 bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-xs font-sans text-oatmeal-300 focus:outline-none"
                      >
                        <option value="all">All Significance</option>
                        <option value="material">Material</option>
                        <option value="significant">Significant</option>
                        <option value="minor">Minor</option>
                      </select>
                      <input
                        type="text"
                        value={filterSearch}
                        onChange={(e) => setFilterSearch(e.target.value)}
                        placeholder="Search accounts..."
                        className="flex-1 min-w-[150px] px-3 py-1.5 bg-obsidian-700/50 border border-obsidian-500/30 rounded-lg text-xs font-sans text-oatmeal-200 placeholder-oatmeal-600 focus:outline-none focus:border-sage-500/40"
                      />
                    </div>
                    <AccountMovementTable
                      movements={comparison.all_movements}
                      filter={{ type: filterType, significance: filterSignificance, search: filterSearch }}
                      hasBudget={hasBudgetData}
                    />
                  </section>

                  {/* Lead Sheet Grouping */}
                  <section>
                    <h3 className="font-serif text-lg text-oatmeal-200 mb-3">By Lead Sheet</h3>
                    <CategoryMovementSection comparison={comparison} hasBudget={hasBudgetData} />
                  </section>

                  {/* Zero-Storage Notice */}
                  <div className="flex items-center gap-2 px-4 py-2 rounded-lg bg-sage-500/5 border border-sage-500/10">
                    <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
                    <span className="text-xs font-sans text-sage-400/80">
                      Zero-Storage: All trial balances processed in memory. No data stored.
                    </span>
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </>
        )}
      </div>
    </main>
  )
}
