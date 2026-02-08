'use client'

/**
 * EngagementBanner — Sprint 103: Tool-Engagement Integration
 *
 * Thin bar displayed at top of tool pages when an engagement is active.
 * Shows client name + period range + Unlink button.
 *
 * Guardrail: "Linked to Diagnostic Workspace" — never "Audit Engagement"
 */

import { motion, AnimatePresence } from 'framer-motion'
import { useClients } from '@/hooks/useClients'
import { useEffect, useState } from 'react'
import type { Engagement } from '@/types/engagement'

interface EngagementBannerProps {
  activeEngagement: Engagement | null
  onUnlink: () => void
}

export function EngagementBanner({ activeEngagement, onUnlink }: EngagementBannerProps) {
  const { getClient } = useClients({ autoFetch: false })
  const [clientName, setClientName] = useState<string | null>(null)

  useEffect(() => {
    if (!activeEngagement?.client_id) {
      setClientName(null)
      return
    }

    let cancelled = false
    getClient(activeEngagement.client_id).then((client) => {
      if (!cancelled && client) {
        setClientName(client.name)
      }
    })
    return () => { cancelled = true }
  }, [activeEngagement?.client_id, getClient])

  const formatDate = (dateStr: string) => {
    try {
      return new Date(dateStr).toLocaleDateString('en-US', {
        month: 'short',
        year: 'numeric',
      })
    } catch {
      return dateStr
    }
  }

  return (
    <AnimatePresence>
      {activeEngagement && (
        <motion.div
          initial={{ height: 0, opacity: 0 }}
          animate={{ height: 'auto', opacity: 1 }}
          exit={{ height: 0, opacity: 0 }}
          transition={{ duration: 0.2, ease: 'easeOut' as const }}
          className="overflow-hidden"
        >
          <div className="h-10 bg-sage-500/10 border-b border-sage-500/20 flex items-center justify-between px-4">
            <div className="flex items-center gap-2 text-sm font-sans">
              <div className="w-2 h-2 bg-sage-400 rounded-full" />
              <span className="text-sage-300 font-medium">Linked to Diagnostic Workspace</span>
              <span className="text-oatmeal-500">—</span>
              <span className="text-oatmeal-300">
                {clientName || `Client #${activeEngagement.client_id}`}
              </span>
              <span className="text-oatmeal-500 text-xs">
                {formatDate(activeEngagement.period_start)} to {formatDate(activeEngagement.period_end)}
              </span>
            </div>
            <button
              onClick={onUnlink}
              className="text-xs font-sans text-oatmeal-500 hover:text-oatmeal-300 transition-colors px-2 py-1 rounded hover:bg-obsidian-700/30"
            >
              Unlink
            </button>
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  )
}
