'use client'

/**
 * Currency Rate Panel — Sprint 258
 *
 * Collapsible panel for managing exchange rates before TB upload.
 * Supports CSV upload and manual single-rate entry.
 */

import { useState, useRef, useCallback } from 'react'
import { useCurrencyRates } from '@/hooks/useCurrencyRates'
import { ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

const COMMON_CURRENCIES = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'CHF', 'CNY']

export function CurrencyRatePanel() {
  const {
    rateStatus,
    uploadStatus,
    error,
    uploadRateTable,
    addSingleRate,
    clearRates,
    refreshStatus,
  } = useCurrencyRates()

  const [isOpen, setIsOpen] = useState(false)
  const [mode, setMode] = useState<'upload' | 'manual'>('upload')
  const [presentationCurrency, setPresentationCurrency] = useState('USD')
  const [dragActive, setDragActive] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  // Manual rate form state
  const [fromCurrency, setFromCurrency] = useState('')
  const [toCurrency, setToCurrency] = useState('USD')
  const [manualRate, setManualRate] = useState('')

  const handleFileUpload = useCallback(async (file: File) => {
    await uploadRateTable(file, presentationCurrency)
  }, [uploadRateTable, presentationCurrency])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileUpload(file)
  }, [handleFileUpload])

  const handleManualSubmit = useCallback(async (e: React.FormEvent) => {
    e.preventDefault()
    if (fromCurrency && toCurrency && manualRate) {
      const success = await addSingleRate(fromCurrency, toCurrency, manualRate, presentationCurrency)
      if (success) {
        setFromCurrency('')
        setManualRate('')
      }
    }
  }, [fromCurrency, toCurrency, manualRate, presentationCurrency, addSingleRate])

  return (
    <div className="border border-theme rounded-lg bg-surface-card overflow-hidden">
      {/* Header */}
      <button
        type="button"
        onClick={() => {
          setIsOpen(!isOpen)
          if (!isOpen) refreshStatus()
        }}
        className="w-full flex items-center justify-between px-4 py-3 text-left hover:bg-surface-page/50 transition-colors"
      >
        <div className="flex items-center gap-2">
          <svg className={`w-4 h-4 text-content-secondary transition-transform ${isOpen ? 'rotate-90' : ''}`} fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="font-serif text-sm font-semibold text-content-primary">
            Multi-Currency Conversion
          </span>
          {rateStatus?.has_rates && (
            <span className="px-2 py-0.5 text-xs rounded-full bg-sage-500/10 text-sage-600 font-mono">
              {rateStatus.rate_count} rate{rateStatus.rate_count !== 1 ? 's' : ''} loaded
            </span>
          )}
        </div>
        <span className="text-xs text-content-tertiary">
          {rateStatus?.has_rates ? rateStatus.presentation_currency : 'Optional'}
        </span>
      </button>

      {/* Collapsible Body */}
      {isOpen && (
        <div className="border-t border-theme px-4 py-4 space-y-4">
          {/* Presentation Currency Selector */}
          <div className="flex items-center gap-3">
            <label className="text-xs text-content-secondary whitespace-nowrap" htmlFor="pres-currency">
              Presentation Currency:
            </label>
            <select
              id="pres-currency"
              value={presentationCurrency}
              onChange={(e) => setPresentationCurrency(e.target.value)}
              className="px-2 py-1 text-sm rounded border border-theme bg-surface-card text-content-primary font-mono"
            >
              {COMMON_CURRENCIES.map(c => (
                <option key={c} value={c}>{c}</option>
              ))}
            </select>
          </div>

          {/* Mode Tabs */}
          <div className="flex gap-1 border-b border-theme">
            <button
              type="button"
              onClick={() => setMode('upload')}
              className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                mode === 'upload'
                  ? 'border-sage-500 text-sage-600'
                  : 'border-transparent text-content-tertiary hover:text-content-secondary'
              }`}
            >
              Upload CSV
            </button>
            <button
              type="button"
              onClick={() => setMode('manual')}
              className={`px-3 py-1.5 text-xs font-medium border-b-2 transition-colors ${
                mode === 'manual'
                  ? 'border-sage-500 text-sage-600'
                  : 'border-transparent text-content-tertiary hover:text-content-secondary'
              }`}
            >
              Manual Entry
            </button>
          </div>

          {/* Upload Mode */}
          {mode === 'upload' && (
            <div
              onDragOver={(e) => { e.preventDefault(); setDragActive(true) }}
              onDragLeave={() => setDragActive(false)}
              onDrop={handleDrop}
              onClick={() => fileInputRef.current?.click()}
              className={`border-2 border-dashed rounded-lg p-6 text-center cursor-pointer transition-colors ${
                dragActive
                  ? 'border-sage-500 bg-sage-500/5'
                  : 'border-theme hover:border-sage-500/50'
              }`}
              role="button"
              aria-label="Upload currency rates file. Drop CSV, TSV, TXT, or Excel file here or press Enter to browse."
              tabIndex={0}
              onKeyDown={(e) => { if (e.key === 'Enter') fileInputRef.current?.click() }}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept={ACCEPTED_FILE_EXTENSIONS_STRING}
                className="hidden"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFileUpload(file)
                }}
              />
              {uploadStatus === 'loading' ? (
                <p className="text-sm text-content-secondary">Uploading...</p>
              ) : (
                <>
                  <p className="text-sm text-content-secondary">
                    Drop a CSV, TSV, TXT, or Excel file with exchange rates
                  </p>
                  <p className="text-xs text-content-tertiary mt-1">
                    Columns: effective_date, from_currency, to_currency, rate
                  </p>
                </>
              )}
            </div>
          )}

          {/* Manual Entry Mode */}
          {mode === 'manual' && (
            <form onSubmit={handleManualSubmit} className="space-y-3">
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className="text-xs text-content-secondary block mb-1" htmlFor="from-curr">
                    From
                  </label>
                  <input
                    id="from-curr"
                    type="text"
                    value={fromCurrency}
                    onChange={(e) => setFromCurrency(e.target.value.toUpperCase().slice(0, 3))}
                    placeholder="EUR"
                    maxLength={3}
                    className="w-full px-2 py-1.5 text-sm rounded border border-theme bg-surface-card text-content-primary font-mono uppercase"
                  />
                </div>
                <div>
                  <label className="text-xs text-content-secondary block mb-1" htmlFor="to-curr">
                    To
                  </label>
                  <input
                    id="to-curr"
                    type="text"
                    value={toCurrency}
                    onChange={(e) => setToCurrency(e.target.value.toUpperCase().slice(0, 3))}
                    placeholder="USD"
                    maxLength={3}
                    className="w-full px-2 py-1.5 text-sm rounded border border-theme bg-surface-card text-content-primary font-mono uppercase"
                  />
                </div>
                <div>
                  <label className="text-xs text-content-secondary block mb-1" htmlFor="rate-val">
                    Rate
                  </label>
                  <input
                    id="rate-val"
                    type="text"
                    value={manualRate}
                    onChange={(e) => setManualRate(e.target.value)}
                    placeholder="1.0523"
                    className="w-full px-2 py-1.5 text-sm rounded border border-theme bg-surface-card text-content-primary font-mono"
                  />
                </div>
              </div>
              <button
                type="submit"
                disabled={!fromCurrency || !toCurrency || !manualRate}
                className="px-3 py-1.5 text-xs font-medium rounded bg-sage-600 text-white hover:bg-sage-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Add Rate
              </button>
            </form>
          )}

          {/* Error */}
          {error && (
            <div className="p-2 rounded bg-clay-500/10 text-clay-600 text-xs" role="alert">
              {error}
            </div>
          )}

          {/* Active Rates Summary */}
          {rateStatus?.has_rates && (
            <div className="flex items-center justify-between p-2 rounded bg-sage-500/5 border border-sage-500/20">
              <div className="text-xs text-content-secondary">
                <span className="font-mono font-medium text-sage-600">
                  {rateStatus.rate_count}
                </span>{' '}
                rate{rateStatus.rate_count !== 1 ? 's' : ''} active
                {rateStatus.currency_pairs.length > 0 && (
                  <span className="text-content-tertiary ml-1">
                    ({rateStatus.currency_pairs.join(', ')})
                  </span>
                )}
              </div>
              <button
                type="button"
                onClick={clearRates}
                className="text-xs text-clay-600 hover:text-clay-700 underline"
              >
                Clear
              </button>
            </div>
          )}

          {/* Help Text */}
          <p className="text-xs text-content-tertiary leading-relaxed">
            Upload exchange rates before your trial balance to enable automatic
            multi-currency conversion. Rates are session-scoped and never stored.
          </p>
        </div>
      )}
    </div>
  )
}
