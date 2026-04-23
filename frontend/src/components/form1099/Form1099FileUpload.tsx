'use client'

/**
 * Form 1099 dual-CSV upload surface — Sprint 689e.
 */

import { useCallback, useMemo, useState } from 'react'
import {
  Form1099CsvParseError,
  parsePaymentsCsv,
  parseVendorsCsv,
  readFileAsText,
} from '@/components/form1099/parseCsv'
import { FileDropZone } from '@/components/shared'
import type {
  Form1099Request,
  PaymentRequest,
  VendorRequest,
} from '@/types/form1099'

interface Form1099FileUploadProps {
  onAnalyze: (payload: Form1099Request) => void
  onExport: (payload: Form1099Request) => void
  loading: boolean
}

interface ParsedState {
  vendors: VendorRequest[]
  payments: PaymentRequest[]
}

export function Form1099FileUpload({ onAnalyze, onExport, loading }: Form1099FileUploadProps) {
  const [vendorsFile, setVendorsFile] = useState<File | null>(null)
  const [paymentsFile, setPaymentsFile] = useState<File | null>(null)
  const [taxYear, setTaxYear] = useState<string>(String(new Date().getUTCFullYear() - 1))
  const [parsed, setParsed] = useState<ParsedState>({ vendors: [], payments: [] })
  const [parseError, setParseError] = useState('')

  const handleVendors = useCallback(async (f: File) => {
    setVendorsFile(f)
    setParseError('')
    try {
      const vendors = parseVendorsCsv(await readFileAsText(f))
      setParsed(prev => ({ ...prev, vendors }))
    } catch (err) {
      setParsed(prev => ({ ...prev, vendors: [] }))
      setParseError(err instanceof Form1099CsvParseError ? err.message : 'Failed to parse vendors CSV.')
    }
  }, [])

  const handlePayments = useCallback(async (f: File) => {
    setPaymentsFile(f)
    setParseError('')
    try {
      const payments = parsePaymentsCsv(await readFileAsText(f))
      setParsed(prev => ({ ...prev, payments }))
    } catch (err) {
      setParsed(prev => ({ ...prev, payments: [] }))
      setParseError(err instanceof Form1099CsvParseError ? err.message : 'Failed to parse payments CSV.')
    }
  }, [])

  const payload = useMemo<Form1099Request | null>(() => {
    if (parsed.vendors.length === 0 || parsed.payments.length === 0) return null
    const year = Number.parseInt(taxYear, 10)
    if (!Number.isFinite(year) || year < 2000 || year > 2099) return null
    return {
      tax_year: year,
      vendors: parsed.vendors,
      payments: parsed.payments,
    }
  }, [parsed, taxYear])

  const canRun = payload !== null && !loading

  return (
    <div className="theme-card p-6">
      <h2 className="font-serif text-lg text-content-primary mb-2">Upload Vendors and Payments</h2>
      <p className="font-sans text-sm text-content-secondary mb-5">
        Export the vendor master file and the AP payment register from your ERP. The tool aggregates
        payments by vendor, applies IRS exemptions (corporation safe-harbor, processor-reported
        amounts), and flags vendors below the reporting threshold.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
        <div>
          <FileDropZone
            label="Vendors"
            hint="Drop vendors.csv or click"
            file={vendorsFile}
            onFileSelect={handleVendors}
            disabled={loading}
            accept=".csv,.tsv,.txt"
          />
          <p className="text-xs font-sans text-content-tertiary mt-2">
            Columns: vendor_id, vendor_name, tin, entity_type
            (individual / partnership / llc / corporation / s_corporation / government / tax_exempt / unknown),
            address_line_1, city, state, postal_code.
            {parsed.vendors.length > 0 && (
              <span className="text-sage-700 font-medium"> &middot; {parsed.vendors.length} vendors parsed.</span>
            )}
          </p>
        </div>
        <div>
          <FileDropZone
            label="Payments"
            hint="Drop payments.csv or click"
            file={paymentsFile}
            onFileSelect={handlePayments}
            disabled={loading}
            accept=".csv,.tsv,.txt"
          />
          <p className="text-xs font-sans text-content-tertiary mt-2">
            Columns: vendor_id, amount, payment_category
            (nonemployee_comp / rents / royalties / medical / legal / interest / other), payment_method
            (check / ach / wire / cash / credit_card / paypal), payment_date, invoice_number.
            {parsed.payments.length > 0 && (
              <span className="text-sage-700 font-medium"> &middot; {parsed.payments.length.toLocaleString()} payments parsed.</span>
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
        <button
          type="button"
          onClick={() => payload && onAnalyze(payload)}
          disabled={!canRun}
          className="px-5 py-2.5 rounded-lg bg-sage-600 text-oatmeal-50 font-sans font-medium hover:bg-sage-700 disabled:bg-obsidian-300 disabled:cursor-not-allowed transition-colors"
        >
          {loading ? 'Preparing…' : 'Prepare 1099 Candidates'}
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
