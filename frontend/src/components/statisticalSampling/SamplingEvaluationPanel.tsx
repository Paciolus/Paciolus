'use client'

import { useState, useCallback } from 'react'
import { ZeroStorageNotice } from '@/components/shared'
import { useFileUpload } from '@/hooks/useFileUpload'
import type { UploadStatus } from '@/types/shared'
import type { SamplingEvaluationConfig, SamplingDesignResult } from '@/types/statisticalSampling'
import { isAcceptedFileType, ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats'

interface SamplingEvaluationPanelProps {
  status: UploadStatus
  error: string
  designResult: SamplingDesignResult | null
  onRun: (file: File, config: SamplingEvaluationConfig) => Promise<void>
  isVerified: boolean
}

export function SamplingEvaluationPanel({ status, error, designResult, onRun, isVerified }: SamplingEvaluationPanelProps) {
  // Pre-fill from design result when available
  const [config, setConfig] = useState<SamplingEvaluationConfig>({
    method: designResult?.method ?? 'mus',
    confidence_level: designResult?.confidence_level ?? 0.95,
    tolerable_misstatement: designResult?.tolerable_misstatement ?? 0,
    expected_misstatement: designResult?.expected_misstatement ?? 0,
    population_value: designResult?.population_value ?? 0,
    sample_size: designResult?.actual_sample_size ?? 0,
    sampling_interval: designResult?.sampling_interval ?? null,
  })
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [validationError, setValidationError] = useState('')

  const handleFileUpload = useCallback(async (file: File) => {
    if (!isAcceptedFileType(file)) return
    setSelectedFile(file)
    setValidationError('')
  }, [])

  const { isDragging, fileInputRef, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } = useFileUpload(handleFileUpload)

  const handleSubmit = useCallback(async () => {
    if (!selectedFile) {
      setValidationError('Please select the completed sample file.')
      return
    }
    if (config.population_value <= 0) {
      setValidationError('Population value must be positive.')
      return
    }
    if (config.sample_size <= 0) {
      setValidationError('Sample size must be positive.')
      return
    }
    if (config.tolerable_misstatement <= 0) {
      setValidationError('Tolerable misstatement must be positive.')
      return
    }
    setValidationError('')
    await onRun(selectedFile, config)
  }, [selectedFile, config, onRun])

  const isLoading = status === 'loading'

  return (
    <div className="space-y-6">
      {/* Pre-fill notice */}
      {designResult && (
        <div className="bg-sage-500/10 border border-sage-500/30 rounded-xl p-4">
          <p className="font-sans text-sm text-sage-600">
            Parameters pre-filled from your design phase. Upload the completed sample with audited amounts.
          </p>
        </div>
      )}

      {/* Configuration */}
      <div className="theme-card rounded-2xl p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Evaluation Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label htmlFor="eval-population-value" className="block font-sans text-sm text-content-secondary mb-1">Population Value ($)</label>
            <input
              id="eval-population-value"
              type="number"
              min={0}
              step={1000}
              value={config.population_value || ''}
              onChange={e => setConfig(c => ({ ...c, population_value: parseFloat(e.target.value) || 0 }))}
              placeholder="Total population value"
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500/50"
            />
          </div>
          <div>
            <label htmlFor="eval-sample-size" className="block font-sans text-sm text-content-secondary mb-1">Sample Size</label>
            <input
              id="eval-sample-size"
              type="number"
              min={1}
              step={1}
              value={config.sample_size || ''}
              onChange={e => setConfig(c => ({ ...c, sample_size: parseInt(e.target.value) || 0 }))}
              placeholder="Number of items tested"
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500/50"
            />
          </div>
          <div>
            <label htmlFor="eval-tolerable-misstatement" className="block font-sans text-sm text-content-secondary mb-1">Tolerable Misstatement ($)</label>
            <input
              id="eval-tolerable-misstatement"
              type="number"
              min={0}
              step={100}
              value={config.tolerable_misstatement || ''}
              onChange={e => setConfig(c => ({ ...c, tolerable_misstatement: parseFloat(e.target.value) || 0 }))}
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500/50"
            />
          </div>
          <div>
            <label htmlFor="eval-confidence-level" className="block font-sans text-sm text-content-secondary mb-1">Confidence Level</label>
            <input
              id="eval-confidence-level"
              type="number"
              min={0.5}
              max={0.99}
              step={0.05}
              value={config.confidence_level}
              onChange={e => setConfig(c => ({ ...c, confidence_level: parseFloat(e.target.value) || 0.95 }))}
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500/50"
            />
          </div>
        </div>
      </div>

      {/* File Upload */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => isVerified && fileInputRef.current?.click()}
        onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); if (isVerified) fileInputRef.current?.click() } }}
        role="button"
        tabIndex={0}
        className={`theme-card rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging ? 'ring-2 ring-sage-500/50 bg-sage-500/5' : 'hover:border-sage-500/30'
        } ${!isVerified ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={ACCEPTED_FILE_EXTENSIONS_STRING}
          onChange={handleFileSelect}
          className="hidden"
        />
        {selectedFile ? (
          <div>
            <p className="font-sans text-content-primary text-sm">
              Selected: <span className="font-mono text-sage-500">{selectedFile.name}</span>
            </p>
            <p className="font-sans text-content-tertiary text-xs mt-1">Click or drag to replace</p>
          </div>
        ) : (
          <div>
            <svg className="w-10 h-10 mx-auto mb-3 text-content-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            <p className="font-sans text-content-secondary text-sm">
              Drop your completed sample file here
            </p>
            <p className="font-sans text-content-tertiary text-xs mt-1">
              Must include Recorded Amount and Audited Amount columns
            </p>
          </div>
        )}
        <ZeroStorageNotice className="mt-4" />
      </div>

      {/* Errors */}
      {(validationError || error) && (
        <div className="bg-clay-500/10 border border-clay-500/30 rounded-xl p-4" role="alert">
          <p className="font-sans text-sm text-clay-500">{validationError || error}</p>
        </div>
      )}

      {/* Run Button */}
      <button
        onClick={handleSubmit}
        disabled={isLoading || !isVerified || !selectedFile}
        className="w-full btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
      >
        <span aria-live="polite">
          {isLoading ? (
            <span className="flex items-center justify-center gap-2">
              <svg className="animate-spin w-4 h-4" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              Evaluating Sample...
            </span>
          ) : (
            'Evaluate Sample'
          )}
        </span>
      </button>
    </div>
  )
}
