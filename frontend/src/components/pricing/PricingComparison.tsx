// Feature comparison table/grid for all pricing tiers.
'use client'

import { motion } from 'framer-motion'
import { type CellValue, comparisonRows } from '@/domain/pricing'

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' as const },
  },
} as const

/* ────────────────────────────────────────────────
   Cell renderer
   ──────────────────────────────────────────────── */

function CellContent({ value }: { value: CellValue }) {
  if (value === true) {
    return (
      <svg className="w-5 h-5 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-label="Included">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
      </svg>
    )
  }
  if (value === false) {
    return <span className="text-oatmeal-600 font-sans text-sm">&mdash;</span>
  }
  return <span className="font-sans text-sm text-oatmeal-300">{value}</span>
}

/* ────────────────────────────────────────────────
   Comparison table
   ──────────────────────────────────────────────── */

export default function PricingComparison() {
  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
    >
      <h2 className="type-headline-sm text-sage-300 text-center mb-10">
        Feature Comparison
      </h2>

      <div
        className="relative overflow-x-auto rounded-2xl border border-sage-500/20 [mask-image:linear-gradient(to_right,transparent,black_16px,black_calc(100%-16px),transparent)] md:[mask-image:none]"
        aria-describedby="pricing-comparison-scroll-hint"
      >
        <span id="pricing-comparison-scroll-hint" className="sr-only">
          Scroll horizontally to reveal the full comparison table on narrow viewports.
        </span>
        <table className="w-full text-left min-w-[700px]">
          <caption className="sr-only">Feature comparison across Free, Solo, Professional, and Enterprise tiers</caption>
          <thead>
            <tr className="border-b border-obsidian-500/30">
              <th scope="col" className="font-serif text-sm text-oatmeal-400 py-4 px-5 w-[20%]">Feature</th>
              <th scope="col" className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[20%]">Free</th>
              <th scope="col" className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[20%]">Solo</th>
              <th scope="col" className="font-serif text-xs text-sage-400 py-4 px-3 text-center w-[20%]">Professional</th>
              <th scope="col" className="font-serif text-xs text-oatmeal-400 py-4 px-3 text-center w-[20%]">Enterprise</th>
            </tr>
          </thead>
          <tbody>
            {comparisonRows.map((row, idx) => (
              <tr
                key={row.feature}
                className={`border-b border-obsidian-500/20 last:border-b-0 ${
                  idx % 2 === 0 ? 'bg-obsidian-800/60' : 'bg-obsidian-800/30'
                }`}
              >
                <th scope="row" className="font-sans text-sm text-oatmeal-300 py-3 px-5 font-normal">{row.feature}</th>
                <td className="py-3 px-3 text-center"><CellContent value={row.free} /></td>
                <td className="py-3 px-3 text-center"><CellContent value={row.solo} /></td>
                <td className="py-3 px-3 text-center"><CellContent value={row.professional} /></td>
                <td className="py-3 px-3 text-center"><CellContent value={row.enterprise} /></td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </motion.div>
  )
}
