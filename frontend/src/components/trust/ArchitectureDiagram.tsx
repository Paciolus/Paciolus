'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { BrandIcon } from '@/components/shared'
import { FLOW_STAGES, accentClasses, architectureNodes } from '@/content/trust'
import { containerVariants, lineGrow, scaleIn, vertLineGrow } from './variants'

export function ArchitectureDiagram() {
  const [expanded, setExpanded] = useState<string | null>(null)

  const toggle = useCallback((id: string) => {
    setExpanded(prev => prev === id ? null : id)
  }, [])

  return (
    <div>
      {/* ── Ephemeral Zone (dashed border container) ── */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="relative rounded-2xl border-2 border-dashed border-sage-500/30 p-8 md:p-10 mb-6"
      >
        {/* Ephemeral Zone label */}
        <div className="absolute -top-3 left-6 px-3 py-0.5 bg-obsidian-800 rounded-md">
          <span className="font-mono text-[11px] text-sage-400 tracking-wider uppercase">
            Ephemeral Zone
          </span>
        </div>
        <p className="font-sans text-xs text-oatmeal-500 mb-8 text-center">
          Your upload lives here temporarily — processed in memory, then released
        </p>

        {/* Desktop: Horizontal Pipeline */}
        <div className="hidden md:block">
          <div className="relative">
            {/* Connecting arrow lines */}
            <div className="absolute top-[3.25rem] left-0 right-0 flex justify-center pointer-events-none z-0" aria-hidden="true">
              <div className="w-full max-w-3xl flex">
                {[0, 1].map(i => (
                  <div key={i} className="flex-1 flex items-center justify-center px-8">
                    <motion.div
                      variants={lineGrow}
                      className="w-full h-0.5 bg-gradient-to-r from-sage-500/40 to-sage-500/30"
                    />
                    <svg className="w-3 h-3 text-theme-success-text/50 -ml-1 shrink-0" fill="currentColor" viewBox="0 0 24 24" aria-hidden="true">
                      <path d="M10 6l6 6-6 6V6z" />
                    </svg>
                  </div>
                ))}
              </div>
            </div>

            {/* Stage Cards */}
            <div className="grid grid-cols-3 gap-8 relative z-10">
              {FLOW_STAGES.map(stage => {
                const node = stage.nodeRef
                if (!node) return null
                const a = accentClasses(node.accent)
                const isExpanded = expanded === stage.id

                return (
                  <motion.div key={stage.id} variants={scaleIn} className="flex flex-col items-center text-center">
                    {/* Icon */}
                    <button
                      onClick={() => toggle(stage.id)}
                      aria-expanded={isExpanded}
                      aria-controls={`flow-detail-${stage.id}`}
                      className={`relative w-[4.5rem] h-[4.5rem] rounded-2xl ${a.bg} border ${a.border} flex items-center justify-center mb-4 ${a.text} shadow-lg ${a.glow} transition-all duration-200 hover:border-sage-500/60 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-400`}
                    >
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-oatmeal-50/5 to-transparent pointer-events-none" />
                      <BrandIcon name={stage.icon} className="w-7 h-7" />
                    </button>

                    <h3 className="font-serif text-lg text-oatmeal-100 mb-1">{stage.label}</h3>
                    <p className="font-sans text-xs text-oatmeal-400 mb-3">{stage.description}</p>

                    {/* Expandable controls */}
                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          id={`flow-detail-${stage.id}`}
                          role="region"
                          aria-label={`${stage.label} security controls`}
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3, ease: 'easeOut' as const }}
                          className="w-full overflow-hidden"
                        >
                          <div className="space-y-2 pt-1">
                            {node.controls.map(ctrl => (
                              <div key={ctrl.label} className="bg-obsidian-800/60 border border-obsidian-600 rounded-lg px-3 py-2 text-left">
                                <p className="font-sans text-xs font-medium text-oatmeal-200">{ctrl.label}</p>
                                <p className="font-sans text-[11px] text-oatmeal-500 leading-relaxed mt-0.5">{ctrl.detail}</p>
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {!isExpanded && (
                      <p className="font-sans text-[11px] text-oatmeal-600 mt-1">
                        {node.controls.length} controls — click to expand
                      </p>
                    )}
                  </motion.div>
                )
              })}
            </div>
          </div>
        </div>

        {/* Mobile: Vertical Pipeline */}
        <div className="md:hidden relative">
          {/* Vertical line */}
          <motion.div
            variants={vertLineGrow}
            className="absolute left-[2.25rem] top-8 bottom-8 w-0.5 bg-gradient-to-b from-sage-500/40 to-sage-500/20 z-0"
            aria-hidden="true"
          />

          <div className="space-y-8">
            {FLOW_STAGES.map(stage => {
              const node = stage.nodeRef
              if (!node) return null
              const a = accentClasses(node.accent)
              const isExpanded = expanded === stage.id

              return (
                <motion.div key={stage.id} variants={scaleIn} className="relative flex items-start gap-5">
                  <button
                    onClick={() => toggle(stage.id)}
                    aria-expanded={isExpanded}
                    aria-controls={`flow-detail-m-${stage.id}`}
                    className={`relative z-10 flex-shrink-0 w-[4.5rem] h-[4.5rem] rounded-xl ${a.bg} border ${a.border} flex items-center justify-center ${a.text} shadow-lg ${a.glow} focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-400`}
                  >
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-oatmeal-50/5 to-transparent pointer-events-none" />
                    <BrandIcon name={stage.icon} className="w-7 h-7" />
                  </button>

                  <div className="flex-1 pt-1">
                    <h3 className="font-serif text-lg text-oatmeal-100 mb-1">{stage.label}</h3>
                    <p className="font-sans text-xs text-oatmeal-400 mb-2">{stage.description}</p>

                    <AnimatePresence>
                      {isExpanded && (
                        <motion.div
                          id={`flow-detail-m-${stage.id}`}
                          role="region"
                          aria-label={`${stage.label} security controls`}
                          initial={{ opacity: 0, height: 0 }}
                          animate={{ opacity: 1, height: 'auto' }}
                          exit={{ opacity: 0, height: 0 }}
                          transition={{ duration: 0.3, ease: 'easeOut' as const }}
                          className="overflow-hidden"
                        >
                          <div className="space-y-2 pt-1">
                            {node.controls.map(ctrl => (
                              <div key={ctrl.label} className="bg-obsidian-800/60 border border-obsidian-600 rounded-lg px-3 py-2">
                                <p className="font-sans text-xs font-medium text-oatmeal-200">{ctrl.label}</p>
                                <p className="font-sans text-[11px] text-oatmeal-500 leading-relaxed mt-0.5">{ctrl.detail}</p>
                              </div>
                            ))}
                          </div>
                        </motion.div>
                      )}
                    </AnimatePresence>

                    {!isExpanded && (
                      <p className="font-sans text-[11px] text-oatmeal-600 mt-1">
                        Tap to view {node.controls.length} controls
                      </p>
                    )}
                  </div>
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.div>

      {/* ── Purge Indicator ── */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.4 }}
        className="flex items-center justify-center gap-3 mb-8"
      >
        <div className="h-8 w-0.5 bg-gradient-to-b from-sage-500/40 to-oatmeal-400/20" />
        <svg className="w-5 h-5 text-oatmeal-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
        <span className="font-sans text-sm text-oatmeal-400">Data destroyed after processing</span>
      </motion.div>

      {/* ── Persistent Boundary ── */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.5 }}
        className="rounded-2xl border border-oatmeal-400/20 bg-obsidian-800/40 p-6 md:p-8"
      >
        <div className="flex items-center gap-3 mb-4">
          <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-400/60" />
          <span className="font-mono text-[11px] text-oatmeal-500 tracking-wider uppercase">
            Persistent Storage
          </span>
        </div>
        <h3 className="font-serif text-lg text-oatmeal-100 mb-2">What we store</h3>
        <p className="font-sans text-sm text-oatmeal-400 leading-relaxed mb-4">
          User profiles, practice settings, engagement metadata, and aggregate diagnostic summaries. No raw files. No line-level financial data. No client PII in analysis results.
        </p>
        {architectureNodes[3] && (
          <div className="space-y-2">
            {architectureNodes[3].controls.map(ctrl => (
              <div key={ctrl.label} className="bg-obsidian-800/60 border border-obsidian-600 rounded-lg px-3 py-2">
                <p className="font-sans text-xs font-medium text-oatmeal-200">{ctrl.label}</p>
                <p className="font-sans text-[11px] text-oatmeal-500 leading-relaxed mt-0.5">{ctrl.detail}</p>
              </div>
            ))}
          </div>
        )}
      </motion.div>

      {/* Upload-handling summary pill */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="max-w-lg mx-auto text-center mt-14"
      >
        <Link
          href="/approach"
          className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-obsidian-800/70 border border-obsidian-500/40 hover:border-sage-500/30 transition-colors group"
        >
          <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" aria-hidden="true" />
          <span className="font-sans text-sm text-oatmeal-400">
            Uploaded files are not kept after analysis
          </span>
          <BrandIcon name="chevron-right" className="w-3.5 h-3.5 text-sage-400 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </motion.div>
    </div>
  )
}
