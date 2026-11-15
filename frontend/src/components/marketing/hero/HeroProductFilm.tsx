'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { STORAGE_DETAIL_HREF, STORAGE_DETAIL_LABEL, STORAGE_STATEMENT } from '@/content/storage-statement'
import { TRIAL_DAYS, getPromoCopy } from '@/domain/pricing'
import { staggerContainer, fadeUp } from '@/lib/motion'
import { useHasMounted, useHeroTelemetry } from './useHeroTelemetry'

/**
 * Homepage hero — Sprint 861.
 *
 * The animated "product film" (cursor, scanning tool grid, download bar) was
 * removed: it showed "3 findings", "17 PDF Memos" and a partial tool grid with
 * struck-out tools, none of which matched the product (CEO decision
 * 2026-11-14 — a claim we cannot prove is removed). A real screenshot made
 * from synthetic data replaces it in Sprint 865; until then the hero is text.
 */
export function HeroScrollSection() {
  const { isAuthenticated } = useAuthSession()
  const mounted = useHasMounted()
  const { trackCtaClick } = useHeroTelemetry()
  const promo = getPromoCopy('monthly')

  return (
    <section className="relative z-10 pt-32 pb-16 px-6" aria-label="Introduction">
      <motion.div
        className="max-w-4xl mx-auto"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <motion.h1 className="type-display-xl text-oatmeal-100 mb-6" variants={fadeUp}>
          Trial balance and ledger testing{' '}
          <span className="text-sage-300">for audit teams.</span>
        </motion.h1>

        <motion.p className="font-sans text-lg text-oatmeal-300 max-w-2xl mb-4" variants={fadeUp}>
          Upload a file. Paciolus runs the tests, flags items for you to review, and produces PDF memos and Excel
          workpapers. The conclusions are yours.
        </motion.p>

        <motion.p className="font-sans text-sm text-oatmeal-400 max-w-2xl mb-8" variants={fadeUp}>
          {STORAGE_STATEMENT}{' '}
          <Link href={STORAGE_DETAIL_HREF} className="text-sage-400 hover:text-sage-300 underline">
            {STORAGE_DETAIL_LABEL}
          </Link>
        </motion.p>

        <motion.div className="mb-8 max-w-lg" variants={fadeUp}>
          <Link
            href="/pricing"
            className="group flex items-center gap-3 px-4 py-3 rounded-xl bg-obsidian-800/80 border border-sage-500/30 hover:border-sage-500/50 transition-colors"
          >
            <div className="w-0.5 h-8 bg-sage-500 rounded-full flex-shrink-0" />
            <div className="flex-1 min-w-0">
              <p className="font-sans text-sm text-oatmeal-200">
                {promo.prefix} <span className="text-sage-400 font-medium">{promo.body}</span>
              </p>
              <p className="font-sans text-xs text-oatmeal-500 group-hover:text-oatmeal-400 transition-colors">
                See Pricing &rarr;
              </p>
            </div>
          </Link>
        </motion.div>

        <motion.div className="flex items-center gap-4" variants={fadeUp}>
          {mounted && !isAuthenticated && (
            <Link
              href="/register"
              className="inline-block px-8 py-3.5 bg-sage-600 rounded-xl text-oatmeal-50 font-sans font-medium hover:bg-sage-500 transition-colors"
              onClick={() => trackCtaClick('start_trial')}
            >
              Start Free Trial
            </Link>
          )}
          <Link
            href="/demo"
            className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-colors"
            onClick={() => trackCtaClick('explore_demo')}
          >
            Explore Demo
          </Link>
        </motion.div>
        <motion.p className="font-sans text-xs text-oatmeal-500 mt-3" variants={fadeUp}>
          Free plan needs no card. Paid trials ask for one; no charge for {TRIAL_DAYS} days.
        </motion.p>
      </motion.div>
    </section>
  )
}
