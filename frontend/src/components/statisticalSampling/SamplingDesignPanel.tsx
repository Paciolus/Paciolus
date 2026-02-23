'use client'

import { useState, useCallback, useRef } from 'react'
import { motion } from 'framer-motion'
import { ZeroStorageNotice } from '@/components/shared'
import { useFileUpload } from '@/hooks/useFileUpload'
import type { UploadStatus } from '@/types/shared'
import type { SamplingDesignConfig, SamplingMethod } from '@/types/statisticalSampling'
import { CONFIDENCE_LEVELS, SAMPLING_METHOD_LABELS } from '@/types/statisticalSampling'

interface SamplingDesignPanelProps {
  status: UploadStatus
  error: string
  onRun: (file: File, config: SamplingDesignConfig) => Promise<void>
  isVerified: boolean
}

const DEFAULT_CONFIG: SamplingDesignConfig = {
  method: 'mus',
  confidence_level: 0.95,
  tolerable_misstatement: 0,
  expected_misstatement: 0,
  stratification_threshold: null,
  sample_size_override: null,
}

export function SamplingDesignPanel({ status, error, onRun, isVerified }: SamplingDesignPanelProps) {
  const [config, setConfig] = useState<SamplingDesignConfig>(DEFAULT_CONFIG)
  const [selectedFile, setSelectedFile] = useState<File | null>(null)
  const [validationError, setValidationError] = useState('')

  const handleFileUpload = useCallback(async (file: File) => {
    const ext = file.name.toLowerCase().split('.').pop()
    if (!['csv', 'xlsx', 'xls'].includes(ext || '')) return
    setSelectedFile(file)
    setValidationError('')
  }, [])

  const { isDragging, fileInputRef, handleDrop, handleDragOver, handleDragLeave, handleFileSelect } = useFileUpload(handleFileUpload)

  const handleSubmit = useCallback(async () => {
    if (!selectedFile) {
      setValidationError('Please select a population file first.')
      return
    }
    if (config.tolerable_misstatement <= 0) {
      setValidationError('Tolerable misstatement must be greater than zero.')
      return
    }
    if (config.expected_misstatement >= config.tolerable_misstatement) {
      setValidationError('Expected misstatement must be less than tolerable misstatement.')
      return
    }
    setValidationError('')
    await onRun(selectedFile, config)
  }, [selectedFile, config, onRun])

  const isLoading = status === 'loading'

  return (
    <div className="space-y-6">
      {/* Configuration */}
      <div className="theme-card rounded-2xl p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Sampling Parameters</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Method */}
          <div>
            <label htmlFor="sampling-method" className="block font-sans text-sm text-content-secondary mb-1">Sampling Method</label>
            <select
              id="sampling-method"
              value={config.method}
              onChange={e => setConfig(c => ({ ...c, method: e.target.value as SamplingMethod }))}
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-sans text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/50"
            >
              {Object.entries(SAMPLING_METHOD_LABELS).map(([key, label]) => (
                <option key={key} value={key}>{label}</option>
              ))}
            </select>
          </div>

          {/* Confidence Level */}
          <div>
            <label htmlFor="confidence-level" className="block font-sans text-sm text-content-secondary mb-1">Confidence Level</label>
            <select
              id="confidence-level"
              value={config.confidence_level}
              onChange={e => setConfig(c => ({ ...c, confidence_level: parseFloat(e.target.value) }))}
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-sans text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/50"
            >
              {CONFIDENCE_LEVELS.map(cl => (
                <option key={cl.value} value={cl.value}>{cl.label}</option>
              ))}
            </select>
          </div>

          {/* Tolerable Misstatement */}
          <div>
            <label htmlFor="tolerable-misstatement" className="block font-sans text-sm text-content-secondary mb-1">Tolerable Misstatement ($)</label>
            <input
              id="tolerable-misstatement"
              type="number"
              min={0}
              step={100}
              value={config.tolerable_misstatement || ''}
              onChange={e => setConfig(c => ({ ...c, tolerable_misstatement: parseFloat(e.target.value) || 0 }))}
              placeholder="e.g., 50000"
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/50"
            />
          </div>

          {/* Expected Misstatement */}
          <div>
            <label htmlFor="expected-misstatement" className="block font-sans text-sm text-content-secondary mb-1">Expected Misstatement ($)</label>
            <input
              id="expected-misstatement"
              type="number"
              min={0}
              step={100}
              value={config.expected_misstatement || ''}
              onChange={e => setConfig(c => ({ ...c, expected_misstatement: parseFloat(e.target.value) || 0 }))}
              placeholder="0 (optional)"
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/50"
            />
          </div>

          {/* Stratification Threshold */}
          <div>
            <label htmlFor="stratification-threshold" className="block font-sans text-sm text-content-secondary mb-1">Stratification Threshold ($)</label>
            <input
              id="stratification-threshold"
              type="number"
              min={0}
              step={1000}
              value={config.stratification_threshold ?? ''}
              onChange={e => {
                const val = e.target.value ? parseFloat(e.target.value) : null
                setConfig(c => ({ ...c, stratification_threshold: val }))
              }}
              placeholder="Optional — items above tested 100%"
              className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/50"
            />
          </div>

          {/* Sample Size Override (random only) */}
          {config.method === 'random' && (
            <div>
              <label htmlFor="sample-size-override" className="block font-sans text-sm text-content-secondary mb-1">Sample Size Override</label>
              <input
                id="sample-size-override"
                type="number"
                min={1}
                step={1}
                value={config.sample_size_override ?? ''}
                onChange={e => {
                  const val = e.target.value ? parseInt(e.target.value) : null
                  setConfig(c => ({ ...c, sample_size_override: val }))
                }}
                placeholder="Auto-calculated if blank"
                className="w-full px-3 py-2 rounded-lg bg-surface-card border border-theme text-content-primary font-mono text-sm focus:outline-none focus:ring-2 focus:ring-sage-500/50"
              />
            </div>
          )}
        </div>
      </div>

      {/* File Upload */}
      <div
        onDrop={handleDrop}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onClick={() => isVerified && fileInputRef.current?.click()}
        className={`theme-card rounded-2xl p-8 text-center cursor-pointer transition-all duration-200 ${
          isDragging ? 'ring-2 ring-sage-500/50 bg-sage-500/5' : 'hover:border-sage-500/30'
        } ${!isVerified ? 'opacity-50 cursor-not-allowed' : ''}`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".csv,.xlsx,.xls"
          onChange={handleFileSelect}
          className="hidden"
        />
        {selectedFile ? (
          <div>
            <p className="font-sans text-content-primary text-sm">
              Selected: <span className="font-mono text-sage-500">{selectedFile.name}</span>
            </p>
            <p className="font-sans text-content-tertiary text-xs mt-1">
              Click or drag to replace
            </p>
          </div>
        ) : (
          <div>
            <svg className="w-10 h-10 mx-auto mb-3 text-content-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
            </svg>
            <p className="font-sans text-content-secondary text-sm">
              Drop your population file here or click to browse
            </p>
            <p className="font-sans text-content-tertiary text-xs mt-1">
              CSV or Excel with ID, Description, and Amount columns
            </p>
          </div>
        )}
        <ZeroStorageNotice className="mt-4" />
      </div>

      {/* Validation/Error Messages */}
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
              Designing Sample...
            </span>
          ) : (
            'Design Sample'
          )}
        </span>
      </button>
    </div>
  )
}
