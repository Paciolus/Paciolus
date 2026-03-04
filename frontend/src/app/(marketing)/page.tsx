'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { FeaturePillars, ProcessTimeline, HeroScrollSection, ToolSlideshow, BottomProof, EvidenceBand } from '@/components/marketing'
import { Reveal } from '@/components/ui/Reveal'
import { ParallaxSection } from '@/utils/marketingMotion'

/**
 * Platform Homepage (Sprint 66, redesigned Sprint 319-323, slideshow + scrubber Sprint 449)
 * Sprint 475: Auth-aware redirect — logged-in users go to /dashboard.
 *
 * Marketing landing page showcasing the Paciolus suite of audit tools.
 * Features: interactive hero with timeline scrubber, animated tool slideshow
 * with rich mock previews, credential evidence band, and closing proof section.
 *
 * Uniform vertical fadeUp entrances (Linear-style precision).
 */
export default function HomePage() {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.push('/dashboard')
    }
  }, [isLoading, isAuthenticated, router])
  return (
    <main className="relative min-h-screen bg-obsidian-800">
      {/* Hero Section — Scroll-Linked Product Film */}
      <HeroScrollSection />

      {/* Tool Slideshow — Animated slideshow with rich previews + modern city atmosphere */}
      <Reveal className="lobby-surface-recessed lobby-atmosphere-modern relative z-10">
        <ToolSlideshow />
      </Reveal>

      {/* Section Divider */}
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <div className="lobby-divider" />
      </div>

      {/* Feature Pillars — accent surface + sage glow + heritage atmosphere + parallax */}
      <ParallaxSection className="lobby-surface-accent lobby-glow-sage lobby-atmosphere-heritage relative z-10" speed={0.06}>
        <Reveal>
          <FeaturePillars />
        </Reveal>
      </ParallaxSection>

      {/* Section Divider — sage accent between pillars and timeline */}
      <div className="relative z-10 max-w-4xl mx-auto px-6">
        <div className="lobby-divider-sage" />
      </div>

      {/* Process Timeline — raised + vignette */}
      <Reveal className="lobby-surface-raised lobby-vignette relative z-10">
        <ProcessTimeline />
      </Reveal>

      {/* Evidence Band — platform credentials + parallax */}
      <ParallaxSection className="lobby-surface-recessed relative z-10" speed={0.05}>
        <Reveal>
          <EvidenceBand />
        </Reveal>
      </ParallaxSection>

      {/* Section Divider — wide before closing proof */}
      <div className="relative z-10 max-w-5xl mx-auto px-6">
        <div className="lobby-divider-wide" />
      </div>

      {/* Bottom Proof — Standards + Closing CTA */}
      <Reveal className="lobby-surface-raised relative z-10">
        <BottomProof />
      </Reveal>

    </main>
  )
}
