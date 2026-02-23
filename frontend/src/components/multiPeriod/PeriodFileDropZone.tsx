'use client'

import { useState, useCallback } from 'react'
import type { UploadStatus } from '@/types/shared'

export interface PeriodState {
  file: File | null
  status: UploadStatus
  result: Record<string, unknown> | null
  error: string | null
}

export function PeriodFileDropZone({ label, period, onFileSelect, disabled }: {
  label: string
  period: PeriodState
  onFileSelect: (file: File) => void
  disabled: boolean
}) {
  const [isDragging, setIsDragging] = useState(false)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    if (disabled) return
    const file = e.dataTransfer.files[0]
    if (file) onFileSelect(file)
  }, [disabled, onFileSelect])

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFileSelect(file)
  }, [onFileSelect])

  return (
    <div className="flex-1 min-w-0">
      <span className="block text-sm font-sans font-medium text-content-secondary mb-2">{label}</span>
      <div
        className={`relative border-2 border-dashed rounded-2xl p-6 text-center transition-all cursor-pointer ${
          disabled ? 'opacity-50 cursor-not-allowed border-theme' :
          isDragging ? 'border-sage-500 bg-sage-50' :
          period.file ? 'border-sage-500/30 bg-sage-50' :
          'bg-surface-card-secondary border-theme hover:border-oatmeal-300 hover:bg-surface-card-secondary'
        }`}
        onDragOver={(e) => { e.preventDefault(); if (!disabled) setIsDragging(true) }}
        onDragLeave={() => setIsDragging(false)}
        onDrop={handleDrop}
        role="button"
        tabIndex={0}
        onClick={() => {
          if (!disabled) {
            const input = document.createElement('input')
            input.type = 'file'
            input.accept = '.csv,.xlsx,.xls'
            input.onchange = (e) => handleFileInput(e as unknown as React.ChangeEvent<HTMLInputElement>)
            input.click()
          }
        }}
        onKeyDown={(e) => {
          if ((e.key === 'Enter' || e.key === ' ') && !disabled) {
            e.preventDefault()
            const input = document.createElement('input')
            input.type = 'file'
            input.accept = '.csv,.xlsx,.xls'
            input.onchange = (ev) => handleFileInput(ev as unknown as React.ChangeEvent<HTMLInputElement>)
            input.click()
          }
        }}
      >
        {period.status === 'loading' ? (
          <div className="flex flex-col items-center gap-2" aria-live="polite">
            <div className="w-8 h-8 border-2 border-sage-500/40 border-t-sage-600 rounded-full animate-spin" />
            <span className="text-sm font-sans text-content-secondary">Auditing...</span>
          </div>
        ) : period.status === 'success' ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 bg-sage-50 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-sage-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <span className="text-sm font-sans text-sage-600">{period.file?.name}</span>
            <span className="text-xs font-sans text-content-tertiary">Audit complete</span>
          </div>
        ) : period.status === 'error' ? (
          <div className="flex flex-col items-center gap-2">
            <div className="w-8 h-8 bg-clay-50 rounded-full flex items-center justify-center">
              <svg className="w-5 h-5 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <span className="text-sm font-sans text-clay-600">{period.error || 'Audit failed'}</span>
          </div>
        ) : period.file ? (
          <div className="flex flex-col items-center gap-2">
            <span className="text-sm font-sans text-content-primary">{period.file.name}</span>
            <span className="text-xs font-sans text-content-tertiary">Ready to audit</span>
          </div>
        ) : (
          <div className="flex flex-col items-center gap-2">
            <svg className="w-8 h-8 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <span className="text-sm font-sans text-content-secondary">Drop CSV or Excel file</span>
            <span className="text-xs font-sans text-content-tertiary">or click to browse</span>
          </div>
        )}
      </div>
    </div>
  )
}
