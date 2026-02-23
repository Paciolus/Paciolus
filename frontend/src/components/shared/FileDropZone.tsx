'use client'

import { useState, useCallback, type KeyboardEvent } from 'react'
import { ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

/**
 * Shared file drag-and-drop upload zone.
 *
 * Sprint 111: Extracted from bank-rec, three-way-match, and ar-aging inline implementations.
 * Supports optional custom icon, disabled state, and file-selected feedback.
 */

interface FileDropZoneProps {
  /** Heading label above the drop zone. */
  label: string
  /** Prompt text shown when no file is selected. */
  hint: string
  /** Current file (null = no file selected). */
  file: File | null
  /** Called when a file is selected via drop or click. */
  onFileSelect: (file: File) => void
  /** Disables interaction. */
  disabled?: boolean
  /** Optional custom icon JSX. Defaults to cloud-upload SVG. */
  icon?: React.ReactNode
  /** Accepted file types. Defaults to '.csv,.xlsx,.xls'. */
  accept?: string
  /** Additional CSS classes on the outer wrapper. */
  className?: string
}

const DEFAULT_ICON = (
  <svg className="w-8 h-8 text-content-tertiary mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
  </svg>
)

export function FileDropZone({
  label,
  hint,
  file,
  onFileSelect,
  disabled = false,
  icon,
  accept = ACCEPTED_FILE_EXTENSIONS_STRING,
  className = '',
}: FileDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const f = e.dataTransfer.files[0]
    if (f) onFileSelect(f)
  }, [disabled, onFileSelect])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f) onFileSelect(f)
  }, [onFileSelect])

  const handleClick = useCallback(() => {
    if (disabled) return
    const input = document.createElement('input')
    input.type = 'file'
    input.accept = accept
    input.onchange = (e) => handleFileInput(e as unknown as React.ChangeEvent<HTMLInputElement>)
    input.click()
  }, [disabled, accept, handleFileInput])

  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault()
      handleClick()
    }
  }, [handleClick])

  return (
    <div className={`flex-1 min-w-0 ${className}`}>
      <span className="block text-sm font-sans font-medium text-content-primary mb-2">{label}</span>
      <div
        role="button"
        tabIndex={disabled ? -1 : 0}
        aria-label={`${label} file upload`}
        aria-disabled={disabled || undefined}
        className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer min-h-[140px] flex flex-col items-center justify-center focus:outline-none focus:ring-2 focus:ring-sage-500 focus:ring-offset-2 ${
          disabled ? 'opacity-50 cursor-not-allowed border-theme' :
          isDragging ? 'border-theme-success-border bg-theme-success-bg' :
          file ? 'border-theme-success-border bg-theme-success-bg' :
          'border-theme hover:border-theme-hover bg-surface-card-secondary hover:bg-surface-card'
        }`}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={handleClick}
        onKeyDown={handleKeyDown}
      >
        {file ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 bg-theme-success-bg rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-theme-success-text" fill="none" stroke="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span className="text-sm font-sans text-theme-success-text truncate max-w-full px-2">{file.name}</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            {icon || DEFAULT_ICON}
            <span className="text-sm font-sans text-content-secondary">{hint}</span>
            <span className="text-xs font-sans text-content-tertiary">CSV, TSV, TXT, or Excel (.xlsx)</span>
          </div>
        )}
      </div>
    </div>
  )
}
