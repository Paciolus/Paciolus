'use client'

import { useState, useCallback, useEffect, useRef } from 'react'

// Hard fail if API URL is not configured
const API_URL = process.env.NEXT_PUBLIC_API_URL
if (!API_URL) {
  throw new Error(
    '\n\n' +
    '='.repeat(60) + '\n' +
    'CONFIGURATION ERROR - CloseSignify cannot start\n' +
    '='.repeat(60) + '\n\n' +
    'Required environment variable NEXT_PUBLIC_API_URL is not set.\n\n' +
    'Please create a .env.local file based on .env.example\n' +
    '='.repeat(60) + '\n'
  )
}

interface AbnormalBalance {
  account: string
  type: string
  issue: string
  amount: number
  debit: number
  credit: number
  materiality: 'material' | 'immaterial'
}

interface AuditResult {
  status: string
  balanced: boolean
  total_debits: number
  total_credits: number
  difference: number
  row_count: number
  message: string
  abnormal_balances: AbnormalBalance[]
  has_risk_alerts: boolean
  materiality_threshold: number
  material_count: number
  immaterial_count: number
}

export default function Home() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [message, setMessage] = useState('')

  // Audit zone state
  const [isDragging, setIsDragging] = useState(false)
  const [auditStatus, setAuditStatus] = useState<'idle' | 'loading' | 'success' | 'error'>('idle')
  const [auditResult, setAuditResult] = useState<AuditResult | null>(null)
  const [auditError, setAuditError] = useState('')

  // Store selected file for reactive recalculation
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [isRecalculating, setIsRecalculating] = useState(false)

  // Materiality threshold state (default $500 per MarketScout recommendation)
  const [materialityThreshold, setMaterialityThreshold] = useState(500)
  const [showImmaterial, setShowImmaterial] = useState(false)

  // Progress indicator state for streaming processing
  const [scanningRows, setScanningRows] = useState(0)
  const progressIntervalRef = useRef<NodeJS.Timeout | null>(null)

  // Ref for debounce timer
  const debounceTimerRef = useRef<NodeJS.Timeout | null>(null)

  // Start simulated progress indicator
  const startProgressIndicator = useCallback(() => {
    setScanningRows(0)
    let rows = 0
    const baseIncrement = 1000 // Start with larger increments

    progressIntervalRef.current = setInterval(() => {
      // Slow down as we "progress" to simulate realistic streaming
      const increment = Math.max(100, baseIncrement - Math.floor(rows / 5000) * 100)
      rows += increment + Math.floor(Math.random() * 500)
      setScanningRows(rows)
    }, 150)
  }, [])

  // Stop progress indicator
  const stopProgressIndicator = useCallback(() => {
    if (progressIntervalRef.current) {
      clearInterval(progressIntervalRef.current)
      progressIntervalRef.current = null
    }
  }, [])

  // Core audit function - can be called for initial upload or recalculation
  const runAudit = useCallback(async (file: File, threshold: number, isRecalc: boolean = false) => {
    if (isRecalc) {
      setIsRecalculating(true)
    } else {
      setAuditStatus('loading')
      setAuditResult(null)
      setAuditError('')
      setShowImmaterial(false)
      startProgressIndicator()
    }

    const formData = new FormData()
    formData.append('file', file)
    formData.append('materiality_threshold', threshold.toString())

    try {
      const response = await fetch(`${API_URL}/audit/trial-balance`, {
        method: 'POST',
        body: formData,
      })

      const data = await response.json()

      // Debug: Log the full API response
      console.log('Audit API Response:', data)
      console.log('Abnormal balances:', data.abnormal_balances)
      console.log('Has risk alerts:', data.has_risk_alerts)

      if (response.ok && data.status === 'success') {
        setAuditStatus('success')
        setAuditResult(data)
      } else {
        setAuditStatus('error')
        setAuditError(data.message || data.detail || 'Failed to analyze file')
      }
    } catch (error) {
      setAuditStatus('error')
      setAuditError('Unable to connect to server. Please try again.')
    } finally {
      setIsRecalculating(false)
      stopProgressIndicator()
    }
  }, [startProgressIndicator, stopProgressIndicator])

  // Handle initial file upload
  const handleFileUpload = useCallback(async (file: File) => {
    setSelectedFile(file)
    await runAudit(file, materialityThreshold, false)
  }, [materialityThreshold, runAudit])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)

    const file = e.dataTransfer.files[0]
    if (file) {
      handleFileUpload(file)
    }
  }, [handleFileUpload])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      handleFileUpload(file)
    }
  }, [handleFileUpload])

  // Debounced effect: Re-run audit when materiality threshold changes
  // Only triggers if a file is already loaded (selectedFile exists)
  useEffect(() => {
    // Skip if no file is loaded or if we're in initial loading state
    if (!selectedFile || auditStatus === 'loading') {
      return
    }

    // Clear any existing debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    // Set new debounce timer (300ms delay)
    debounceTimerRef.current = setTimeout(() => {
      runAudit(selectedFile, materialityThreshold, true)
    }, 300)

    // Cleanup on unmount or when dependencies change
    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [materialityThreshold, selectedFile, auditStatus, runAudit])

  // Cleanup progress interval on unmount
  useEffect(() => {
    return () => {
      if (progressIntervalRef.current) {
        clearInterval(progressIntervalRef.current)
      }
    }
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')

    try {
      const response = await fetch(`${API_URL}/waitlist`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email }),
      })

      const data = await response.json()

      if (response.ok) {
        setStatus('success')
        setMessage(data.message)
        setEmail('')
      } else {
        setStatus('error')
        setMessage(data.detail || 'Something went wrong. Please try again.')
      }
    } catch (error) {
      setStatus('error')
      setMessage('Unable to connect. Please try again later.')
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-900 via-slate-800 to-slate-900">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-slate-900/80 backdrop-blur-md border-b border-slate-700/50 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <div className="text-xl font-bold text-white tracking-tight">
            Close<span className="text-primary-400">Signify</span>
          </div>
          <div className="text-sm text-slate-400">
            For Fractional CFOs
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 bg-primary-500/10 border border-primary-500/20 rounded-full px-4 py-1.5 mb-8">
            <span className="w-2 h-2 bg-primary-400 rounded-full animate-pulse"></span>
            <span className="text-primary-300 text-sm font-medium">Now in Private Beta</span>
          </div>

          {/* Main Headline */}
          <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-6 leading-tight">
            Audit-Ready Trial Balances
            <span className="block text-primary-400">in Seconds</span>
          </h1>

          {/* Sub-headline */}
          <p className="text-xl md:text-2xl text-slate-300 mb-12 max-w-3xl mx-auto leading-relaxed">
            Fractional CFOs: Eliminate sign errors and misclassifications with automated
            <span className="text-white font-semibold"> Close Health Reports</span>.
          </p>

          {/* Waitlist Form */}
          <form onSubmit={handleSubmit} className="max-w-md mx-auto">
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your work email"
                required
                className="flex-1 px-5 py-4 bg-slate-800 border border-slate-600 rounded-xl text-white placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent transition-all"
              />
              <button
                type="submit"
                disabled={status === 'loading'}
                className="px-8 py-4 bg-primary-500 hover:bg-primary-400 disabled:bg-primary-600 disabled:cursor-not-allowed text-white font-semibold rounded-xl transition-all transform hover:scale-105 active:scale-95 shadow-lg shadow-primary-500/25"
              >
                {status === 'loading' ? 'Joining...' : 'Join Waitlist'}
              </button>
            </div>

            {/* Status Message */}
            {status === 'success' && (
              <p className="mt-4 text-green-400 font-medium">{message}</p>
            )}
            {status === 'error' && (
              <p className="mt-4 text-red-400 font-medium">{message}</p>
            )}
          </form>

          <p className="mt-6 text-slate-500 text-sm">
            Join 50+ Fractional CFOs already on the waitlist
          </p>
        </div>
      </section>

      {/* Secure Audit Zone */}
      <section className="py-16 px-6 bg-slate-800/30">
        <div className="max-w-3xl mx-auto">
          <div className="text-center mb-8">
            <div className="inline-flex items-center gap-2 bg-green-500/10 border border-green-500/20 rounded-full px-4 py-1.5 mb-4">
              <svg className="w-4 h-4 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span className="text-green-300 text-sm font-medium">Zero-Storage Processing</span>
            </div>
            <h2 className="text-3xl font-bold text-white mb-2">Secure Audit Zone</h2>
            <p className="text-slate-400">Upload your trial balance for instant validation. Your data never leaves your browser's memory.</p>
          </div>

          {/* Materiality Threshold Control */}
          <div className="bg-slate-800/50 border border-slate-700/50 rounded-xl p-6 mb-6">
            <div className="flex items-center gap-2 mb-4">
              <label htmlFor="materiality-threshold" className="text-white font-medium">
                Materiality Threshold
              </label>
              {/* Tooltip */}
              <div className="relative group">
                <button
                  type="button"
                  aria-label="What is materiality threshold?"
                  className="w-5 h-5 rounded-full bg-slate-600 text-slate-300 text-xs flex items-center justify-center hover:bg-slate-500 transition-colors"
                >
                  ?
                </button>
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-sm text-slate-300 w-64 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
                  <p className="font-medium text-white mb-1">What is Materiality?</p>
                  <p>Balances below this dollar amount are considered &quot;Indistinct&quot; and won&apos;t trigger high-priority alerts. This helps reduce alert fatigue on large trial balances.</p>
                  <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-slate-600"></div>
                </div>
              </div>
            </div>

            <div className="flex flex-col sm:flex-row items-center gap-4">
              {/* Numerical Input */}
              <div className="flex items-center gap-2">
                <span className="text-slate-400">$</span>
                <input
                  id="materiality-threshold"
                  type="number"
                  min="0"
                  step="100"
                  value={materialityThreshold}
                  onChange={(e) => setMaterialityThreshold(Math.max(0, Number(e.target.value)))}
                  aria-describedby="threshold-description"
                  className="w-28 px-3 py-2 bg-slate-900 border border-slate-600 rounded-lg text-white text-right font-mono focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              {/* Slider */}
              <div className="flex-1 w-full">
                <input
                  type="range"
                  min="0"
                  max="10000"
                  step="100"
                  value={materialityThreshold}
                  onChange={(e) => setMaterialityThreshold(Number(e.target.value))}
                  aria-label={`Materiality threshold slider, current value $${materialityThreshold}`}
                  className="w-full h-2 bg-slate-700 rounded-lg appearance-none cursor-pointer accent-primary-500"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>$0</span>
                  <span>$5,000</span>
                  <span>$10,000</span>
                </div>
              </div>
            </div>

            <p id="threshold-description" className="text-slate-500 text-sm mt-3">
              Current: Balances under <span className="text-white font-mono">${materialityThreshold.toLocaleString()}</span> will be marked as Indistinct
            </p>

            {/* Live update indicator when file is loaded */}
            {selectedFile && auditStatus === 'success' && (
              <div className="flex items-center gap-2 mt-3 text-xs">
                <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></div>
                <span className="text-green-400">
                  Live: Adjusting threshold will automatically recalculate
                </span>
                <span className="text-slate-500">
                  ({selectedFile.name})
                </span>
              </div>
            )}
          </div>

          {/* Drop Zone */}
          <div
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all cursor-pointer ${
              isDragging
                ? 'border-primary-400 bg-primary-500/10'
                : 'border-slate-600 hover:border-slate-500 bg-slate-800/50'
            }`}
          >
            <input
              type="file"
              accept=".csv,.xlsx,.xls"
              onChange={handleFileSelect}
              className="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
            />

            {auditStatus === 'idle' && (
              <>
                <svg className="w-12 h-12 text-slate-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
                <p className="text-slate-300 text-lg mb-2">Drag and drop your trial balance</p>
                <p className="text-slate-500 text-sm">or click to browse. Supports CSV and Excel files.</p>
              </>
            )}

            {auditStatus === 'loading' && (
              <div className="flex flex-col items-center">
                <div className="w-12 h-12 border-4 border-primary-500/30 border-t-primary-500 rounded-full animate-spin mb-4"></div>
                <p className="text-slate-300 mb-2">Streaming analysis in progress...</p>

                {/* Progress Indicator */}
                <div className="w-full max-w-xs">
                  {/* Progress bar background */}
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden mb-2">
                    {/* Animated progress bar (indeterminate style with pulse) */}
                    <div className="h-full bg-gradient-to-r from-primary-500 via-primary-400 to-primary-500 rounded-full animate-pulse"
                         style={{ width: '100%' }}></div>
                  </div>

                  {/* Scanning rows counter */}
                  <div className="flex items-center justify-center gap-2 text-sm">
                    <svg className="w-4 h-4 text-primary-400 animate-pulse" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    <span className="text-primary-300 font-mono">
                      Scanning rows: <span className="text-white">{scanningRows.toLocaleString()}</span>...
                    </span>
                  </div>
                </div>

                <p className="text-slate-500 text-xs mt-3">
                  Processing in memory-efficient chunks
                </p>
              </div>
            )}

            {auditStatus === 'success' && auditResult && (
              <div className={`space-y-4 ${isRecalculating ? 'opacity-70' : ''} transition-opacity`}>
                {/* Recalculating Indicator */}
                {isRecalculating && (
                  <div className="flex items-center justify-center gap-2 bg-primary-500/20 border border-primary-500/30 rounded-lg px-4 py-2 mb-2">
                    <div className="w-4 h-4 border-2 border-primary-400/30 border-t-primary-400 rounded-full animate-spin"></div>
                    <span className="text-primary-300 text-sm font-medium">Recalculating with new threshold...</span>
                  </div>
                )}

                {auditResult.balanced ? (
                  <>
                    <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                    </div>
                    <p className="text-green-400 text-xl font-semibold">Balanced</p>
                  </>
                ) : (
                  <>
                    <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto">
                      <svg className="w-10 h-10 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                    </div>
                    <p className="text-red-400 text-xl font-semibold">Out of Balance</p>
                  </>
                )}

                <div className="bg-slate-900/50 rounded-xl p-4 text-left max-w-sm mx-auto">
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <span className="text-slate-400">Total Debits:</span>
                    <span className="text-white text-right font-mono">${auditResult.total_debits.toLocaleString()}</span>
                    <span className="text-slate-400">Total Credits:</span>
                    <span className="text-white text-right font-mono">${auditResult.total_credits.toLocaleString()}</span>
                    <span className="text-slate-400">Difference:</span>
                    <span className={`text-right font-mono ${auditResult.difference === 0 ? 'text-green-400' : 'text-red-400'}`}>
                      ${auditResult.difference.toLocaleString()}
                    </span>
                    <span className="text-slate-400">Rows Analyzed:</span>
                    <span className="text-white text-right font-mono">{auditResult.row_count}</span>
                  </div>
                </div>

                {/* Risk Alerts Section - Material (High Priority) */}
                {auditResult.material_count > 0 && (
                  <div className="bg-yellow-500/10 border border-yellow-500/30 rounded-xl p-4 text-left max-w-md mx-auto mt-4">
                    <div className="flex items-center gap-2 mb-3">
                      <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                      </svg>
                      <span className="text-yellow-400 font-semibold">
                        Material Risk Alerts ({auditResult.material_count})
                      </span>
                    </div>
                    <p className="text-yellow-200/70 text-xs mb-3">
                      High-priority: Balances ≥ ${auditResult.materiality_threshold.toLocaleString()} with unusual directions
                    </p>
                    <div className="space-y-2">
                      {auditResult.abnormal_balances
                        .filter(item => item.materiality === 'material')
                        .map((item, index) => (
                          <div key={index} className="bg-slate-900/50 rounded-lg p-3">
                            <div className="flex justify-between items-start">
                              <div className="flex items-start gap-2">
                                <svg className="w-4 h-4 text-yellow-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20" aria-hidden="true">
                                  <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                                </svg>
                                <div>
                                  <p className="text-white font-medium text-sm">{item.account}</p>
                                  <p className="text-yellow-300/70 text-xs">{item.type} Account</p>
                                </div>
                              </div>
                              <span className="text-yellow-400 font-mono text-sm">${item.amount.toLocaleString()}</span>
                            </div>
                            <p className="text-slate-400 text-xs mt-1 ml-6">{item.issue}</p>
                          </div>
                        ))}
                    </div>
                  </div>
                )}

                {/* Immaterial (Indistinct) Alerts - Collapsed by default */}
                {auditResult.immaterial_count > 0 && (
                  <div className="bg-slate-700/30 border border-slate-600/50 rounded-xl p-4 text-left max-w-md mx-auto mt-4">
                    <button
                      onClick={() => setShowImmaterial(!showImmaterial)}
                      className="flex items-center justify-between w-full text-left"
                      aria-expanded={showImmaterial}
                      aria-controls="immaterial-alerts"
                    >
                      <div className="flex items-center gap-2">
                        <svg className="w-5 h-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                        </svg>
                        <span className="text-slate-400 font-medium">
                          Indistinct Items ({auditResult.immaterial_count})
                        </span>
                      </div>
                      <svg
                        className={`w-5 h-5 text-slate-400 transition-transform ${showImmaterial ? 'rotate-180' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        viewBox="0 0 24 24"
                        aria-hidden="true"
                      >
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                      </svg>
                    </button>
                    <p className="text-slate-500 text-xs mt-2">
                      Below materiality threshold (${auditResult.materiality_threshold.toLocaleString()})
                    </p>

                    {showImmaterial && (
                      <div id="immaterial-alerts" className="space-y-2 mt-3">
                        {auditResult.abnormal_balances
                          .filter(item => item.materiality === 'immaterial')
                          .map((item, index) => (
                            <div key={index} className="bg-slate-800/50 rounded-lg p-3 opacity-70">
                              <div className="flex justify-between items-start">
                                <div className="flex items-start gap-2">
                                  <svg className="w-4 h-4 text-slate-500 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
                                  </svg>
                                  <div>
                                    <p className="text-slate-300 font-medium text-sm">{item.account}</p>
                                    <p className="text-slate-500 text-xs">{item.type} Account</p>
                                  </div>
                                </div>
                                <span className="text-slate-400 font-mono text-sm">${item.amount.toLocaleString()}</span>
                              </div>
                              <p className="text-slate-500 text-xs mt-1 ml-6">{item.issue}</p>
                            </div>
                          ))}
                      </div>
                    )}
                  </div>
                )}

                <button
                  onClick={() => {
                    setAuditStatus('idle')
                    setAuditResult(null)
                    setSelectedFile(null)
                  }}
                  className="text-primary-400 hover:text-primary-300 text-sm font-medium mt-2"
                  disabled={isRecalculating}
                >
                  Upload another file
                </button>
              </div>
            )}

            {auditStatus === 'error' && (
              <div className="space-y-4">
                <div className="w-16 h-16 bg-red-500/20 rounded-full flex items-center justify-center mx-auto">
                  <svg className="w-10 h-10 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </div>
                <p className="text-red-400 font-medium">{auditError}</p>
                <button
                  onClick={() => {
                    setAuditStatus('idle')
                    setAuditError('')
                    setSelectedFile(null)
                  }}
                  className="text-primary-400 hover:text-primary-300 text-sm font-medium"
                >
                  Try again
                </button>
              </div>
            )}
          </div>

          <p className="text-center text-slate-500 text-xs mt-4">
            Your file is processed entirely in-memory and is never saved to any disk or server.
          </p>
        </div>
      </section>

      {/* Features Section */}
      <section className="py-20 px-6 border-t border-slate-700/50">
        <div className="max-w-6xl mx-auto">
          <h2 className="text-3xl font-bold text-white text-center mb-16">
            Why CFOs Choose CloseSignify
          </h2>

          <div className="grid md:grid-cols-3 gap-8">
            {/* Feature 1 */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8 hover:border-primary-500/50 transition-all">
              <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Instant Validation</h3>
              <p className="text-slate-400 leading-relaxed">
                Upload your trial balance and get immediate feedback on sign errors, balance mismatches, and classification issues.
              </p>
            </div>

            {/* Feature 2 */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8 hover:border-primary-500/50 transition-all">
              <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Zero Data Storage</h3>
              <p className="text-slate-400 leading-relaxed">
                Your client data never touches our servers. All processing happens in-memory and is cleared immediately after.
              </p>
            </div>

            {/* Feature 3 */}
            <div className="bg-slate-800/50 border border-slate-700/50 rounded-2xl p-8 hover:border-primary-500/50 transition-all">
              <div className="w-12 h-12 bg-primary-500/20 rounded-xl flex items-center justify-center mb-6">
                <svg className="w-6 h-6 text-primary-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-white mb-3">Close Health Reports</h3>
              <p className="text-slate-400 leading-relaxed">
                Generate professional PDF reports highlighting issues and recommendations, ready to share with your clients.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center bg-gradient-to-r from-primary-500/10 to-primary-600/10 border border-primary-500/20 rounded-3xl p-12">
          <h2 className="text-3xl font-bold text-white mb-4">
            Ready to streamline your close process?
          </h2>
          <p className="text-slate-300 mb-8">
            Join the waitlist and be the first to know when we launch.
          </p>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
            className="inline-block px-8 py-4 bg-primary-500 hover:bg-primary-400 text-white font-semibold rounded-xl transition-all transform hover:scale-105"
          >
            Get Early Access
          </a>
        </div>
      </section>

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-slate-700/50">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-slate-500 text-sm">
            2024 CloseSignify. Built for Fractional CFOs.
          </div>
          <div className="text-slate-500 text-sm">
            Zero-Storage Architecture. Your data stays yours.
          </div>
        </div>
      </footer>
    </main>
  )
}
