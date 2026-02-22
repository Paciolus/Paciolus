'use client'

/**
 * ToolStatePresence — Sprint 402: Phase LVI
 *
 * Single AnimatePresence wrapper for the 4-state tool upload lifecycle.
 * Replaces per-block motion.div wrappers with a unified crossfade:
 * old state slides up 8px + fades out, new state enters from below 8px + fades in.
 *
 * Usage:
 *   <ToolStatePresence status={status}>
 *     {status === 'idle' && <UploadZone />}
 *     {status === 'loading' && <LoadingIndicator />}
 *     {status === 'error' && <ErrorDisplay />}
 *     {status === 'success' && result && <Results />}
 *   </ToolStatePresence>
 */

import { type ReactNode } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import type { UploadStatus } from '@/types/shared'
import { STATE_CROSSFADE } from '@/utils/motionTokens'

interface ToolStatePresenceProps {
  status: UploadStatus
  children: ReactNode
}

export function ToolStatePresence({ status, children }: ToolStatePresenceProps) {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key={status}
        variants={STATE_CROSSFADE}
        initial="initial"
        animate="animate"
        exit="exit"
      >
        {children}
      </motion.div>
    </AnimatePresence>
  )
}
