'use client'

import { useState, useMemo } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { WorkbookInfo, SheetInfo } from '@/types/mapping'

interface WorkbookInspectorProps {
  isOpen: boolean
  onClose: () => void
  onConfirm: (selectedSheets: string[]) => void
  workbookInfo: WorkbookInfo
}

/**
 * WorkbookInspector - Day 11 Multi-Sheet Selection Modal
 *
 * Premium "Workbook Inspector" UI for selecting which Excel sheets to audit.
 * Follows Oat & Obsidian design system with Merriweather aesthetic.
 *
 * Features:
 * - Sheet list with checkboxes
 * - Row count and column preview
 * - Select All / Deselect All
 * - Subtle hover effects
 *
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */
export function WorkbookInspector({
  isOpen,
  onClose,
  onConfirm,
  workbookInfo,
}: WorkbookInspectorProps) {
  const [selectedSheets, setSelectedSheets] = useState<Set<string>>(() => {
    // Pre-select all sheets with data by default
    return new Set(workbookInfo.sheets.filter(s => s.has_data).map(s => s.name))
  })

  const sheetsWithData = useMemo(
    () => workbookInfo.sheets.filter(s => s.has_data),
    [workbookInfo.sheets]
  )

  const allSelected = selectedSheets.size === sheetsWithData.length
  const noneSelected = selectedSheets.size === 0

  const toggleSheet = (sheetName: string) => {
    setSelectedSheets(prev => {
      const next = new Set(prev)
      if (next.has(sheetName)) {
        next.delete(sheetName)
      } else {
        next.add(sheetName)
      }
      return next
    })
  }

  const toggleAll = () => {
    if (allSelected) {
      setSelectedSheets(new Set())
    } else {
      setSelectedSheets(new Set(sheetsWithData.map(s => s.name)))
    }
  }

  const handleConfirm = () => {
    onConfirm(Array.from(selectedSheets))
  }

  const totalSelectedRows = useMemo(() => {
    return workbookInfo.sheets
      .filter(s => selectedSheets.has(s.name))
      .reduce((sum, s) => sum + s.row_count, 0)
  }, [workbookInfo.sheets, selectedSheets])

  // Animation variants
  const overlayVariants = {
    hidden: { opacity: 0 },
    visible: { opacity: 1 },
  }

  const modalVariants = {
    hidden: { opacity: 0, scale: 0.95, y: 20 },
    visible: {
      opacity: 1,
      scale: 1,
      y: 0,
      transition: { type: 'spring' as const, damping: 25, stiffness: 300 },
    },
    exit: { opacity: 0, scale: 0.95, y: 20 },
  }

  const listItemVariants = {
    hidden: { opacity: 0, x: -10 },
    visible: (i: number) => ({
      opacity: 1,
      x: 0,
      transition: { delay: i * 0.03 },
    }),
  }

  if (!isOpen) return null

  return (
    <AnimatePresence>
      <motion.div
        className="fixed inset-0 z-50 flex items-center justify-center p-4"
        variants={overlayVariants}
        initial="hidden"
        animate="visible"
        exit="hidden"
      >
        {/* Backdrop */}
        <motion.div
          className="absolute inset-0 bg-obsidian-900/80 backdrop-blur-sm"
          onClick={onClose}
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
        />

        {/* Modal */}
        <motion.div
          className="relative w-full max-w-lg bg-surface-card border border-theme rounded-2xl shadow-2xl overflow-hidden"
          variants={modalVariants}
          initial="hidden"
          animate="visible"
          exit="exit"
        >
          {/* Header */}
          <div className="px-6 py-5 border-b border-theme">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-xl bg-sage-500/20 flex items-center justify-center">
                <svg
                  className="w-5 h-5 text-sage-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
                  />
                </svg>
              </div>
              <div>
                <h2 className="text-xl font-serif font-bold text-content-primary">
                  Workbook Inspector
                </h2>
                <p className="text-sm text-content-tertiary font-sans">
                  {workbookInfo.filename}
                </p>
              </div>
            </div>
          </div>

          {/* Sheet Summary */}
          <div className="px-6 py-3 bg-surface-card-secondary border-b border-theme">
            <div className="flex items-center justify-between text-sm font-sans">
              <span className="text-content-secondary">
                {workbookInfo.sheet_count} sheet{workbookInfo.sheet_count !== 1 ? 's' : ''} found
              </span>
              <span className="text-content-tertiary">
                {workbookInfo.total_rows.toLocaleString()} total rows
              </span>
            </div>
          </div>

          {/* Instructions */}
          <div className="px-6 py-3 border-b border-theme">
            <p className="text-sm text-content-secondary font-sans">
              Select the sheets to include in the consolidated audit. Multiple sheets will be aggregated using Summation Consolidation.
            </p>
          </div>

          {/* Select All Toggle */}
          <div className="px-6 py-3 border-b border-theme">
            <button
              onClick={toggleAll}
              className="flex items-center gap-2 text-sm font-sans text-sage-400 hover:text-sage-300 transition-colors"
            >
              <div
                className={`w-5 h-5 rounded border-2 flex items-center justify-center transition-all ${
                  allSelected
                    ? 'bg-sage-500 border-sage-500'
                    : 'border-oatmeal-500/50 hover:border-oatmeal-400'
                }`}
              >
                {allSelected && (
                  <svg className="w-3 h-3 text-obsidian-900" fill="currentColor" viewBox="0 0 20 20">
                    <path
                      fillRule="evenodd"
                      d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                      clipRule="evenodd"
                    />
                  </svg>
                )}
              </div>
              {allSelected ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          {/* Sheet List */}
          <div className="max-h-64 overflow-y-auto">
            <div className="px-6 py-2">
              {workbookInfo.sheets.map((sheet, index) => (
                <motion.div
                  key={sheet.name}
                  custom={index}
                  variants={listItemVariants}
                  initial="hidden"
                  animate="visible"
                  className={`
                    flex items-center gap-3 p-3 rounded-lg mb-2 cursor-pointer
                    transition-all duration-150
                    ${selectedSheets.has(sheet.name)
                      ? 'bg-sage-500/10 border border-sage-500/30'
                      : 'bg-surface-card-secondary border border-transparent hover:bg-surface-card hover:border-theme'
                    }
                    ${!sheet.has_data ? 'opacity-50 cursor-not-allowed' : ''}
                  `}
                  onClick={() => sheet.has_data && toggleSheet(sheet.name)}
                >
                  {/* Checkbox */}
                  <div
                    className={`w-5 h-5 rounded border-2 flex items-center justify-center flex-shrink-0 transition-all ${
                      selectedSheets.has(sheet.name)
                        ? 'bg-sage-500 border-sage-500'
                        : 'border-oatmeal-500/50'
                    }`}
                  >
                    {selectedSheets.has(sheet.name) && (
                      <svg className="w-3 h-3 text-obsidian-900" fill="currentColor" viewBox="0 0 20 20">
                        <path
                          fillRule="evenodd"
                          d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z"
                          clipRule="evenodd"
                        />
                      </svg>
                    )}
                  </div>

                  {/* Sheet Info */}
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-content-primary font-sans font-medium truncate">
                        {sheet.name}
                      </span>
                      {!sheet.has_data && (
                        <span className="text-xs bg-oatmeal-500/20 text-content-secondary px-2 py-0.5 rounded font-sans">
                          Empty
                        </span>
                      )}
                    </div>
                    <div className="flex items-center gap-3 mt-1 text-xs text-content-tertiary font-sans">
                      <span>{sheet.row_count.toLocaleString()} rows</span>
                      <span>{sheet.column_count} columns</span>
                    </div>
                    {sheet.columns.length > 0 && (
                      <div className="mt-1 text-xs text-content-tertiary font-mono truncate">
                        {sheet.columns.slice(0, 4).join(', ')}
                        {sheet.columns.length > 4 && ` +${sheet.columns.length - 4} more`}
                      </div>
                    )}
                  </div>
                </motion.div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div className="px-6 py-4 border-t border-theme bg-surface-card-secondary">
            <div className="flex items-center justify-between mb-3">
              <span className="text-sm text-content-secondary font-sans">
                {selectedSheets.size} sheet{selectedSheets.size !== 1 ? 's' : ''} selected
              </span>
              <span className="text-sm text-content-tertiary font-mono">
                {totalSelectedRows.toLocaleString()} rows to audit
              </span>
            </div>

            <div className="flex gap-3">
              <button
                onClick={onClose}
                className="flex-1 px-4 py-2.5 rounded-lg border border-theme text-content-primary font-sans font-medium hover:bg-surface-card-secondary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleConfirm}
                disabled={noneSelected}
                className={`flex-1 px-4 py-2.5 rounded-lg font-sans font-medium transition-all ${
                  noneSelected
                    ? 'bg-surface-card-secondary text-content-tertiary cursor-not-allowed'
                    : 'bg-sage-500 text-obsidian-900 hover:bg-sage-400'
                }`}
              >
                {selectedSheets.size > 1 ? 'Consolidate & Audit' : 'Audit Selected'}
              </button>
            </div>
          </div>
        </motion.div>
      </motion.div>
    </AnimatePresence>
  )
}

export default WorkbookInspector
