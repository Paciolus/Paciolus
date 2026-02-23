/**
 * useCanvasAccentSync — maps tool UploadStatus to canvas AccentState
 *
 * Call from any tool page to sync its processing status
 * with the IntelligenceCanvas accent glow and particle speed.
 *
 * Mapping: idle→idle, loading→analyze, success→validate, error→idle
 */

import { useEffect, useRef } from 'react'
import type { AccentState } from '@/components/shared/IntelligenceCanvas'
import { useSonification } from '@/hooks/useSonification'
import { useCanvasAccent } from '@/contexts/CanvasAccentContext'
import type { UploadStatus } from '@/types/shared'

const STATUS_TO_ACCENT: Record<UploadStatus, AccentState> = {
  idle: 'idle',
  loading: 'analyze',
  success: 'validate',
  error: 'idle',
}

const STATUS_TO_TONE: Partial<Record<UploadStatus, 'uploadStart' | 'success' | 'error'>> = {
  loading: 'uploadStart',
  success: 'success',
  error: 'error',
}

export function useCanvasAccentSync(status: UploadStatus): void {
  const { setAccentState } = useCanvasAccent()
  const { playTone } = useSonification()
  const prevStatus = useRef<UploadStatus>(status)

  useEffect(() => {
    setAccentState(STATUS_TO_ACCENT[status])

    // Play tone only on status transitions (not initial mount)
    if (prevStatus.current !== status) {
      const tone = STATUS_TO_TONE[status]
      if (tone) playTone(tone)
      prevStatus.current = status
    }
  }, [status, setAccentState, playTone])
}
