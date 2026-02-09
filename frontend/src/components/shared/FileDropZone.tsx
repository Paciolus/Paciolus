'use client'

import { useState, useCallback } from 'react'

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
  <svg className="w-8 h-8 text-oatmeal-500 mx-auto" fill="none" stroke="currentColor" viewBox="0 0 24 24">
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
  accept = '.csv,.xlsx,.xls',
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

  return (
    <div className={`flex-1 min-w-0 ${className}`}>
      <label className="block text-sm font-sans font-medium text-oatmeal-300 mb-2">{label}</label>
      <div
        className={`relative border-2 border-dashed rounded-xl p-6 text-center transition-all cursor-pointer min-h-[140px] flex flex-col items-center justify-center ${
          disabled ? 'opacity-50 cursor-not-allowed border-obsidian-600/30' :
          isDragging ? 'border-sage-500/60 bg-sage-500/5' :
          file ? 'border-sage-500/30 bg-sage-500/5' :
          'border-obsidian-500/40 hover:border-oatmeal-400/40 hover:bg-obsidian-700/30'
        }`}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        {file ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 bg-sage-500/20 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span className="text-sm font-sans text-sage-400 truncate max-w-full px-2">{file.name}</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            {icon || DEFAULT_ICON}
            <span className="text-sm font-sans text-oatmeal-400">{hint}</span>
            <span className="text-xs font-sans text-oatmeal-600">CSV or Excel (.xlsx)</span>
          </div>
        )}
      </div>
    </div>
  )
}
