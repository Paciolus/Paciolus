// Pricing estimator widget: persona selector, segmented inputs, seat calculator, and recommendation engine.
'use client'

import { useState, useCallback } from 'react'
import Link from 'next/link'
import { motion, AnimatePresence } from 'framer-motion'
import {
  type Uploads,
  type Features,
  type TeamSize,
  type PersonaKey,
  type BillingInterval,
  type Persona,
  personas,
  uploadOptions,
  featureOptions,
  teamOptions,
  getRecommendedTier,
  SEAT_CONFIGS,
  calculateSeatCost,
  getSeatCalculatorDescription,
} from '@/domain/pricing'

/* ────────────────────────────────────────────────
   Persona icon SVGs
   ──────────────────────────────────────────────── */

function PersonaIcon({ icon, className }: { icon: Persona['icon']; className?: string }) {
  const cls = className ?? 'w-5 h-5'
  switch (icon) {
    case 'calculator':
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 15.75V18m-7.5-6.75h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25v-.008zm0 2.25h.008v.008H8.25v-.008zm2.25-4.5h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008v-.008zm0 2.25h.008v.008h-.008v-.008zm2.25-4.5h.008v.008H12.75v-.008zm0 2.25h.008v.008H12.75v-.008zm2.25-6.75h.008v.008H15v-.008zm0 2.25h.008v.008H15v-.008zm-2.25 0h.008v.008H12.75v-.008zM6 6.75A.75.75 0 016.75 6h10.5a.75.75 0 01.75.75v10.5a.75.75 0 01-.75.75H6.75a.75.75 0 01-.75-.75V6.75z" />
        </svg>
      )
    case 'building':
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 21h16.5M4.5 3h15M5.25 3v18m13.5-18v18M9 6.75h1.5m-1.5 3h1.5m-1.5 3h1.5m3-6H15m-1.5 3H15m-1.5 3H15M9 21v-3.375c0-.621.504-1.125 1.125-1.125h3.75c.621 0 1.125.504 1.125 1.125V21" />
        </svg>
      )
    case 'users':
      return (
        <svg className={cls} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5} aria-hidden="true">
          <path strokeLinecap="round" strokeLinejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z" />
        </svg>
      )
  }
}

/* ────────────────────────────────────────────────
   Segmented selector
   ──────────────────────────────────────────────── */

function SegmentedSelector<T extends string>({
  label,
  options,
  value,
  onChange,
}: {
  label: string
  options: { value: T; label: string }[]
  value: T
  onChange: (v: T) => void
}) {
  const labelId = `segment-label-${label.replace(/\s+/g, '-').toLowerCase()}`
  return (
    <div>
      <p id={labelId} className="font-sans text-sm text-oatmeal-400 mb-2">{label}</p>
      <div className="flex rounded-xl border border-oatmeal-500/20 overflow-hidden" role="radiogroup" aria-labelledby={labelId}>
        {options.map((opt) => (
          <button
            key={opt.value}
            type="button"
            role="radio"
            aria-checked={value === opt.value}
            onClick={() => onChange(opt.value)}
            className={`flex-1 py-2 px-3 text-xs font-sans transition-colors ${
              value === opt.value
                ? 'bg-oatmeal-200/10 text-oatmeal-200 border-oatmeal-400/30'
                : 'bg-obsidian-800/50 text-oatmeal-500 hover:text-oatmeal-300'
            }`}
          >
            {opt.label}
          </button>
        ))}
      </div>
    </div>
  )
}

/* ────────────────────────────────────────────────
   Seat calculator widget
   ──────────────────────────────────────────────── */

