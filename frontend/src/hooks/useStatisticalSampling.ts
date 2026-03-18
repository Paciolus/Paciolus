/**
 * Statistical Sampling Hook — Sprint 270
 * Phase XXXVI: Tool 12
 *
 * Custom hook (NOT factory-based) — two independent API calls:
 *   1. runDesign(file, config) → SamplingDesignResult
 *   2. runEvaluation(file, config) → SamplingEvaluationResult
 *
 * Each phase has independent status/result/error state.
 * Sprint 551: Unified upload handler to eliminate duplication.
 */

import { useState, useCallback } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
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

const INITIAL_STATE = { status: 'idle' as UploadStatus, result: null, error: '' }

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

/**
 * Shared upload handler for both sampling phases.
 * Handles verification check, FormData construction, auth headers, and error handling.
 */
async function executeSamplingUpload<T>(
  endpoint: string,
  file: File,
  fields: Record<string, string | number | null | undefined>,
  token: string | null,
  user: { is_verified?: boolean } | null,
  setState: (s: PhaseState<T>) => void,
  errorPrefix: string,
): Promise<void> {
  if (user && user.is_verified === false) {
    setState({ status: 'error', result: null, error: `Please verify your email address before running ${errorPrefix}.` })
    return
  }

  setState({ status: 'loading', result: null, error: '' })

  const formData = new FormData()
  formData.append('file', file)
  for (const [key, value] of Object.entries(fields)) {
    if (value !== null && value !== undefined) {
      formData.append(key, value.toString())
    }
  }

  try {
    const csrfToken = getCsrfToken()
    const response = await fetch(`${API_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
      },
      body: formData,
    })

    if (response.status === 401) {
      setState({ status: 'error', result: null, error: `Please sign in to run ${errorPrefix}.` })
      return
    }

    const data = await response.json()

    if (!response.ok) {
      const detail = data?.detail || `${errorPrefix} failed. Please check your parameters.`
      setState({ status: 'error', result: null, error: detail })
      return
    }

    setState({ status: 'success', result: data as T, error: '' })
  } catch {
    setState({ status: 'error', result: null, error: 'Network error. Please try again.' })
  }
}

export function useStatisticalSampling(): UseStatisticalSamplingReturn {
  const { token, user } = useAuthSession()
  const engagement = useOptionalEngagementContext()
  const engagementId = engagement?.engagementId

  const [design, setDesign] = useState<PhaseState<SamplingDesignResult>>(INITIAL_STATE)
  const [evaluation, setEvaluation] = useState<PhaseState<SamplingEvaluationResult>>(INITIAL_STATE)

  const runDesign = useCallback(async (file: File, config: SamplingDesignConfig) => {
    await executeSamplingUpload<SamplingDesignResult>(
      '/audit/sampling/design',
      file,
      {
        method: config.method,
        confidence_level: config.confidence_level,
        tolerable_misstatement: config.tolerable_misstatement,
        expected_misstatement: config.expected_misstatement,
        stratification_threshold: config.stratification_threshold,
        sample_size_override: config.sample_size_override,
        engagement_id: engagementId,
      },
      token,
      user,
      setDesign,
      'sampling',
    )
  }, [token, user, engagementId])

  const runEvaluation = useCallback(async (file: File, config: SamplingEvaluationConfig) => {
    await executeSamplingUpload<SamplingEvaluationResult>(
      '/audit/sampling/evaluate',
      file,
      {
        method: config.method,
        confidence_level: config.confidence_level,
        tolerable_misstatement: config.tolerable_misstatement,
        expected_misstatement: config.expected_misstatement,
        population_value: config.population_value,
        sample_size: config.sample_size,
        sampling_interval: config.sampling_interval,
        engagement_id: engagementId,
      },
      token,
      user,
      setEvaluation,
      'evaluation',
    )
  }, [token, user, engagementId])

  const resetDesign = useCallback(() => setDesign(INITIAL_STATE), [])
  const resetEvaluation = useCallback(() => setEvaluation(INITIAL_STATE), [])

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
