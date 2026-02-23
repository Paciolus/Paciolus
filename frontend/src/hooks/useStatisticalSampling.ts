/**
 * Statistical Sampling Hook — Sprint 270
 * Phase XXXVI: Tool 12
 *
 * Custom hook (NOT factory-based) — two independent API calls:
 *   1. runDesign(file, config) → SamplingDesignResult
 *   2. runEvaluation(file, config) → SamplingEvaluationResult
 *
 * Each phase has independent status/result/error state.
 */

import { useState, useCallback } from 'react'
import { useAuth } from '@/contexts/AuthContext'
import { useOptionalEngagementContext } from '@/contexts/EngagementContext'
import type { UploadStatus } from '@/types/shared'
import type {
  SamplingDesignResult,
  SamplingDesignConfig,
  SamplingEvaluationResult,
  SamplingEvaluationConfig,
} from '@/types/statisticalSampling'
import { getCsrfToken } from '@/utils/apiClient'
import { API_URL } from '@/utils/constants'

interface PhaseState<T> {
  status: UploadStatus
  result: T | null
  error: string
}

export interface UseStatisticalSamplingReturn {
  // Design phase
  designStatus: UploadStatus
  designResult: SamplingDesignResult | null
  designError: string
  runDesign: (file: File, config: SamplingDesignConfig) => Promise<void>
  resetDesign: () => void
  // Evaluation phase
  evalStatus: UploadStatus
  evalResult: SamplingEvaluationResult | null
  evalError: string
  runEvaluation: (file: File, config: SamplingEvaluationConfig) => Promise<void>
  resetEvaluation: () => void
}

export function useStatisticalSampling(): UseStatisticalSamplingReturn {
  const { token, user } = useAuth()
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId

  const [design, setDesign] = useState<PhaseState<SamplingDesignResult>>({
    status: 'idle',
    result: null,
    error: '',
  })

  const [evaluation, setEvaluation] = useState<PhaseState<SamplingEvaluationResult>>({
    status: 'idle',
    result: null,
    error: '',
  })

  const runDesign = useCallback(async (file: File, config: SamplingDesignConfig) => {
    if (user && user.is_verified === false) {
      setDesign({ status: 'error', result: null, error: 'Please verify your email address before running sampling.' })
      return
    }

    setDesign({ status: 'loading', result: null, error: '' })

    const formData = new FormData()
    formData.append('file', file)
    formData.append('method', config.method)
    formData.append('confidence_level', config.confidence_level.toString())
    formData.append('tolerable_misstatement', config.tolerable_misstatement.toString())
    formData.append('expected_misstatement', config.expected_misstatement.toString())
    if (config.stratification_threshold !== null) {
      formData.append('stratification_threshold', config.stratification_threshold.toString())
    }
    if (config.sample_size_override !== null) {
      formData.append('sample_size_override', config.sample_size_override.toString())
    }
    if (engagementId) {
      formData.append('engagement_id', engagementId.toString())
    }

    try {
      const csrfToken = getCsrfToken()
      const response = await fetch(`${API_URL}/audit/sampling/design`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setDesign({ status: 'error', result: null, error: 'Please sign in to run statistical sampling.' })
        return
      }

      const data = await response.json()

      if (!response.ok) {
        const detail = data?.detail || 'Sample design failed. Please check your parameters.'
        setDesign({ status: 'error', result: null, error: detail })
        return
      }

      setDesign({ status: 'success', result: data as SamplingDesignResult, error: '' })
    } catch {
      setDesign({ status: 'error', result: null, error: 'Network error. Please try again.' })
    }
  }, [token, user, engagementId])

  const runEvaluation = useCallback(async (file: File, config: SamplingEvaluationConfig) => {
    if (user && user.is_verified === false) {
      setEvaluation({ status: 'error', result: null, error: 'Please verify your email address before running evaluation.' })
      return
    }

    setEvaluation({ status: 'loading', result: null, error: '' })

    const formData = new FormData()
    formData.append('file', file)
    formData.append('method', config.method)
    formData.append('confidence_level', config.confidence_level.toString())
    formData.append('tolerable_misstatement', config.tolerable_misstatement.toString())
    formData.append('expected_misstatement', config.expected_misstatement.toString())
    formData.append('population_value', config.population_value.toString())
    formData.append('sample_size', config.sample_size.toString())
    if (config.sampling_interval !== null) {
      formData.append('sampling_interval', config.sampling_interval.toString())
    }
    if (engagementId) {
      formData.append('engagement_id', engagementId.toString())
    }

    try {
      const csrfToken = getCsrfToken()
      const response = await fetch(`${API_URL}/audit/sampling/evaluate`, {
        method: 'POST',
        headers: {
          ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
          ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        },
        body: formData,
      })

      if (response.status === 401) {
        setEvaluation({ status: 'error', result: null, error: 'Please sign in to run evaluation.' })
        return
      }

      const data = await response.json()

      if (!response.ok) {
        const detail = data?.detail || 'Sample evaluation failed. Please check your parameters.'
        setEvaluation({ status: 'error', result: null, error: detail })
        return
      }

      setEvaluation({ status: 'success', result: data as SamplingEvaluationResult, error: '' })
    } catch {
      setEvaluation({ status: 'error', result: null, error: 'Network error. Please try again.' })
    }
  }, [token, user, engagementId])

  const resetDesign = useCallback(() => {
    setDesign({ status: 'idle', result: null, error: '' })
  }, [])

  const resetEvaluation = useCallback(() => {
    setEvaluation({ status: 'idle', result: null, error: '' })
  }, [])

  return {
    designStatus: design.status,
    designResult: design.result,
    designError: design.error,
    runDesign,
    resetDesign,
    evalStatus: evaluation.status,
    evalResult: evaluation.result,
    evalError: evaluation.error,
    runEvaluation,
    resetEvaluation,
  }
}
