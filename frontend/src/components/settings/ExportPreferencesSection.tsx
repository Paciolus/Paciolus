'use client'

/**
 * ExportPreferencesSection — Display preferences + export format + FYE
 * Sprint 519 Phase 4: Extracted from practice settings page.
 */

import { Reveal } from '@/components/ui/Reveal'

interface ExportPreferencesSectionProps {
  showImmaterial: boolean
  autoSaveSummaries: boolean
  defaultExportFormat: string
  defaultFYE: string
  getInputClasses: (field: string, isValid?: boolean) => string
  onShowImmaterialChange: (value: boolean) => void
  onAutoSaveSummariesChange: (value: boolean) => void
  onExportFormatChange: (value: string) => void
  onFYEChange: (value: string) => void
}

export function ExportPreferencesSection({
  showImmaterial,
  autoSaveSummaries,
  defaultExportFormat,
  defaultFYE,
  getInputClasses,
  onShowImmaterialChange,
  onAutoSaveSummariesChange,
  onExportFormatChange,
  onFYEChange,
}: ExportPreferencesSectionProps) {
  return (
    <>
      {/* Display Preferences */}
      <Reveal delay={0.12} className="theme-card p-6 mb-6">
        <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
          Display Preferences
        </h2>

        <div className="space-y-4">
          <label htmlFor="show-immaterial" className="flex items-center gap-3 cursor-pointer">
            <input
              id="show-immaterial"
              type="checkbox"
              checked={showImmaterial}
              onChange={(e) => onShowImmaterialChange(e.target.checked)}
              className="w-5 h-5 rounded-sm border-theme bg-surface-input text-sage-500 focus:ring-sage-500/20"
            />
            <div>
              <span className="text-content-primary font-sans font-medium">Show immaterial items by default</span>
              <p className="text-content-tertiary text-xs">Display all anomalies, including those below materiality threshold</p>
            </div>
          </label>

          <label htmlFor="auto-save-summaries" className="flex items-center gap-3 cursor-pointer">
            <input
              id="auto-save-summaries"
              type="checkbox"
              checked={autoSaveSummaries}
              onChange={(e) => onAutoSaveSummariesChange(e.target.checked)}
              className="w-5 h-5 rounded-sm border-theme bg-surface-input text-sage-500 focus:ring-sage-500/20"
            />
            <div>
              <span className="text-content-primary font-sans font-medium">Auto-save diagnostic summaries</span>
              <p className="text-content-tertiary text-xs">Automatically store aggregate totals for trend analysis (Zero-Storage compliant)</p>
            </div>
          </label>
        </div>
      </Reveal>

      {/* Export Settings */}
      <Reveal delay={0.16} className="theme-card p-6 mb-6">
        <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
          Export Settings
        </h2>

        <div className="mb-4">
          <label htmlFor="export-format" className="block text-content-secondary font-sans font-medium mb-2">
            Default Export Format
          </label>
          <select
            id="export-format"
            value={defaultExportFormat}
            onChange={(e) => onExportFormatChange(e.target.value)}
            className={getInputClasses('exportFormat')}
          >
            <option value="pdf" className="bg-surface-input">PDF Report</option>
            <option value="excel" className="bg-surface-input">Excel Workpaper</option>
          </select>
        </div>

        <div>
          <label htmlFor="fiscal-year-end" className="block text-content-secondary font-sans font-medium mb-2">
            Default Fiscal Year End
          </label>
          <input
            id="fiscal-year-end"
            type="text"
            value={defaultFYE}
            onChange={(e) => onFYEChange(e.target.value)}
            placeholder="MM-DD"
            className={getInputClasses('fye')}
          />
          <p className="text-content-tertiary text-xs mt-1">Format: MM-DD (e.g., 12-31 for December 31)</p>
        </div>
      </Reveal>
    </>
  )
}
