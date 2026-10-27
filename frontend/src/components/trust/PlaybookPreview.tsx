'use client'

import { useState } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import { BrandIcon } from '@/components/shared'
import { accentClasses, playbookPhases } from '@/content/trust'
import { containerVariants, fadeUp } from './variants'

export function PlaybookPreview() {
  const [activePhase, setActivePhase] = useState(0)

  return (
    <div>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Phase Selector Tabs */}
        <motion.div
          variants={fadeUp}
          className="flex items-center justify-center gap-2 mb-10"
          role="tablist"
          aria-label="Incident response phases"
        >
          {playbookPhases.map((phase, i) => {
            const a = accentClasses(phase.accent)
            const isActive = activePhase === i
            return (
              <button
                key={phase.title}
                role="tab"
                aria-selected={isActive}
                aria-controls={`playbook-panel-${i}`}
                id={`playbook-tab-${i}`}
                onClick={() => setActivePhase(i)}
                className={`inline-flex items-center gap-2 px-4 py-2.5 rounded-xl font-sans text-sm transition-all duration-200 border focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-400 ${
                  isActive
                    ? `${a.bg} ${a.border} ${a.text}`
                    : 'bg-obsidian-800/40 border-obsidian-700 text-oatmeal-500 hover:text-oatmeal-300 hover:border-obsidian-500'
                }`}
              >
                <BrandIcon name={phase.icon} className="w-4 h-4" />
                <span className="hidden sm:inline">{phase.title}</span>
              </button>
            )
          })}
        </motion.div>

        {/* Active Phase Panel */}
        <AnimatePresence mode="wait">
          {playbookPhases.map((phase, i) => {
            if (i !== activePhase) return null
            const a = accentClasses(phase.accent)
            return (
              <motion.div
                key={phase.title}
                id={`playbook-panel-${i}`}
                role="tabpanel"
                aria-labelledby={`playbook-tab-${i}`}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -12 }}
                transition={{ duration: 0.3, ease: 'easeOut' as const }}
                className={`bg-obsidian-800/60 border-l-4 ${a.border} rounded-r-xl p-6 md:p-8 max-w-3xl mx-auto`}
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className={`w-10 h-10 rounded-xl ${a.bg} border ${a.border} flex items-center justify-center ${a.text}`}>
                    <BrandIcon name={phase.icon} className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="font-serif text-xl text-oatmeal-100">{phase.title}</h3>
                    <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Phase {String(i + 1).padStart(2, '0')}</p>
                  </div>
                </div>

                <p className="font-sans text-sm text-oatmeal-300 leading-relaxed mb-5">{phase.description}</p>

                <ul className="space-y-2.5">
                  {phase.measures.map(measure => (
                    <li key={measure} className="flex items-start gap-2.5">
                      <BrandIcon name="checkmark" className="w-3.5 h-3.5 text-sage-400 flex-shrink-0 mt-0.5" />
                      <span className="font-sans text-xs text-oatmeal-400 leading-relaxed">{measure}</span>
                    </li>
                  ))}
                </ul>
              </motion.div>
            )
          })}
        </AnimatePresence>

        {/* Organization CTA */}
        <motion.div variants={fadeUp} className="text-center mt-10">
          <Link
            href="/contact?inquiry_type=organization"
            className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-obsidian-800/70 border border-obsidian-500/40 hover:border-sage-500/30 transition-colors group font-sans text-sm text-oatmeal-400"
          >
            <BrandIcon name="shield-check" className="w-4 h-4 text-sage-400" />
            Full playbook available on request for Organization accounts
            <BrandIcon name="chevron-right" className="w-3.5 h-3.5 text-sage-400 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </motion.div>
      </motion.div>
    </div>
  )
}
