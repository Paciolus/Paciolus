'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'
import { FeaturePillars, ProcessTimeline, ProductPreview, HeroProductFilm, GradientMesh, ToolShowcase, ProofStrip, BottomProof } from '@/components/marketing'
import { BrandIcon } from '@/components/shared'
import { SectionReveal } from '@/utils/marketingMotion'

/**
 * Platform Homepage (Sprint 66, redesigned Sprint 319-323, motion system Sprint 337)
 *
 * Marketing landing page showcasing the Paciolus suite of audit tools.
 * Features: cinematic hero, gradient mesh atmosphere, categorized tool grid,
 * interactive product preview, and social proof metrics.
 *
 * SectionReveal wrappers create directional continuity:
 * ProofStrip(up) → ToolShowcase(up) → FeaturePillars(left) →
 * ProcessTimeline(right) → ProductPreview(up) → BottomProof(left)
 */
export default function HomePage() {
  const { isAuthenticated } = useAuth()

  return (
    <main className="relative min-h-screen bg-gradient-obsidian">
      {/* Atmospheric gradient mesh background */}
      <GradientMesh />

      {/* Hero Section — Split Layout */}
      <section className="relative z-10 pt-28 pb-24 px-6 overflow-hidden">
        <div className="max-w-7xl mx-auto">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 lg:gap-8 items-center">
            {/* Left — Headline + CTAs */}
            <div className="text-center lg:text-left">
              <motion.div
                initial={{ opacity: 0, x: -30 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.7, ease: 'easeOut' as const }}
              >
                <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-500/15 border border-sage-500/30 mb-8">
                  <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
                  <span className="text-sage-300 text-sm font-sans font-medium">Professional Audit Intelligence</span>
                </div>
              </motion.div>

              <motion.h1
                className="font-serif text-5xl md:text-6xl lg:text-7xl text-oatmeal-100 mb-6 leading-[1.1]"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.15 }}
              >
                The Complete Audit
                <br />
                <span className="bg-gradient-to-r from-sage-400 via-sage-300 to-oatmeal-300 bg-clip-text text-transparent">Intelligence Suite</span>
              </motion.h1>

              <motion.p
                className="font-sans text-lg text-oatmeal-400 max-w-xl mx-auto lg:mx-0 mb-10 leading-relaxed"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.3 }}
              >
                Professional-grade diagnostic tools for financial professionals.
                Zero-Storage architecture ensures your client data is never saved.
                Twelve integrated tools. One diagnostic workspace.
              </motion.p>

              <motion.div
                className="flex items-center justify-center lg:justify-start gap-4"
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.7, delay: 0.45 }}
              >
                <Link
                  href="/tools/trial-balance"
                  className="group relative px-8 py-3.5 bg-sage-600 rounded-xl text-white font-sans font-medium hover:bg-sage-500 transition-all shadow-lg shadow-sage-600/25 hover:shadow-xl hover:shadow-sage-600/30"
                >
                  <span className="relative z-10">Explore Our Tools</span>
                </Link>
                {!isAuthenticated && (
                  <Link
                    href="/register"
                    className="px-8 py-3.5 bg-transparent border border-oatmeal-400/30 rounded-xl text-oatmeal-300 font-sans font-medium hover:border-oatmeal-400/50 hover:bg-oatmeal-200/5 transition-all"
                  >
                    Get Started Free
                  </Link>
                )}
              </motion.div>

              {/* Trust indicators */}
              <motion.div
                className="mt-12 flex items-center justify-center lg:justify-start gap-6"
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.7, delay: 0.7 }}
              >
                <div className="flex items-center gap-2 text-oatmeal-600">
                  <BrandIcon name="shield-check" className="w-4 h-4 text-sage-500" />
                  <span className="text-xs font-sans">ISA/PCAOB Standards</span>
                </div>
                <div className="w-px h-4 bg-obsidian-600" />
                <div className="flex items-center gap-2 text-oatmeal-600">
                  <BrandIcon name="padlock" className="w-4 h-4 text-sage-500" />
                  <span className="text-xs font-sans">Zero-Storage</span>
                </div>
                <div className="w-px h-4 bg-obsidian-600" />
                <div className="flex items-center gap-2 text-oatmeal-600">
                  <span className="text-xs font-sans font-mono">12 Tools</span>
                </div>
              </motion.div>
            </div>

            {/* Right — Product Film */}
            <motion.div
              className="relative"
              initial={{ opacity: 0, x: 30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.8, delay: 0.5 }}
            >
              <HeroProductFilm />
            </motion.div>
          </div>
        </div>
      </section>

      {/* Proof Strip — Credibility Band */}
      <SectionReveal className="relative z-10" direction="up">
        <ProofStrip />
      </SectionReveal>

      {/* Tool Showcase — Categorized Grid + Social Proof */}
      <SectionReveal className="lobby-surface-recessed relative z-10" direction="up">
        <ToolShowcase />
      </SectionReveal>

      {/* Section Divider */}
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <div className="lobby-divider" />
      </div>

      {/* Feature Pillars — accent surface + sage glow */}
      <SectionReveal className="lobby-surface-accent lobby-glow-sage relative z-10" direction="left">
        <FeaturePillars />
      </SectionReveal>

      {/* Section Divider */}
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <div className="lobby-divider" />
      </div>

      {/* Process Timeline — raised + vignette */}
      <SectionReveal className="lobby-surface-raised lobby-vignette relative z-10" direction="right">
        <ProcessTimeline />
      </SectionReveal>

      {/* Product Preview — recessed */}
      <SectionReveal className="lobby-surface-recessed relative z-10" direction="up">
        <ProductPreview />
      </SectionReveal>

      {/* Section Divider */}
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <div className="lobby-divider" />
      </div>

      {/* Bottom Proof — Testimonials + Closing CTA */}
      <SectionReveal className="lobby-surface-raised relative z-10" direction="left">
        <BottomProof />
      </SectionReveal>

    </main>
  )
}
