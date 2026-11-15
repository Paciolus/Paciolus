'use client'

import Image from 'next/image'
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
 * from synthetic data replaces it (Sprint 865): the screenshot is the live app
 * on a synthetic trial balance, and the figures below it are captioned as such.
 */
export function HeroScrollSection() {
  const { isAuthenticated } = useAuthSession()
  const mounted = useHasMounted()
  const { trackCtaClick } = useHeroTelemetry()
  const promo = getPromoCopy('monthly')

  return (
    <section className="relative z-10 pt-32 pb-16 px-6" aria-label="Introduction">
      <div className="max-w-6xl mx-auto grid lg:grid-cols-[minmax(0,1fr)_minmax(0,26rem)] gap-12 items-start">
      <motion.div
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
            className="group flex items-center gap-3 px-4 py-3 rounded-lg bg-obsidian-800/80 border border-sage-500/30 hover:border-sage-500/50 transition-colors"
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
              className="inline-block px-8 py-3.5 bg-sage-600 rounded-lg text-oatmeal-50 font-sans font-medium hover:bg-sage-500 transition-colors"
              onClick={() => trackCtaClick('start_trial')}
            >
              Start Free Trial
            </Link>
          )}
          <Link
            href="/demo"
            className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-lg text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-colors"
            onClick={() => trackCtaClick('explore_demo')}
          >
            Explore Demo
          </Link>
        </motion.div>
        <motion.p className="font-sans text-xs text-oatmeal-500 mt-3" variants={fadeUp}>
          Free plan needs no card. Paid trials ask for one; no charge for {TRIAL_DAYS} days.
        </motion.p>
      </motion.div>

      <figure className="lg:pt-4">
        <Image
          src="/screenshots/tb-flagged-accounts.png"
          alt="Trial Balance Diagnostics results: a $500 materiality threshold and two flagged accounts, a receivable with a credit balance and an unreconciled suspense balance."
          width={722}
          height={564}
          priority
          className="w-full h-auto rounded-lg border border-obsidian-500/60"
        />
        <figcaption className="mt-3 font-sans text-xs text-oatmeal-500">
          Trial Balance Diagnostics on a synthetic trial balance: two accounts flagged for review.
        </figcaption>
      </figure>
      </div>

      <div className="max-w-6xl mx-auto mt-20 grid md:grid-cols-2 gap-10">
        <figure>
          <Image
            src="/screenshots/tb-upload-columns.png"
            alt="Data readiness score of 95 and column detection matching the Account, Debit and Credit columns."
            width={845}
            height={395}
            className="w-full h-auto rounded-lg border border-obsidian-500/60"
          />
          <figcaption className="mt-3 font-sans text-xs text-oatmeal-500">
            <span className="font-mono text-sage-400 mr-2">Fig. 1</span>
            Before analysis: a data-readiness check and column detection on the uploaded file.
          </figcaption>
        </figure>
        <figure>
          <Image
            src="/screenshots/je-memo-proof-summary.png"
            alt="Page 2 of a Journal Entry Testing memo: scope, proof summary and the tests applied."
            width={980}
            height={1268}
            className="w-full h-auto max-h-[28rem] object-cover object-top rounded-lg border border-obsidian-500/60"
          />
          <figcaption className="mt-3 font-sans text-xs text-oatmeal-500">
            <span className="font-mono text-sage-400 mr-2">Fig. 2</span>
            A Journal Entry Testing memo in its default layout (sign-off lines are optional, completed by the firm). Synthetic data.{' '}
            <a href="/samples/paciolus-sample-je-testing-memo.pdf" className="text-sage-400 hover:text-sage-300 underline">
              Download the sample memo (PDF)
            </a>
          </figcaption>
        </figure>
      </div>
    </section>
  )
}
