'use client'

import { FeaturePillars, ProcessTimeline, HeroScrollSection, ToolSlideshow, BottomProof, EvidenceBand } from '@/components/marketing'
import { SectionReveal, ParallaxSection } from '@/utils/marketingMotion'

/**
 * Platform Homepage (Sprint 66, redesigned Sprint 319-323, slideshow + scrubber Sprint 449)
 *
 * Marketing landing page showcasing the Paciolus suite of audit tools.
 * Features: interactive hero with timeline scrubber, animated tool slideshow
 * with rich mock previews, credential evidence band, and closing proof section.
 *
 * SectionReveal wrappers create directional continuity:
 * ToolSlideshow(up) → FeaturePillars(left) →
 * ProcessTimeline(right) → EvidenceBand(up) → BottomProof(left)
 */
export default function HomePage() {
  return (
    <main className="relative min-h-screen bg-obsidian-800">
      {/* Hero Section — Scroll-Linked Product Film */}
      <HeroScrollSection />

      {/* Tool Slideshow — Animated slideshow with rich previews */}
      <SectionReveal className="lobby-surface-recessed relative z-10" direction="up">
        <ToolSlideshow />
      </SectionReveal>

      {/* Section Divider */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6">
        <div className="lobby-divider" />
      </div>

      {/* Feature Pillars — accent surface + sage glow + parallax */}
      <ParallaxSection className="lobby-surface-accent lobby-glow-sage relative z-10" speed={0.06}>
        <SectionReveal direction="left">
          <FeaturePillars />
        </SectionReveal>
      </ParallaxSection>

      {/* Section Divider — sage accent between pillars and timeline */}
      <div className="relative z-10 max-w-4xl mx-auto px-4 sm:px-6">
        <div className="lobby-divider-sage" />
      </div>

      {/* Process Timeline — raised + vignette */}
      <SectionReveal className="lobby-surface-raised lobby-vignette relative z-10" direction="right">
        <ProcessTimeline />
      </SectionReveal>

      {/* Evidence Band — platform credentials + parallax */}
      <ParallaxSection className="lobby-surface-recessed relative z-10" speed={0.05}>
        <SectionReveal direction="up">
          <EvidenceBand />
        </SectionReveal>
      </ParallaxSection>

      {/* Section Divider — wide before closing proof */}
      <div className="relative z-10 max-w-5xl mx-auto px-4 sm:px-6">
        <div className="lobby-divider-wide" />
      </div>

      {/* Bottom Proof — Standards + Closing CTA */}
      <SectionReveal className="lobby-surface-raised relative z-10" direction="left">
        <BottomProof />
      </SectionReveal>

    </main>
  )
}
