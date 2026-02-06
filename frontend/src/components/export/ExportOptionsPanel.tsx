'use client'

import { useState } from 'react'
import { motion, AnimatePresence } from 'framer-motion'

interface AuditResultForExport {
  status: string
  balanced: boolean
  total_debits: number
  total_credits: number
  difference: number
  row_count: number
  message: string
  abnormal_balances: any[]
  has_risk_alerts: boolean
  materiality_threshold: number
  material_count: number
  immaterial_count: number
  classification_summary?: any
  column_detection?: any
  risk_summary?: any
  is_consolidated?: boolean
  sheet_count?: number
  selected_sheets?: string[]
  sheet_results?: any
  analytics?: any
}

interface WorkpaperFields {
  prepared_by: string
  reviewed_by: string
  workpaper_date: string
}

interface ExportOptionsPanelProps {
  auditResult: AuditResultForExport
  filename: string
  disabled?: boolean
  token?: string | null
}

const API_URL = process.env.NEXT_PUBLIC_API_URL

type ExportFormat = 'pdf' | 'excel' | 'csv-tb' | 'csv-anomalies'

/**
 * ExportOptionsPanel - Sprint 53/54 Professional Export Interface
 *
 * Provides workpaper signoff fields (Prepared By, Reviewed By, Date)
 * and export buttons for PDF, Excel, and CSV formats.
 *
 * Features:
 * - Workpaper signoff fields for professional documentation
 * - PDF and Excel export options (with signoff)
 * - CSV export for trial balance and anomalies (Sprint 54)
 * - Reference numbers included in exports
 * - Oat & Obsidian design system
 */
