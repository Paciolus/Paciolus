'use client'

import { useState, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { BrandIcon } from '@/components/shared'
import { accentClasses, controlCategories, securityControls, type ControlCategory } from '@/content/trust'
import { containerVariants, fadeUp } from './variants'

export function ControlMatrix() {
  const [expandedDomain, setExpandedDomain] = useState<ControlCategory | null>(null)

  const toggleDomain = useCallback((cat: ControlCategory) => {
    setExpandedDomain(prev => prev === cat ? null : cat)
  }, [])

  return (
    <motion.div
      variants={containerVariants}
      initial="hidden"
      animate="visible"
      className="max-w-3xl mx-auto space-y-2"
    >
      {controlCategories.map(cat => {
        const domainControls = securityControls.filter(c => c.category === cat.key)
        const isOpen = expandedDomain === cat.key
        const a = accentClasses(cat.key === 'authentication' || cat.key === 'tenancy' ? 'sage' : 'oatmeal')

        return (
          <motion.div key={cat.key} variants={fadeUp}>
            {/* Domain Header Row */}
            <button
              onClick={() => toggleDomain(cat.key)}
              aria-expanded={isOpen}
              aria-controls={`domain-panel-${cat.key}`}
              className={`w-full flex items-center gap-4 px-5 py-4 rounded-xl border transition-all duration-200 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-400 ${
                isOpen
                  ? `${a.bg} ${a.border}`
                  : 'bg-obsidian-800/60 border-obsidian-600 hover:border-obsidian-500/60'
              }`}
            >
              <div className={`w-9 h-9 rounded-lg ${a.bg} border ${a.border} flex items-center justify-center ${a.text} flex-shrink-0`}>
                <BrandIcon name={cat.icon} className="w-4.5 h-4.5" />
              </div>
              <div className="flex-1 text-left">
                <span className="font-serif text-sm text-oatmeal-100">{cat.label}</span>
                <span className="font-mono text-[11px] text-oatmeal-500 ml-2">
                  {domainControls.length} controls
                </span>
              </div>
              {/* Collapsed: show standard refs as compact pills */}
              {!isOpen && (
                <div className="hidden sm:flex items-center gap-1.5 flex-shrink-0">
                  {domainControls.slice(0, 3).map(ctrl => (
                    <span
                      key={ctrl.standard}
                      className="font-mono text-[9px] text-oatmeal-600 px-1.5 py-0.5 rounded bg-obsidian-700/50 border border-obsidian-600/50"
                    >
                      {ctrl.standard}
                    </span>
                  ))}
                  {domainControls.length > 3 && (
                    <span className="font-mono text-[9px] text-oatmeal-600">
                      +{domainControls.length - 3}
                    </span>
                  )}
                </div>
              )}
              <BrandIcon
                name="chevron-right"
                className={`w-4 h-4 text-oatmeal-500 transition-transform duration-200 flex-shrink-0 ${isOpen ? 'rotate-90' : ''}`}
              />
            </button>

            {/* Expanded: control list */}
            <AnimatePresence>
              {isOpen && (
                <motion.div
                  id={`domain-panel-${cat.key}`}
                  role="region"
                  aria-label={`${cat.label} security controls`}
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  transition={{ duration: 0.3, ease: 'easeOut' as const }}
                  className="overflow-hidden"
                >
                  <div className="pt-2 pb-1 space-y-1">
                    {domainControls.map(ctrl => (
                      <div
                        key={ctrl.name}
                        className="flex items-start gap-3 px-5 py-3 rounded-lg bg-obsidian-800/40 border border-obsidian-700/50"
                      >
                        <div className="flex-shrink-0 w-2 h-2 mt-1.5 rounded-full bg-sage-400" aria-hidden="true" />
                        <div className="flex-1 min-w-0">
                          <div className="flex items-baseline justify-between gap-3">
                            <span className="font-sans text-sm text-oatmeal-200">{ctrl.name}</span>
                            <span className="font-mono text-[10px] text-sage-400/80 flex-shrink-0">{ctrl.standard}</span>
                          </div>
                          <p className="font-sans text-[11px] text-oatmeal-500 leading-relaxed mt-1">{ctrl.description}</p>
                        </div>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </motion.div>
        )
      })}
    </motion.div>
  )
}
