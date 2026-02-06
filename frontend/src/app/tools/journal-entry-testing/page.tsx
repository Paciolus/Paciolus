'use client'

import { useState, useCallback, useRef } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { ProfileDropdown, VerificationBanner } from '@/components/auth'
import { JEScoreCard, TestResultGrid, GLDataQualityBadge, BenfordChart, FlaggedEntryTable } from '@/components/jeTesting'
import { useJETesting } from '@/hooks/useJETesting'

const API_URL = process.env.NEXT_PUBLIC_API_URL

/**
 * Journal Entry Testing — Full Tool (Sprint 66)
 *
 * Standalone tool for automated journal entry analysis.
 * Upload → Process → Results with Benford's Law visualization.
 */
export default function JournalEntryTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading, logout, token } = useAuth()
  const { status, result, error, runTests, reset } = useJETesting()
  const [isDragging, setIsDragging] = useState(false)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [exporting, setExporting] = useState<'pdf' | 'csv' | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileUpload = useCallback(async (file: File) => {
    const validTypes = [
      'text/csv',
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      'application/vnd.ms-excel',
    ]
    const ext = file.name.toLowerCase().split('.').pop()
    if (!validTypes.includes(file.type) && !['csv', 'xlsx', 'xls'].includes(ext || '')) {
      return
    }
    setSelectedFile(file)
    await runTests(file)
  }, [runTests])

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFileUpload(file)
  }, [handleFileUpload])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback(() => setIsDragging(false), [])

  const handleNewTest = useCallback(() => {
    reset()
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [reset])

  const handleExportMemo = useCallback(async () => {
    if (!result || !token) return
    setExporting('pdf')
    try {
      const body = {
        composite_score: result.composite_score,
        test_results: result.test_results,
        data_quality: result.data_quality,
        column_detection: result.column_detection ?? null,
        multi_currency_warning: result.multi_currency_warning ?? null,
        benford_result: result.benford_result ?? null,
        filename: selectedFile?.name || 'je_testing',
        client_name: null,
        period_tested: null,
        prepared_by: null,
        reviewed_by: null,
        workpaper_date: null,
      }
      const res = await fetch(`${API_URL}/export/je-testing-memo`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `JE_Testing_Memo_${new Date().toISOString().slice(0, 10)}.pdf`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // Silent fail — user can retry
    } finally {
      setExporting(null)
    }
  }, [result, token, selectedFile])

  const handleExportCSV = useCallback(async () => {
    if (!result || !token) return
    setExporting('csv')
    try {
      const body = {
        composite_score: result.composite_score,
        test_results: result.test_results,
        data_quality: result.data_quality,
        column_detection: result.column_detection ?? null,
        multi_currency_warning: result.multi_currency_warning ?? null,
        benford_result: result.benford_result ?? null,
        filename: selectedFile?.name || 'je_testing',
      }
      const res = await fetch(`${API_URL}/export/csv/je-testing`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`,
        },
        body: JSON.stringify(body),
      })
      if (!res.ok) throw new Error('Export failed')
      const blob = await res.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `JE_Flagged_Entries_${new Date().toISOString().slice(0, 10)}.csv`
      a.click()
      URL.revokeObjectURL(url)
    } catch {
      // Silent fail — user can retry
    } finally {
      setExporting(null)
    }
  }, [result, token, selectedFile])

  const isVerified = user?.is_verified !== false

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-obsidian-900/90 backdrop-blur-lg border-b border-obsidian-600/30 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3 group">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
            />
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/tools/trial-balance"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              TB Diagnostics
            </Link>
            <Link
              href="/tools/multi-period"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Multi-Period
            </Link>
            <span className="text-sm font-sans text-sage-400 border-b border-sage-400/50">
              JE Testing
            </span>
            <div className="ml-4 pl-4 border-l border-obsidian-600/30">
              {authLoading ? null : isAuthenticated && user ? (
                <ProfileDropdown user={user} onLogout={logout} />
              ) : (
                <Link
                  href="/login"
                  className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      <div className="pt-24 pb-16 px-6 max-w-5xl mx-auto">
        {/* Verification Banner */}
        {isAuthenticated && user && !isVerified && (
          <VerificationBanner />
        )}

        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-500/10 border border-sage-500/20 mb-6">
            <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
            <span className="text-sage-300 text-sm font-sans font-medium">Automated Analysis</span>
          </div>
          <h1 className="font-serif text-4xl text-oatmeal-100 mb-3">
            Journal Entry Testing
          </h1>
          <p className="font-sans text-oatmeal-400 text-lg max-w-2xl mx-auto">
            Upload a General Ledger extract for automated testing — Benford&apos;s Law,
            structural validation, and statistical anomaly detection.
          </p>
        </div>

        {/* Guest CTA */}
        {!authLoading && !isAuthenticated && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-2xl p-8 text-center mb-10"
          >
            <h2 className="font-serif text-xl text-oatmeal-200 mb-2">Sign in to get started</h2>
            <p className="font-sans text-oatmeal-500 text-sm mb-6 max-w-md mx-auto">
              Journal Entry Testing requires a verified account. Sign in or create a free account to analyze your GL data.
            </p>
            <div className="flex items-center justify-center gap-4">
              <Link
                href="/login"
                className="px-6 py-3 bg-sage-500/20 border border-sage-500/40 rounded-lg text-sage-300 font-sans text-sm hover:bg-sage-500/30 transition-colors"
              >
                Sign In
              </Link>
              <Link
                href="/register"
                className="px-6 py-3 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors"
              >
                Create Account
              </Link>
            </div>
          </motion.div>
        )}

        {/* Upload Zone — Only for authenticated verified users */}
        {isAuthenticated && isVerified && status === 'idle' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
          >
            <div
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              className={`relative border-2 border-dashed rounded-2xl p-12 text-center transition-all duration-200 cursor-pointer
                ${isDragging
                  ? 'border-sage-400 bg-sage-500/5'
                  : 'border-obsidian-600/50 bg-obsidian-800/30 hover:border-obsidian-500 hover:bg-obsidian-800/50'
                }`}
              onClick={() => fileInputRef.current?.click()}
            >
              <input
                ref={fileInputRef}
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={(e) => {
                  const file = e.target.files?.[0]
                  if (file) handleFileUpload(file)
                }}
                className="hidden"
              />
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-obsidian-700/50 flex items-center justify-center">
                <svg className="w-8 h-8 text-oatmeal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="font-serif text-lg text-oatmeal-200 mb-2">
                Upload General Ledger Extract
              </h3>
              <p className="font-sans text-sm text-oatmeal-500 mb-1">
                Drop your GL file here or click to browse
              </p>
              <p className="font-sans text-xs text-oatmeal-600">
                CSV or Excel (.xlsx) — up to 50MB
              </p>
            </div>

            {/* Zero-Storage notice */}
            <div className="flex items-center justify-center gap-2 mt-4">
              <svg className="w-4 h-4 text-sage-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <span className="font-sans text-xs text-oatmeal-600">
                Zero-Storage: Your data is processed in-memory and never saved.
              </span>
            </div>
          </motion.div>
        )}

        {/* Loading State */}
        <AnimatePresence>
          {status === 'loading' && (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="text-center py-16"
            >
              <div className="inline-flex items-center gap-3 px-6 py-4 bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl">
                <div className="w-5 h-5 border-2 border-sage-500/30 border-t-sage-400 rounded-full animate-spin" />
                <span className="font-sans text-oatmeal-300">
                  Running 8-test battery on {selectedFile?.name}...
                </span>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Error State */}
        {status === 'error' && (
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-obsidian-800/50 border border-l-4 border-clay-500/30 border-l-clay-500 rounded-xl p-6 mb-6"
          >
            <h3 className="font-serif text-sm text-clay-400 mb-1">Analysis Failed</h3>
            <p className="font-sans text-sm text-oatmeal-400">{error}</p>
            <button
              onClick={handleNewTest}
              className="mt-3 px-4 py-2 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors"
            >
              Try Again
            </button>
          </motion.div>
        )}

        {/* Results */}
        {status === 'success' && result && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            className="space-y-6"
          >
            {/* Action bar */}
            <div className="flex items-center justify-between flex-wrap gap-3">
              <div>
                <p className="font-sans text-sm text-oatmeal-500">
                  Results for <span className="text-oatmeal-300">{selectedFile?.name}</span>
                </p>
              </div>
              <div className="flex items-center gap-3">
                <button
                  onClick={handleExportMemo}
                  disabled={exporting === 'pdf'}
                  className="px-4 py-2 bg-sage-500/15 border border-sage-500/30 rounded-lg text-sage-300 font-sans text-sm hover:bg-sage-500/25 transition-colors disabled:opacity-50"
                >
                  {exporting === 'pdf' ? 'Generating...' : 'Download Testing Memo'}
                </button>
                <button
                  onClick={handleExportCSV}
                  disabled={exporting === 'csv'}
                  className="px-4 py-2 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors disabled:opacity-50"
                >
                  {exporting === 'csv' ? 'Exporting...' : 'Export Flagged CSV'}
                </button>
                <button
                  onClick={handleNewTest}
                  className="px-4 py-2 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors"
                >
                  New Test
                </button>
              </div>
            </div>

            {/* Multi-currency warning */}
            {result.multi_currency_warning && (
              <div className="bg-obsidian-800/50 border border-l-4 border-oatmeal-500/30 border-l-oatmeal-400 rounded-xl p-4">
                <p className="font-sans text-sm text-oatmeal-300">
                  {result.multi_currency_warning.warning_message}
                </p>
              </div>
            )}

            {/* Score Card */}
            <JEScoreCard score={result.composite_score} />

            {/* Data Quality + Benford side by side */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <GLDataQualityBadge quality={result.data_quality} />
              {result.benford_result && (
                <BenfordChart benford={result.benford_result} />
              )}
            </div>

            {/* Test Results Grid */}
            <div>
              <h2 className="font-serif text-lg text-oatmeal-200 mb-4">Test Results</h2>
              <TestResultGrid results={result.test_results} />
            </div>

            {/* Flagged Entry Table */}
            <div>
              <h2 className="font-serif text-lg text-oatmeal-200 mb-4">Flagged Entries</h2>
              <FlaggedEntryTable results={result.test_results} />
            </div>

            {/* Disclaimer */}
            <div className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl p-4 mt-8">
              <p className="font-sans text-xs text-oatmeal-600 leading-relaxed">
                <span className="text-oatmeal-500 font-medium">Disclaimer:</span> This automated journal entry testing
                tool provides analytical procedures to assist professional auditors. Results should be interpreted in
                the context of the specific engagement and are not a substitute for professional judgment. Statistical
                tests use standard thresholds that may require adjustment for specific industries or entity sizes.
              </p>
            </div>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">T1-T5</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Unbalanced entries, missing fields, duplicates, round amounts, unusual amounts
              </p>
            </div>
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">T6-T8</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Benford&apos;s Law analysis, weekend postings, month-end clustering
              </p>
            </div>
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">T9+</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Advanced Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Coming soon — user analysis, backdating, reciprocal entries, threshold splitting
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
