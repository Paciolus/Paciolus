/**
 * useCanvasAccentSync — maps tool UploadStatus to canvas AccentState
 *
 * Call from any tool page to sync its processing status
 * with the IntelligenceCanvas accent glow and particle speed.
 *
 * Mapping: idle→idle, loading→analyze, success→validate, error→idle
 */

import { useEffect } from 'react'
import { useCanvasAccent } from '@/contexts/CanvasAccentContext'
import type { AccentState } from '@/components/shared/IntelligenceCanvas'
import type { UploadStatus } from '@/types/shared'

const STATUS_TO_ACCENT: Record<UploadStatus, AccentState> = {
  idle: 'idle',
  loading: 'analyze',
  success: 'validate',
  error: 'idle',
}

export function useCanvasAccentSync(status: UploadStatus): void {
  const { setAccentState } = useCanvasAccent()

  useEffect(() => {
    setAccentState(STATUS_TO_ACCENT[status])
  }, [status, setAccentState])
}
