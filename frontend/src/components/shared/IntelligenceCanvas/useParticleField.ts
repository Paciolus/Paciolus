/**
 * useParticleField — imperative rAF animation loop hook
 *
 * Runs the particle flow field entirely outside React's render cycle.
 * Only variant/accentState prop changes update config refs;
 * the animation loop reads them on the next tick.
 *
 * Fully paused under prefers-reduced-motion.
 */

import { useRef, useEffect, useCallback } from 'react'
import {
  VARIANT_CONFIGS,
  ACCENT_CONFIGS,
  flowAngle,
  randomInRange,
  getParticleCount,
} from './canvasConfig'
import type { Particle, CanvasVariant, AccentState } from './types'

interface UseParticleFieldOptions {
  variant: CanvasVariant
  accentState: AccentState
}

export function useParticleField(
  canvasRef: React.RefObject<HTMLCanvasElement | null>,
  { variant, accentState }: UseParticleFieldOptions
) {
  const particlesRef = useRef<Particle[]>([])
  const animFrameRef = useRef<number>(0)
  const timeRef = useRef(0)
  const variantRef = useRef(variant)
  const accentRef = useRef(accentState)

  // Update refs when props change (no re-render, loop reads on next tick)
  useEffect(() => {
    variantRef.current = variant
  }, [variant])

  useEffect(() => {
    accentRef.current = accentState
  }, [accentState])

  const initParticles = useCallback((width: number, height: number) => {
    const config = VARIANT_CONFIGS[variantRef.current]
    const count = getParticleCount(config)
    const particles: Particle[] = []

    for (let i = 0; i < count; i++) {
      const baseOpacity = randomInRange(
        config.particle.opacityRange[0],
        config.particle.opacityRange[1]
      )
      particles.push({
        x: Math.random() * width,
        y: Math.random() * height,
        size: randomInRange(config.particle.sizeRange[0], config.particle.sizeRange[1]),
        opacity: baseOpacity,
        baseOpacity,
        speed: randomInRange(config.particle.speedRange[0], config.particle.speedRange[1]),
        life: Math.random() * Math.PI * 2, // random phase offset
      })
    }

    particlesRef.current = particles
  }, [])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    // Respect prefers-reduced-motion
    const motionQuery = window.matchMedia('(prefers-reduced-motion: reduce)')
    if (motionQuery.matches) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    // Handle resize
    const resizeCanvas = () => {
      const dpr = window.devicePixelRatio || 1
      const rect = canvas.getBoundingClientRect()
      canvas.width = rect.width * dpr
      canvas.height = rect.height * dpr
      ctx.scale(dpr, dpr)
      initParticles(rect.width, rect.height)
    }

    resizeCanvas()
    window.addEventListener('resize', resizeCanvas)

    // Animation loop
    const animate = () => {
      const config = VARIANT_CONFIGS[variantRef.current]
      const accent = ACCENT_CONFIGS[accentRef.current]
      const { width, height } = canvas.getBoundingClientRect()

      // Clear with trail or full clear
      if (config.particle.trailAlpha < 1) {
        ctx.fillStyle = `rgba(13, 13, 13, ${1 - config.particle.trailAlpha})`
        ctx.fillRect(0, 0, width, height)
      } else {
        ctx.clearRect(0, 0, width, height)
      }

      timeRef.current += 0.016 // ~60fps frame time

      const particles = particlesRef.current
      for (const p of particles) {
        // Flow field direction
        const angle = flowAngle(p.x, p.y, timeRef.current)
        const speedMod = p.speed * accent.speedMultiplier

        p.x += Math.cos(angle) * speedMod
        p.y += Math.sin(angle) * speedMod
        p.life += 0.02

        // Gentle opacity breathing
        p.opacity = p.baseOpacity * (0.7 + 0.3 * Math.sin(p.life))

        // Edge wrapping
        if (p.x < -10) p.x = width + 10
        if (p.x > width + 10) p.x = -10
        if (p.y < -10) p.y = height + 10
        if (p.y > height + 10) p.y = -10

        // Draw particle
        ctx.beginPath()
        ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(${config.particle.color}, ${p.opacity})`
        ctx.fill()
      }

      animFrameRef.current = requestAnimationFrame(animate)
    }

    animFrameRef.current = requestAnimationFrame(animate)

    // Handle motion preference change
    const handleMotionChange = (e: MediaQueryListEvent) => {
      if (e.matches) {
        cancelAnimationFrame(animFrameRef.current)
        ctx.clearRect(0, 0, canvas.width, canvas.height)
      } else {
        resizeCanvas()
        animFrameRef.current = requestAnimationFrame(animate)
      }
    }
    motionQuery.addEventListener('change', handleMotionChange)

    return () => {
      cancelAnimationFrame(animFrameRef.current)
      window.removeEventListener('resize', resizeCanvas)
      motionQuery.removeEventListener('change', handleMotionChange)
    }
  }, [canvasRef, initParticles])
}
