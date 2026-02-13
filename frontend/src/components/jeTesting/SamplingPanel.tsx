'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type {
  SamplingCriterion,
  SamplingPreview,
  SamplingResult,
} from '@/types/jeTesting'
import { SAMPLING_CRITERIA_LABELS } from '@/types/jeTesting'
import { API_URL } from '@/utils/constants'
import { getCsrfToken } from '@/utils/apiClient'

type SamplingStep = 'configure' | 'preview' | 'results'

interface SamplingPanelProps {
  file: File | null
  token: string | null
}

export function SamplingPanel({ file, token }: SamplingPanelProps) {
  const [step, setStep] = useState<SamplingStep>('configure')
  const [criteria, setCriteria] = useState<SamplingCriterion[]>(['account', 'amount_range'])
  const [sampleRate, setSampleRate] = useState(0.10)
  const [fixedPerStratum, setFixedPerStratum] = useState<number | null>(null)
  const [useFixed, setUseFixed] = useState(false)
  const [preview, setPreview] = useState<SamplingPreview | null>(null)
  const [result, setResult] = useState<SamplingResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const toggleCriterion = useCallback((c: SamplingCriterion) => {
    setCriteria(prev =>
      prev.includes(c) ? prev.filter(x => x !== c) : [...prev, c]
    )
  }, [])

  const handlePreview = useCallback(async () => {
    if (!file || !token || criteria.length === 0) return
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('stratify_by', JSON.stringify(criteria))

      const csrfToken = getCsrfToken()
      const res = await fetch(`${API_URL}/audit/journal-entries/sample/preview`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        },
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Preview failed')
      }
      const data = await res.json()
      setPreview(data as SamplingPreview)
      setStep('preview')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Preview failed')
    } finally {
      setLoading(false)
    }
  }, [file, token, criteria])

  const handleSample = useCallback(async () => {
    if (!file || !token) return
    setLoading(true)
    setError('')
    try {
      const formData = new FormData()
      formData.append('file', file)
      formData.append('stratify_by', JSON.stringify(criteria))
      formData.append('sample_rate', String(sampleRate))
      if (useFixed && fixedPerStratum !== null) {
        formData.append('fixed_per_stratum', String(fixedPerStratum))
      }

      const csrfToken2 = getCsrfToken()
      const res = await fetch(`${API_URL}/audit/journal-entries/sample`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          ...(csrfToken2 ? { 'X-CSRF-Token': csrfToken2 } : {}),
        },
        body: formData,
      })
      if (!res.ok) {
        const err = await res.json().catch(() => ({}))
        throw new Error(err.detail || 'Sampling failed')
      }
      const data = await res.json()
      setResult(data as SamplingResult)
      setStep('results')
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Sampling failed')
    } finally {
      setLoading(false)
    }
  }, [file, token, criteria, sampleRate, useFixed, fixedPerStratum])

  const handleReset = useCallback(() => {
    setStep('configure')
    setPreview(null)
    setResult(null)
    setError('')
  }, [])

  if (!file) return null

  const allCriteria: SamplingCriterion[] = ['account', 'amount_range', 'period', 'user']

  return (
 <div className="theme-card rounded-2xl overflow-hidden">
      {/* Header */}
      <div className="p-5 border-b border-theme-divider">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-sage-50 flex items-center justify-center">
              <svg className="w-4 h-4 text-sage-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3 4h13M3 8h9m-9 4h6m4 0l4-4m0 0l4 4m-4-4v12" />
              </svg>
            </div>
            <div>
              <h3 className="font-serif text-sm text-content-primary">Stratified Sampling</h3>
              <p className="font-sans text-xs text-content-tertiary">PCAOB AS 2315 / ISA 530 compliant</p>
            </div>
          </div>
          {/* Step indicator */}
          <div className="flex items-center gap-2">
            {(['configure', 'preview', 'results'] as const).map((s, i) => (
              <div
                key={s}
                className={`flex items-center gap-1.5 ${
                  step === s ? 'text-sage-600' : 'text-content-tertiary'
                }`}
              >
                <div className={`w-6 h-6 rounded-full flex items-center justify-center text-xs font-mono ${
                  step === s
                    ? 'bg-sage-50 border border-sage-300'
                    : s === 'results' && result ? 'bg-sage-50 border border-sage-200' :
                      s === 'preview' && (preview || step === 'results') ? 'bg-sage-50 border border-sage-200' :
                      'bg-surface-card-secondary border border-theme'
                }`}>
                  {i + 1}
                </div>
                {i < 2 && <div className="w-4 h-px bg-oatmeal-300" />}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="p-5">
        <AnimatePresence mode="wait">
          {/* Step 1: Configure */}
          {step === 'configure' && (
            <motion.div
              key="configure"
              initial={{ opacity: 0, x: -12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -12 }}
              className="space-y-4"
            >
              {/* Criteria selection */}
              <div>
                <label className="font-serif text-xs text-content-primary mb-2 block">Stratify by</label>
                <div className="flex flex-wrap gap-2">
                  {allCriteria.map(c => (
                    <button
                      key={c}
                      onClick={() => toggleCriterion(c)}
                      className={`px-3 py-1.5 rounded-lg font-sans text-xs transition-colors ${
                        criteria.includes(c)
                          ? 'bg-sage-50 border border-sage-300 text-sage-700'
                          : 'bg-surface-card-secondary border border-theme text-content-tertiary hover:border-theme-hover'
                      }`}
                    >
                      {SAMPLING_CRITERIA_LABELS[c]}
                    </button>
                  ))}
                </div>
              </div>

              {/* Sample rate */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="font-serif text-xs text-content-primary mb-2 block">
                    <input
                      type="radio"
                      checked={!useFixed}
                      onChange={() => setUseFixed(false)}
                      className="mr-2"
                    />
                    Sample Rate
                  </label>
                  <div className="flex items-center gap-2">
                    <input
                      type="range"
                      min={1}
                      max={50}
                      value={sampleRate * 100}
                      onChange={e => setSampleRate(Number(e.target.value) / 100)}
                      disabled={useFixed}
                      className="flex-1 accent-sage-500"
                    />
                    <span className="font-mono text-xs text-content-primary w-10 text-right">
                      {(sampleRate * 100).toFixed(0)}%
                    </span>
                  </div>
                </div>
                <div>
                  <label className="font-serif text-xs text-content-primary mb-2 block">
                    <input
                      type="radio"
                      checked={useFixed}
                      onChange={() => setUseFixed(true)}
                      className="mr-2"
                    />
                    Fixed per Stratum
                  </label>
                  <input
                    type="number"
                    min={1}
                    max={100}
                    value={fixedPerStratum ?? 5}
                    onChange={e => setFixedPerStratum(Number(e.target.value))}
                    disabled={!useFixed}
                    className="w-full bg-surface-input border border-theme rounded-lg px-3 py-1.5 font-mono text-xs text-content-primary disabled:opacity-40"
                  />
                </div>
              </div>

              {error && (
                <p className="font-sans text-xs text-clay-600">{error}</p>
              )}

              <button
                onClick={handlePreview}
                disabled={loading || criteria.length === 0}
                className="w-full px-4 py-2.5 bg-sage-600 text-white rounded-xl font-sans text-sm hover:bg-sage-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Loading preview...' : 'Preview Strata'}
              </button>
            </motion.div>
          )}

          {/* Step 2: Preview */}
          {step === 'preview' && preview && (
            <motion.div
              key="preview"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 12 }}
              className="space-y-4"
            >
              <div className="flex items-center justify-between mb-2">
                <div>
                  <p className="font-sans text-xs text-content-secondary">
                    <span className="font-mono text-content-primary">{preview.strata.length}</span> strata found across{' '}
                    <span className="font-mono text-content-primary">{preview.total_population.toLocaleString()}</span> entries
                  </p>
                </div>
                <button
                  onClick={handleReset}
                  className="font-sans text-xs text-content-tertiary hover:text-content-primary transition-colors"
                >
                  Back
                </button>
              </div>

              {/* Strata table */}
              <div className="max-h-60 overflow-y-auto rounded-lg border border-theme">
                <table className="w-full">
                  <thead className="bg-surface-card-secondary sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2 font-sans text-[10px] text-content-tertiary uppercase tracking-wider">Stratum</th>
                      <th className="text-right px-3 py-2 font-sans text-[10px] text-content-tertiary uppercase tracking-wider">Population</th>
                      <th className="text-right px-3 py-2 font-sans text-[10px] text-content-tertiary uppercase tracking-wider">Est. Sample</th>
                    </tr>
                  </thead>
                  <tbody>
                    {preview.strata.slice(0, 25).map((s, i) => {
                      const estSample = useFixed && fixedPerStratum
                        ? Math.min(fixedPerStratum, s.population_size)
                        : Math.max(1, Math.round(s.population_size * sampleRate))
                      return (
                        <tr key={i} className="border-t border-theme-divider">
                          <td className="px-3 py-1.5 font-sans text-xs text-content-primary truncate max-w-[200px]">{s.name}</td>
                          <td className="px-3 py-1.5 font-mono text-xs text-content-secondary text-right">{s.population_size}</td>
                          <td className="px-3 py-1.5 font-mono text-xs text-sage-600 text-right">{estSample}</td>
                        </tr>
                      )
                    })}
                  </tbody>
                </table>
                {preview.strata.length > 25 && (
                  <p className="text-center text-content-tertiary text-xs py-2">
                    + {preview.strata.length - 25} more strata
                  </p>
                )}
              </div>

              {error && (
                <p className="font-sans text-xs text-clay-600">{error}</p>
              )}

              <button
                onClick={handleSample}
                disabled={loading}
                className="w-full px-4 py-2.5 bg-sage-600 text-white rounded-xl font-sans text-sm hover:bg-sage-700 transition-colors disabled:opacity-50"
              >
                {loading ? 'Running CSPRNG sampling...' : 'Execute Sampling'}
              </button>
            </motion.div>
          )}

          {/* Step 3: Results */}
          {step === 'results' && result && (
            <motion.div
              key="results"
              initial={{ opacity: 0, x: 12 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: 12 }}
              className="space-y-4"
            >
              {/* Summary stats */}
              <div className="grid grid-cols-3 gap-3">
                <div className="bg-surface-card-secondary rounded-lg p-3 text-center">
                  <p className="font-mono text-lg text-content-primary">{result.total_population.toLocaleString()}</p>
                  <p className="font-sans text-[10px] text-content-tertiary">Population</p>
                </div>
                <div className="bg-surface-card-secondary rounded-lg p-3 text-center">
                  <p className="font-mono text-lg text-sage-600">{result.total_sampled.toLocaleString()}</p>
                  <p className="font-sans text-[10px] text-content-tertiary">Sampled</p>
                </div>
                <div className="bg-surface-card-secondary rounded-lg p-3 text-center">
                  <p className="font-mono text-lg text-content-primary">{result.strata.length}</p>
                  <p className="font-sans text-[10px] text-content-tertiary">Strata</p>
                </div>
              </div>

              {/* Seed for reproducibility */}
              <div className="bg-surface-card-secondary rounded-lg px-3 py-2 flex items-center justify-between">
                <span className="font-sans text-xs text-content-tertiary">Sampling Seed</span>
                <span className="font-mono text-xs text-content-secondary">{result.sampling_seed.slice(0, 16)}...</span>
              </div>

              {/* Strata results */}
              <div className="max-h-60 overflow-y-auto rounded-lg border border-theme">
                <table className="w-full">
                  <thead className="bg-surface-card-secondary sticky top-0">
                    <tr>
                      <th className="text-left px-3 py-2 font-sans text-[10px] text-content-tertiary uppercase tracking-wider">Stratum</th>
                      <th className="text-right px-3 py-2 font-sans text-[10px] text-content-tertiary uppercase tracking-wider">Pop.</th>
                      <th className="text-right px-3 py-2 font-sans text-[10px] text-content-tertiary uppercase tracking-wider">Sampled</th>
                      <th className="text-right px-3 py-2 font-sans text-[10px] text-content-tertiary uppercase tracking-wider">Rate</th>
                    </tr>
                  </thead>
                  <tbody>
                    {result.strata.map((s, i) => (
                      <tr key={i} className="border-t border-theme-divider">
                        <td className="px-3 py-1.5 font-sans text-xs text-content-primary truncate max-w-[180px]">{s.name}</td>
                        <td className="px-3 py-1.5 font-mono text-xs text-content-secondary text-right">{s.population_size}</td>
                        <td className="px-3 py-1.5 font-mono text-xs text-sage-600 text-right">{s.sample_size}</td>
                        <td className="px-3 py-1.5 font-mono text-xs text-content-tertiary text-right">
                          {(s.sample_size / s.population_size * 100).toFixed(0)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>

              <div className="flex gap-3">
                <button
                  onClick={handleReset}
                  className="flex-1 px-4 py-2.5 bg-surface-card border border-oatmeal-300 rounded-xl text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
                >
                  New Sample
                </button>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </div>
  )
}
