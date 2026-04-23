'use client'

/**
 * W-2 / W-3 Reconciliation triple-CSV upload — Sprint 689d.
 *
 * Three optional file drops (payroll.csv is required; w2_drafts.csv
 * and form_941.csv are optional). Each is parsed client-side before
 * the analyze button posts JSON to /audit/w2-reconciliation.
 */

import { useCallback, useMemo, useState } from 'react'
import { FileDropZone } from '@/components/shared'
import {
  W2CsvParseError,
  parseForm941Csv,
  parsePayrollCsv,
  parseW2DraftsCsv,
  readFileAsText,
} from '@/components/w2Reconciliation/parseCsv'
import type {
  Form941QuarterRequest,
  W2DraftRequest,
  W2EmployeePayrollRequest,
  W2ReconciliationRequest,
} from '@/types/w2Reconciliation'

interface W2FileUploadProps {
  onAnalyze: (payload: W2ReconciliationRequest) => void
  onExport: (payload: W2ReconciliationRequest) => void
  loading: boolean
}

interface ParsedState {
  employees: W2EmployeePayrollRequest[]
  w2_drafts: W2DraftRequest[]
  form_941_quarters: Form941QuarterRequest[]
}

export function W2FileUpload({ onAnalyze, onExport, loading }: W2FileUploadProps) {
  const [payrollFile, setPayrollFile] = useState<File | null>(null)
  const [draftsFile, setDraftsFile] = useState<File | null>(null)
  const [form941File, setForm941File] = useState<File | null>(null)
  const [taxYear, setTaxYear] = useState<string>(String(new Date().getUTCFullYear() - 1))
  const [tolerance, setTolerance] = useState('1.00')
  const [parsed, setParsed] = useState<ParsedState>({ employees: [], w2_drafts: [], form_941_quarters: [] })
  const [parseError, setParseError] = useState('')

  const handlePayrollFile = useCallback(async (f: File) => {
    setPayrollFile(f)
    setParseError('')
    try {
      const employees = parsePayrollCsv(await readFileAsText(f))
      setParsed(prev => ({ ...prev, employees }))
    } catch (err) {
      setParsed(prev => ({ ...prev, employees: [] }))
      setParseError(err instanceof W2CsvParseError ? err.message : 'Failed to parse payroll CSV.')
    }
  }, [])

  const handleDraftsFile = useCallback(async (f: File) => {
    setDraftsFile(f)
    setParseError('')
    try {
      const w2_drafts = parseW2DraftsCsv(await readFileAsText(f))
      setParsed(prev => ({ ...prev, w2_drafts }))
    } catch (err) {
      setParsed(prev => ({ ...prev, w2_drafts: [] }))
      setParseError(err instanceof W2CsvParseError ? err.message : 'Failed to parse W-2 draft CSV.')
    }
  }, [])

  const handleForm941File = useCallback(async (f: File) => {
    setForm941File(f)
    setParseError('')
    try {
      const form_941_quarters = parseForm941Csv(await readFileAsText(f))
      setParsed(prev => ({ ...prev, form_941_quarters }))
    } catch (err) {
      setParsed(prev => ({ ...prev, form_941_quarters: [] }))
      setParseError(err instanceof W2CsvParseError ? err.message : 'Failed to parse Form 941 CSV.')
    }
  }, [])

  const payload = useMemo<W2ReconciliationRequest | null>(() => {
    if (parsed.employees.length === 0) return null
    const year = Number.parseInt(taxYear, 10)
    if (!Number.isFinite(year) || year < 2000 || year > 2099) return null
    return {
      tax_year: year,
      employees: parsed.employees,
      w2_drafts: parsed.w2_drafts,
      form_941_quarters: parsed.form_941_quarters,
      tolerance,
    }
  }, [parsed, taxYear, tolerance])

  const canRun = payload !== null && !loading

  return (
    <div className="theme-card p-6">
      <h2 className="font-serif text-lg text-content-primary mb-2">Upload Reconciliation Inputs</h2>
      <p className="font-sans text-sm text-content-secondary mb-5">
        Payroll YTD is required; W-2 draft and Form 941 quarterly CSVs are optional but enable
        richer discrepancy checks. Files are parsed client-side and discarded after analysis.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
        <div>
          <FileDropZone
            label="Payroll YTD (required)"
            hint="Drop payroll.csv or click"
            file={payrollFile}
            onFileSelect={handlePayrollFile}
            disabled={loading}
            accept=".csv,.tsv,.txt"
          />
          <p className="text-xs font-sans text-content-tertiary mt-2">
            Columns: employee_id, employee_name, federal_wages, federal_withholding, ss_wages,
            ss_tax_withheld, medicare_wages, medicare_tax_withheld, plus optional HSA / 401(k) / SIMPLE IRA.
            {parsed.employees.length > 0 && (
              <span className="text-sage-700 font-medium"> &middot; {parsed.employees.length} employees.</span>
            )}
          </p>
        </div>
        <div>
          <FileDropZone
            label="W-2 drafts (optional)"
            hint="Drop w2_drafts.csv"
            file={draftsFile}
            onFileSelect={handleDraftsFile}
            disabled={loading}
            accept=".csv,.tsv,.txt"
          />
          <p className="text-xs font-sans text-content-tertiary mt-2">
            Columns: employee_id, box_1_federal_wages … box_6_medicare_tax_withheld, box_12_code_w_hsa,
            box_12_code_d_401k, box_12_code_s_simple.
            {parsed.w2_drafts.length > 0 && (
              <span className="text-sage-700 font-medium"> &middot; {parsed.w2_drafts.length} drafts.</span>
            )}
          </p>
        </div>
        <div>
          <FileDropZone
            label="Form 941 quarterly (optional)"
            hint="Drop form_941.csv"
            file={form941File}
            onFileSelect={handleForm941File}
            disabled={loading}
            accept=".csv,.tsv,.txt"
          />
          <p className="text-xs font-sans text-content-tertiary mt-2">
            Columns: quarter, total_federal_wages, total_federal_withholding, total_ss_wages,
            total_medicare_wages (max 4 rows).
            {parsed.form_941_quarters.length > 0 && (
              <span className="text-sage-700 font-medium"> &middot; {parsed.form_941_quarters.length} quarter(s).</span>
            )}
          </p>
        </div>
      </div>

      {parseError && (
        <div className="mb-4 p-3 rounded-lg border border-clay-200 bg-clay-50 text-clay-700 text-sm font-sans">
          {parseError}
        </div>
      )}

      <div className="flex flex-wrap items-center gap-3">
        <label className="flex items-center gap-2 text-xs font-sans text-content-secondary">
          <span>Tax year</span>
          <input
            type="text"
            value={taxYear}
            onChange={e => setTaxYear(e.target.value)}
            disabled={loading}
            className="w-20 px-2 py-1 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500"
            aria-label="Tax year"
          />
        </label>
        <label className="flex items-center gap-2 text-xs font-sans text-content-secondary">
          <span>Tolerance</span>
          <input
            type="text"
            value={tolerance}
            onChange={e => setTolerance(e.target.value)}
            disabled={loading}
            className="w-24 px-2 py-1 rounded border border-theme bg-surface-card font-mono text-xs text-content-primary focus:outline-hidden focus:ring-2 focus:ring-sage-500"
            aria-label="Reconciliation tolerance"
          />
        </label>
        <button
          type="button"
          onClick={() => payload && onAnalyze(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg bg-sage-600 text-oatmeal-50 font-sans font-medium hover:bg-sage-700 disabled:bg-obsidian-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Reconciling…' : 'Run Reconciliation'}
        </button>
        <button
          type="button"
          onClick={() => payload && onExport(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg border border-theme bg-surface-card text-content-primary font-sans font-medium hover:bg-oatmeal-100 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Download CSV
        </button>
      </div>
    </div>
  )
}
