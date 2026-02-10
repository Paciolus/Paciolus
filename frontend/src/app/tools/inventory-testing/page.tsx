'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import Link from 'next/link'
import { useAuth } from '@/context/AuthContext'
import { VerificationBanner } from '@/components/auth'
import { ToolNav } from '@/components/shared'
import { InventoryScoreCard, InventoryTestResultGrid, InventoryDataQualityBadge, FlaggedInventoryTable } from '@/components/inventoryTesting'
import { useInventoryTesting } from '@/hooks/useInventoryTesting'
import { useFileUpload } from '@/hooks/useFileUpload'
import { useTestingExport } from '@/hooks/useTestingExport'

/**
 * Inventory Testing — Tool 11 (Sprint 119)
 *
 * IAS 2 / ISA 501 / ISA 540: Inventory existence, completeness, and valuation.
 * Upload an inventory register for automated testing — 9-test battery
 * for inventory anomaly indicators across structural, statistical, and advanced tiers.
 */
export default function InventoryTestingPage() {
  const { user, isAuthenticated, isLoading: authLoading } = useAuth()
  const { status, result, error, runTests, reset } = useInventoryTesting()
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const { exporting, handleExportMemo, handleExportCSV } = useTestingExport(
    '/export/inventory-memo', '/export/csv/inventory',
    'InventoryTesting_Memo.pdf', 'InventoryTesting_Flagged.csv',
  )

  const exportBody = {
    composite_score: result?.composite_score,
    test_results: result?.test_results,
    data_quality: result?.data_quality,
    column_detection: result?.column_detection,
    filename: selectedFile?.name?.replace(/\.[^.]+$/, '') || 'inventory_testing',
  }

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

  const { isDragging, fileInputRef, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } = useFileUpload(handleFileUpload)

  const handleNewTest = useCallback(() => {
    reset()
    setSelectedFile(null)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [reset, fileInputRef])

  const isVerified = user?.is_verified !== false

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      <ToolNav currentTool="inventory-testing" />

      <div className="pt-24 pb-16 px-6 max-w-5xl mx-auto">
        {/* Verification Banner */}
        {isAuthenticated && user && !isVerified && (
          <VerificationBanner />
        )}

        {/* Hero Header */}
        <div className="text-center mb-10">
          <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-500/10 border border-sage-500/20 mb-6">
            <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
            <span className="text-sage-300 text-sm font-sans font-medium">IAS 2 / ISA 501 Inventory Analysis</span>
          </div>
          <h1 className="font-serif text-4xl text-oatmeal-100 mb-3">
            Inventory Testing
          </h1>
          <p className="font-sans text-oatmeal-400 text-lg max-w-2xl mx-auto">
            Upload an inventory register for automated testing &mdash; 9-test battery
            for inventory anomaly indicators per IAS 2 and ISA 501.
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
              Inventory Testing requires a verified account. Sign in or create a free account to analyze your inventory register.
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

        {/* Upload Zone */}
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
                onChange={handleFileSelect}
                className="hidden"
              />
              <div className="w-16 h-16 mx-auto mb-4 rounded-full bg-obsidian-700/50 flex items-center justify-center">
                <svg className="w-8 h-8 text-oatmeal-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
                </svg>
              </div>
              <h3 className="font-serif text-lg text-oatmeal-200 mb-2">
                Upload Inventory Register
              </h3>
              <p className="font-sans text-sm text-oatmeal-500 mb-1">
                Drop your inventory register here or click to browse
              </p>
              <p className="font-sans text-xs text-oatmeal-600">
                CSV or Excel (.xlsx) &mdash; up to 50MB
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
                  Running 9-test inventory battery on {selectedFile?.name}...
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
                  onClick={() => handleExportMemo(exportBody)}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-sage-500/15 border border-sage-500/30 rounded-lg text-sage-300 font-sans text-sm hover:bg-sage-500/25 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {exporting === 'pdf' ? 'Generating...' : 'Download Testing Memo'}
                </button>
                <button
                  onClick={() => handleExportCSV(exportBody)}
                  disabled={exporting !== null || !result}
                  className="px-4 py-2 bg-obsidian-700 border border-obsidian-500/40 rounded-lg text-oatmeal-300 font-sans text-sm hover:bg-obsidian-600 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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

            {/* Score Card */}
            <InventoryScoreCard score={result.composite_score} />

            {/* Data Quality */}
            <InventoryDataQualityBadge quality={result.data_quality} />

            {/* Test Results Grid */}
            <div>
              <h2 className="font-serif text-lg text-oatmeal-200 mb-4">Test Results</h2>
              <InventoryTestResultGrid results={result.test_results} />
            </div>

            {/* Flagged Inventory Table */}
            <div>
              <h2 className="font-serif text-lg text-oatmeal-200 mb-4">Flagged Inventory Items</h2>
              <FlaggedInventoryTable results={result.test_results} />
            </div>

            {/* Disclaimer */}
            <div className="bg-obsidian-800/30 border border-obsidian-600/20 rounded-xl p-4 mt-8">
              <p className="font-sans text-xs text-oatmeal-600 leading-relaxed">
                <span className="text-oatmeal-500 font-medium">Disclaimer:</span> This automated inventory testing
                tool provides analytical procedures to assist professional auditors in evaluating inventory register
                anomaly indicators per IAS 2 (Inventories), ISA 501 (Audit Evidence &mdash; Specific Considerations),
                and ISA 540 (Auditing Accounting Estimates).
                Results are not NRV adequacy conclusions or obsolescence determinations and should be interpreted
                in the context of the specific engagement. They are not a substitute for professional judgment or
                sufficient audit evidence per ISA 500.
              </p>
            </div>
          </motion.div>
        )}

        {/* Info cards for idle state */}
        {status === 'idle' && isAuthenticated && isVerified && (
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">IN-01 to IN-03</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Structural Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Missing fields, negative values, extended value mismatch
              </p>
            </div>
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">IN-04 to IN-07</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Statistical Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Unit cost outliers, quantity outliers, slow-moving inventory, category concentration
              </p>
            </div>
            <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
              <div className="text-2xl mb-3">IN-08 to IN-09</div>
              <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Advanced Tests</h3>
              <p className="font-sans text-oatmeal-500 text-xs">
                Duplicate items, zero-value items
              </p>
            </div>
          </div>
        )}
      </div>
    </main>
  )
}