export function ExportOptionsPanel({
  auditResult,
  filename,
  disabled = false,
  token,
}: ExportOptionsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  const [workpaperFields, setWorkpaperFields] = useState<WorkpaperFields>({
    prepared_by: '',
    reviewed_by: '',
    workpaper_date: new Date().toISOString().split('T')[0],
  })
  const [isExporting, setIsExporting] = useState<ExportFormat | null>(null)
  const [error, setError] = useState<string | null>(null)

  const handleFieldChange = (field: keyof WorkpaperFields, value: string) => {
    setWorkpaperFields(prev => ({ ...prev, [field]: value }))
  }

  const handleExport = async (format: ExportFormat) => {
    if (isExporting || disabled) return

    setIsExporting(format)
    setError(null)

    try {
      const requestBody = {
        ...auditResult,
        filename,
        // Sprint 53: Include workpaper fields (for PDF/Excel)
        prepared_by: workpaperFields.prepared_by || null,
        reviewed_by: workpaperFields.reviewed_by || null,
        workpaper_date: workpaperFields.workpaper_date || null,
      }

      // Sprint 54: Map format to endpoint
      const endpointMap: Record<ExportFormat, string> = {
        'pdf': '/export/pdf',
        'excel': '/export/excel',
        'csv-tb': '/export/csv/trial-balance',
        'csv-anomalies': '/export/csv/anomalies',
      }
      const endpoint = endpointMap[format]

      const response = await fetch(`${API_URL}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        },
        body: JSON.stringify(requestBody),
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        const detail = errorData.detail
        const msg = typeof detail === 'object' && detail !== null
          ? (detail.message || detail.code || 'Failed to generate export')
          : (detail || 'Failed to generate export')
        throw new Error(msg)
      }

      const blob = await response.blob()
      const contentDisposition = response.headers.get('Content-Disposition')

      // Default filenames by format
      const defaultFilenames: Record<ExportFormat, string> = {
        'pdf': 'Paciolus_Report.pdf',
        'excel': 'Paciolus_Workpaper.xlsx',
        'csv-tb': 'Paciolus_TrialBalance.csv',
        'csv-anomalies': 'Paciolus_Anomalies.csv',
      }
      let downloadFilename = defaultFilenames[format]

      if (contentDisposition) {
        const match = contentDisposition.match(/filename="(.+)"/)
        if (match) {
          downloadFilename = match[1]
        }
      }

      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = downloadFilename
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)

    } catch (err) {
      console.error(`${format} export error:`, err)
      setError(err instanceof Error ? err.message : `Failed to generate export`)
    } finally {
      setIsExporting(null)
    }
  }

  const spinnerVariants = {
    animate: {
      rotate: 360,
      transition: { duration: 1, repeat: Infinity, ease: 'linear' as const },
    },
  }

  return (
    <div className="bg-obsidian-800/50 border border-obsidian-600/50 rounded-xl p-4">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        disabled={disabled}
        className="w-full flex items-center justify-between text-left"
      >
        <div className="flex items-center gap-3">
          <div className="p-2 bg-sage-500/10 rounded-lg">
            <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
              />
            </svg>
          </div>
          <div>
            <h3 className="font-serif text-oatmeal-200 text-sm font-medium">Export Diagnostic</h3>
            <p className="text-oatmeal-500 text-xs font-sans">PDF, Excel, or CSV formats</p>
          </div>
        </div>
        <motion.svg
          animate={{ rotate: isExpanded ? 180 : 0 }}
          className="w-5 h-5 text-oatmeal-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </motion.svg>
      </button>

      {/* Expanded Content */}
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="overflow-hidden"
          >
            <div className="mt-4 pt-4 border-t border-obsidian-600/50 space-y-4">
              {/* Workpaper Fields */}
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
                <div>
                  <label className="block text-oatmeal-400 text-xs font-sans mb-1">
                    Prepared By
                  </label>
                  <input
                    type="text"
                    value={workpaperFields.prepared_by}
                    onChange={(e) => handleFieldChange('prepared_by', e.target.value)}
                    placeholder="Your name"
                    disabled={disabled}
                    className="w-full px-3 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg
                      text-oatmeal-200 text-sm font-sans placeholder-oatmeal-600
                      focus:outline-none focus:border-sage-500/50 focus:ring-1 focus:ring-sage-500/20
                      disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="block text-oatmeal-400 text-xs font-sans mb-1">
                    Reviewed By
                  </label>
                  <input
                    type="text"
                    value={workpaperFields.reviewed_by}
                    onChange={(e) => handleFieldChange('reviewed_by', e.target.value)}
                    placeholder="Reviewer name"
                    disabled={disabled}
                    className="w-full px-3 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg
                      text-oatmeal-200 text-sm font-sans placeholder-oatmeal-600
                      focus:outline-none focus:border-sage-500/50 focus:ring-1 focus:ring-sage-500/20
                      disabled:opacity-50"
                  />
                </div>
                <div>
                  <label className="block text-oatmeal-400 text-xs font-sans mb-1">
                    Date
                  </label>
                  <input
                    type="date"
                    value={workpaperFields.workpaper_date}
                    onChange={(e) => handleFieldChange('workpaper_date', e.target.value)}
                    disabled={disabled}
                    className="w-full px-3 py-2 bg-obsidian-700 border border-obsidian-600 rounded-lg
                      text-oatmeal-200 text-sm font-sans
                      focus:outline-none focus:border-sage-500/50 focus:ring-1 focus:ring-sage-500/20
                      disabled:opacity-50"
                  />
                </div>
              </div>

              {/* Export Buttons - Primary */}
              <div className="flex flex-wrap gap-3">
                {/* PDF Button */}
                <motion.button
                  onClick={() => handleExport('pdf')}
                  disabled={disabled || isExporting !== null}
                  whileHover={{ scale: disabled || isExporting ? 1 : 1.02 }}
                  whileTap={{ scale: disabled || isExporting ? 1 : 0.98 }}
                  className={`flex-1 min-w-[140px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                    font-sans text-sm font-medium transition-colors
                    ${disabled || isExporting
                      ? 'bg-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                      : 'bg-sage-500 text-obsidian-900 hover:bg-sage-400'
                    }`}
                >
                  {isExporting === 'pdf' ? (
                    <>
                      <motion.svg variants={spinnerVariants} animate="animate" className="w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </motion.svg>
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M12 10v6m0 0l-3-3m3 3l3-3M6 19a2 2 0 01-2-2V7a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H6z"
                        />
                      </svg>
                      <span>Export PDF</span>
                    </>
                  )}
                </motion.button>

                {/* Excel Button */}
                <motion.button
                  onClick={() => handleExport('excel')}
                  disabled={disabled || isExporting !== null}
                  whileHover={{ scale: disabled || isExporting ? 1 : 1.02 }}
                  whileTap={{ scale: disabled || isExporting ? 1 : 0.98 }}
                  className={`flex-1 min-w-[140px] flex items-center justify-center gap-2 px-4 py-2.5 rounded-lg
                    font-sans text-sm font-medium transition-colors border
                    ${disabled || isExporting
                      ? 'bg-obsidian-700 border-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                      : 'bg-obsidian-700 border-sage-500/30 text-sage-400 hover:bg-obsidian-600 hover:border-sage-500/50'
                    }`}
                >
                  {isExporting === 'excel' ? (
                    <>
                      <motion.svg variants={spinnerVariants} animate="animate" className="w-4 h-4" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </motion.svg>
                      <span>Generating...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                        />
                      </svg>
                      <span>Export Excel</span>
                    </>
                  )}
                </motion.button>
              </div>

              {/* CSV Export Buttons - Sprint 54 */}
              <div className="flex flex-wrap gap-3">
                {/* CSV Trial Balance */}
                <motion.button
                  onClick={() => handleExport('csv-tb')}
                  disabled={disabled || isExporting !== null}
                  whileHover={{ scale: disabled || isExporting ? 1 : 1.02 }}
                  whileTap={{ scale: disabled || isExporting ? 1 : 0.98 }}
                  className={`flex-1 min-w-[140px] flex items-center justify-center gap-2 px-4 py-2 rounded-lg
                    font-sans text-xs font-medium transition-colors border
                    ${disabled || isExporting
                      ? 'bg-obsidian-700 border-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                      : 'bg-obsidian-700/50 border-obsidian-600 text-oatmeal-400 hover:bg-obsidian-700 hover:text-oatmeal-300'
                    }`}
                >
                  {isExporting === 'csv-tb' ? (
                    <>
                      <motion.svg variants={spinnerVariants} animate="animate" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </motion.svg>
                      <span>Exporting...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      <span>CSV Trial Balance</span>
                    </>
                  )}
                </motion.button>

                {/* CSV Anomalies */}
                <motion.button
                  onClick={() => handleExport('csv-anomalies')}
                  disabled={disabled || isExporting !== null}
                  whileHover={{ scale: disabled || isExporting ? 1 : 1.02 }}
                  whileTap={{ scale: disabled || isExporting ? 1 : 0.98 }}
                  className={`flex-1 min-w-[140px] flex items-center justify-center gap-2 px-4 py-2 rounded-lg
                    font-sans text-xs font-medium transition-colors border
                    ${disabled || isExporting
                      ? 'bg-obsidian-700 border-obsidian-600 text-oatmeal-500 cursor-not-allowed'
                      : 'bg-obsidian-700/50 border-obsidian-600 text-oatmeal-400 hover:bg-obsidian-700 hover:text-oatmeal-300'
                    }`}
                >
                  {isExporting === 'csv-anomalies' ? (
                    <>
                      <motion.svg variants={spinnerVariants} animate="animate" className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24">
                        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                      </motion.svg>
                      <span>Exporting...</span>
                    </>
                  ) : (
                    <>
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                          d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
                        />
                      </svg>
                      <span>CSV Anomalies</span>
                    </>
                  )}
                </motion.button>
              </div>

              {/* Error Message */}
              <AnimatePresence>
                {error && (
                  <motion.p
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0 }}
                    className="text-clay-400 text-xs font-sans text-center"
                  >
                    {error}
                  </motion.p>
                )}
              </AnimatePresence>

              {/* Info */}
              <p className="text-oatmeal-500 text-xs font-sans text-center">
                Reference numbers (TB-M001, TB-I001) included for audit trail
              </p>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  )
}

export default ExportOptionsPanel
