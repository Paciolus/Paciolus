'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { FeaturePillars, ProcessTimeline, HeroScrollSection, ToolSlideshow, BottomProof, EvidenceBand } from '@/components/marketing'
import { ParallaxSection } from '@/utils/marketingMotion'

/**
 * Platform Homepage (Sprint 66, redesigned Sprint 319-323, slideshow + scrubber Sprint 449)
 * Sprint 475: Auth-aware redirect — logged-in users go to /dashboard.
 *
 * Marketing landing page showcasing the Paciolus suite of audit tools.
 * Features: interactive hero with timeline scrubber, animated tool slideshow
 * with rich mock previews, credential evidence band, and closing proof section.
 *
 * Sections manage their own scroll-reveal internally — no outer Reveal
 * wrappers here to avoid compounding entrance delays.
 */
export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuthSession()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isLoading, isAuthenticated, router])
  return (
    <main id="main-content" className="relative min-h-screen bg-obsidian-800">
      {/* Hero Section — Scroll-Linked Product Film */}
      <HeroScrollSection />

      {/* Tool Slideshow — Animated slideshow with rich previews + modern city atmosphere */}
      <div className="lobby-surface-recessed lobby-atmosphere-modern relative z-10">
        <ToolSlideshow />
      </div>

      {/* Section Divider */}
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <div className="lobby-divider" />
      </div>

      {/* Feature Pillars — accent surface + sage glow + parallax */}
      <ParallaxSection className="lobby-surface-accent lobby-glow-sage relative z-10" speed={0.06}>
        <FeaturePillars />
      </ParallaxSection>

      {/* Section Divider — sage accent between pillars and timeline */}
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <div className="lobby-divider-sage" />
      </div>

      {/* Process Timeline — raised + vignette */}
      <div className="lobby-surface-raised lobby-vignette relative z-10">
        <ProcessTimeline />
      </div>

      {/* Evidence Band — platform credentials + parallax */}
      <ParallaxSection className="lobby-surface-recessed relative z-10" speed={0.05}>
        <EvidenceBand />
      </ParallaxSection>

      {/* Section Divider — wide before closing proof */}
      <div className="relative z-10 max-w-5xl mx-auto px-6">
        <div className="lobby-divider-wide" />
      </div>

      {/* Bottom Proof — Standards + Closing CTA */}
      <div className="lobby-surface-raised relative z-10">
        <BottomProof />
      </div>

    </main>
  )
}
