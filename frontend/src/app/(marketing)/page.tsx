'use client'

import { FeaturePillars, ProcessTimeline, ProductPreview, HeroScrollSection, ToolShowcase, ProofStrip, BottomProof } from '@/components/marketing'
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
  return (
    <main className="relative min-h-screen bg-obsidian-800">
      {/* Hero Section — Scroll-Linked Product Film */}
      <HeroScrollSection />

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
