'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { STAGGER, ENTER, VIEWPORT, CountUp } from '@/utils/marketingMotion'

/**
 * BottomProof — Sprint 334, motion migrated Sprint 337
 *
 * Closing argument section: social validation via testimonials,
 * reinforced by quantitative metrics, with an auth-aware CTA
 * that catches users who scrolled past the hero.
 *
 * Placed after ProductPreview, before footer.
 */

interface Testimonial {
  quote: string
  role: string
  context: string
  accent: string
}

interface ClosingMetric {
  target: number
  suffix: string
  label: string
}

const TESTIMONIALS: Testimonial[] = [
  {
    quote: 'What used to take our team half a day now runs in seconds. The anomaly detection catches things we would have missed in manual review.',
    role: 'Senior Auditor, Mid-Tier CPA Firm',
    context: 'Trial Balance Diagnostics',
    accent: 'border-l-sage-500/40',
  },
  {
    quote: 'Zero-Storage was non-negotiable for us. Knowing that client data is never persisted gives our compliance team complete peace of mind.',
    role: 'Internal Audit Manager, Manufacturing',
    context: 'Data Security',
    accent: 'border-l-oatmeal-400/40',
  },
  {
    quote: 'The PDF memos are presentation-ready. We attach them directly to workpapers without reformatting a single line.',
    role: 'Financial Controller, Professional Services',
    context: 'Export & Documentation',
    accent: 'border-l-clay-500/40',
  },
]

const CLOSING_METRICS: ClosingMetric[] = [
  { target: 3780, suffix: '+', label: 'Backend Tests' },
  { target: 24, suffix: '', label: 'Export Endpoints' },
  { target: 11, suffix: '', label: 'PDF Memos' },
]

export function BottomProof() {
  const { isAuthenticated } = useAuth()

  return (
    <section className="py-24 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Section heading */}
        <motion.div
          className="text-center"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5 }}
        >
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-100">
            Ready to Transform Your Diagnostic Workflow?
          </h2>
          <p className="font-sans text-oatmeal-400 mt-3 max-w-xl mx-auto">
            Join financial professionals who have already streamlined their diagnostic process.
          </p>
        </motion.div>

        {/* Testimonial grid */}
        <motion.div
          className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12"
          variants={STAGGER.fast}
          initial="hidden"
          whileInView="visible"
          viewport={VIEWPORT.eager}
        >
          {TESTIMONIALS.map((testimonial) => (
            <motion.div
              key={testimonial.role}
              variants={ENTER.fadeUp}
              className={`border-l-4 ${testimonial.accent} bg-obsidian-800/50 border border-obsidian-500/20 rounded-xl p-6`}
            >
              <p className="font-sans text-sm italic text-oatmeal-300 leading-relaxed">
                &ldquo;{testimonial.quote}&rdquo;
              </p>
              <div className="mt-4">
                <p className="font-sans text-sm font-medium text-oatmeal-200">{testimonial.role}</p>
                <p className="font-sans text-xs text-oatmeal-500 mt-0.5">{testimonial.context}</p>
              </div>
            </motion.div>
          ))}
        </motion.div>

        {/* Closing metric band */}
        <motion.div
          className="grid grid-cols-3 gap-6 mt-12"
          initial={{ opacity: 0, y: 20 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5, delay: 0.1 }}
        >
          {CLOSING_METRICS.map((metric) => (
            <div
              key={metric.label}
              className="text-center bg-obsidian-800/40 border border-obsidian-500/20 rounded-xl p-5"
            >
              <p className="font-mono text-2xl font-bold text-oatmeal-200">
                <CountUp target={metric.target} suffix={metric.suffix} />
              </p>
              <p className="font-sans text-sm text-oatmeal-400 mt-1">{metric.label}</p>
            </div>
          ))}
        </motion.div>

        {/* CTA row */}
        <motion.div
          className="flex items-center justify-center gap-4 mt-12"
          initial={{ opacity: 0, y: 15 }}
          whileInView={{ opacity: 1, y: 0 }}
          viewport={VIEWPORT.default}
          transition={{ duration: 0.5, delay: 0.3 }}
        >
          {!isAuthenticated && (
            <Link
              href="/register"
              className="px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
            >
              Start Free
            </Link>
          )}
          <Link
            href="/tools/trial-balance"
            className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
          >
            Explore Tools
          </Link>
        </motion.div>
      </div>
    </section>
  )
}