function SeatCalculator({ interval }: { interval: BillingInterval }) {
  const [teamSizes, setTeamSizes] = useState<number[]>(SEAT_CONFIGS.map(c => c.baseSeats))

  const handleChange = useCallback((index: number, value: string) => {
    const num = parseInt(value, 10)
    setTeamSizes(prev => {
      const next = [...prev]
      if (!isNaN(num) && num >= 1) {
        next[index] = Math.min(num, 999)
      } else if (value === '') {
        next[index] = 1
      }
      return next
    })
  }, [])

  const periodLabel = interval === 'annual' ? '/yr' : '/mo'

  return (
    <div className="space-y-6">
      {SEAT_CONFIGS.map((config, idx) => {
        const teamSize = teamSizes[idx] ?? config.baseSeats
        const exceedsLimit = teamSize > config.maxSeats
        const breakdown = exceedsLimit ? null : calculateSeatCost(config, teamSize, interval)
        const seatRate = interval === 'annual' ? config.seatAnnual : config.seatMonthly

        return (
          <div key={config.label} className="rounded-xl border border-sage-500/30 bg-sage-500/5 p-6">
            <h3 className="font-serif text-sm text-sage-300 mb-4">{config.label} Seat Calculator</h3>

            <div className="flex items-center gap-4 mb-5">
              <label htmlFor={`seat-input-${idx}`} className="font-sans text-sm text-oatmeal-400 shrink-0">
                Enter your team size
              </label>
              <input
                id={`seat-input-${idx}`}
                type="number"
                min={1}
                max={999}
                value={teamSize}
                onChange={(e) => handleChange(idx, e.target.value)}
                className="w-24 px-3 py-2 rounded-lg bg-obsidian-700/50 border border-obsidian-500/40 text-oatmeal-100 font-mono text-sm tabular-nums text-center focus:outline-hidden focus:border-sage-500/50 transition-colors"
              />
            </div>

            {exceedsLimit ? (
              <div className="text-center py-4">
                <p className="font-sans text-sm text-oatmeal-300 mb-2">
                  For teams larger than {config.maxSeats} seats, we offer custom pricing.
                </p>
                <Link
                  href="/contact?inquiry=seats"
                  className="inline-flex items-center gap-2 font-sans text-sm text-sage-400 hover:text-sage-300 underline underline-offset-2"
                >
                  Contact sales
                </Link>
              </div>
            ) : breakdown && (
              <div className="space-y-2.5 font-sans text-sm">
                <div className="flex justify-between text-oatmeal-400">
                  <span>Base plan ({config.baseSeats} seats included)</span>
                  <span className="font-mono tabular-nums text-oatmeal-200">
                    ${breakdown.baseCost.toLocaleString()}{periodLabel}
                  </span>
                </div>
                {breakdown.additionalSeats > 0 && (
                  <div className="flex justify-between text-oatmeal-400">
                    <span>+{breakdown.additionalSeats} additional seat{breakdown.additionalSeats !== 1 ? 's' : ''} @ ${seatRate}{periodLabel}</span>
                    <span className="font-mono tabular-nums text-oatmeal-200">
                      ${breakdown.seatCost.toLocaleString()}{periodLabel}
                    </span>
                  </div>
                )}
                <div className="flex justify-between pt-2.5 border-t border-sage-500/30 text-oatmeal-100 font-medium">
                  <span>Total</span>
                  <span className="font-mono tabular-nums text-lg text-sage-300">
                    ${breakdown.totalCost.toLocaleString()}{periodLabel}
                  </span>
                </div>
              </div>
            )}
          </div>
        )
      })}
    </div>
  )
}

/* ────────────────────────────────────────────────
   Exported composite widget
   ──────────────────────────────────────────────── */

export default function PricingEstimator({ interval }: { interval: BillingInterval }) {
  const [uploads, setUploads] = useState<Uploads>('under-10')
  const [features, setFeatures] = useState<Features>('basic')
  const [teamSize, setTeamSize] = useState<TeamSize>('solo')
  const [activePersona, setActivePersona] = useState<PersonaKey | null>(null)

  const recommendedTier = getRecommendedTier(uploads, features, teamSize)

  function selectPersona(persona: Persona) {
    setActivePersona(persona.key)
    setUploads(persona.defaults.uploads)
    setFeatures(persona.defaults.features)
    setTeamSize(persona.defaults.teamSize)
  }

  function handleUploads(v: Uploads) {
    setUploads(v)
    setActivePersona(null)
  }

  function handleFeatures(v: Features) {
    setFeatures(v)
    setActivePersona(null)
  }

  function handleTeamSize(v: TeamSize) {
    setTeamSize(v)
    setActivePersona(null)
  }

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-8 items-start">
      {/* Left column: Plan Estimator */}
      <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/40 p-6">
        <h3 className="font-serif text-base text-oatmeal-200 mb-6">Find Your Plan</h3>

        {/* Persona toggles */}
        <div className="flex flex-wrap gap-2 mb-6">
          {personas.map((persona) => (
            <button
              key={persona.key}
              type="button"
              onClick={() => selectPersona(persona)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl border font-sans text-sm transition-colors ${
                activePersona === persona.key
                  ? 'border-sage-500/50 bg-sage-500/15 text-sage-300'
                  : 'border-obsidian-500/30 bg-obsidian-800/50 text-oatmeal-400 hover:text-oatmeal-200 hover:border-obsidian-400/40'
              }`}
            >
              <PersonaIcon icon={persona.icon} className="w-4 h-4" />
              <span>{persona.label}</span>
            </button>
          ))}
        </div>

        {/* Input selectors */}
        <div className="space-y-5">
          <SegmentedSelector
            label="Monthly Uploads"
            options={uploadOptions}
            value={uploads}
            onChange={handleUploads}
          />
          <SegmentedSelector
            label="Features Needed"
            options={featureOptions}
            value={features}
            onChange={handleFeatures}
          />
          <SegmentedSelector
            label="Team Size"
            options={teamOptions}
            value={teamSize}
            onChange={handleTeamSize}
          />
        </div>

        {/* Recommendation line */}
        <div className="mt-6 pt-5 border-t border-obsidian-500/20">
          <AnimatePresence mode="wait">
            <motion.p
              key={recommendedTier}
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -4 }}
              transition={{ duration: 0.2, ease: 'easeOut' as const }}
              className="font-sans text-sm text-oatmeal-300"
            >
              Based on your needs, we recommend{' '}
              <span className="text-sage-400 font-semibold">{recommendedTier}</span>.
            </motion.p>
          </AnimatePresence>
        </div>
      </div>

      {/* Right column: Seat Calculator */}
      <div className="rounded-2xl border border-obsidian-500/30 bg-obsidian-800/40 p-6">
        <h3 className="font-serif text-base text-oatmeal-200 mb-2">Seat Calculator</h3>
        <p className="font-sans text-xs text-oatmeal-500 mb-6">
          {getSeatCalculatorDescription()}
        </p>
        <SeatCalculator interval={interval} />
      </div>
    </div>
  )
}
