'use client'

/**
 * MechanicalGauge — Sprint 707 demo signature moment.
 *
 * Replaces the flat circle-dial Composite Diagnostic Score with a proper
 * arc-style mechanical gauge: 180° sweep, hairline tick marks every 10
 * units, serif numeral readout at centre, a needle that eases to the
 * score value on mount.
 *
 * Usage:
 *   <MechanicalGauge score={76} riskLevel="low" />
 *
 * `prefers-reduced-motion: reduce` skips the needle animation and
 * renders the final angle immediately.
 *
 * Demo-surface-only: this component lives under `components/demo/` and
 * must not leak into real product views (Sprint 707 isolation rule).
 */

import { useEffect, useState } from 'react'

type RiskLevel = 'low' | 'moderate' | 'elevated' | 'high'

interface MechanicalGaugeProps {
  /** 0-100 composite score. Clamped. */
  score: number
  /** Risk classification — sets the needle colour. */
  riskLevel: RiskLevel
  /** Override the default size (width + height) in pixels. */
  size?: number
}

const RISK_COLOR: Record<RiskLevel, string> = {
  low: '#4A7C59', // sage-600
  moderate: '#8a7446', // warm oatmeal-brass
  elevated: '#B08D57', // brass
  high: '#BC4749', // clay-500
}

const RISK_LABEL: Record<RiskLevel, string> = {
  low: 'Low Risk',
  moderate: 'Moderate',
  elevated: 'Elevated',
  high: 'High Risk',
}

export function MechanicalGauge({ score, riskLevel, size = 180 }: MechanicalGaugeProps) {
  const clamped = Math.max(0, Math.min(100, score))
  const targetAngle = -90 + (clamped / 100) * 180 // -90° at 0, +90° at 100
  const prefersReduced = usePrefersReducedMotion()

  const [angle, setAngle] = useState(prefersReduced ? targetAngle : -90)

  useEffect(() => {
    if (prefersReduced) {
      setAngle(targetAngle)
      return
    }
    // Ease the needle from 0 (-90°) to targetAngle over ~1.1s.
    const start = performance.now()
    const durationMs = 1100
    let frame = 0
    const step = (now: number) => {
      const t = Math.min(1, (now - start) / durationMs)
      // easeOutCubic — reads as decisive-and-settling rather than overshooting
      const eased = 1 - Math.pow(1 - t, 3)
      setAngle(-90 + eased * (targetAngle + 90))
      if (t < 1) frame = requestAnimationFrame(step)
    }
    frame = requestAnimationFrame(step)
    return () => cancelAnimationFrame(frame)
  }, [targetAngle, prefersReduced])

  const cx = 100
  const cy = 100
  const arcRadius = 82
  const needleLength = 72
  const needleColor = RISK_COLOR[riskLevel]

  // Tick marks every 10 units (0 → 100, so 11 ticks).
  const ticks = Array.from({ length: 11 }, (_, i) => {
    const frac = i / 10
    const tAngleRad = (-90 + frac * 180) * (Math.PI / 180)
    const outer = arcRadius + 2
    const inner = arcRadius - (i % 5 === 0 ? 8 : 4) // major tick every 50 units
    return {
      x1: cx + outer * Math.cos(tAngleRad),
      y1: cy + outer * Math.sin(tAngleRad),
      x2: cx + inner * Math.cos(tAngleRad),
      y2: cy + inner * Math.sin(tAngleRad),
      major: i % 5 === 0,
      label: i % 5 === 0 ? `${i * 10}` : null,
      labelX: cx + (arcRadius - 18) * Math.cos(tAngleRad),
      labelY: cy + (arcRadius - 18) * Math.sin(tAngleRad),
    }
  })

  const needleAngleRad = angle * (Math.PI / 180)
  const needleTipX = cx + needleLength * Math.cos(needleAngleRad)
  const needleTipY = cy + needleLength * Math.sin(needleAngleRad)

  return (
    <figure
      className="inline-flex flex-col items-center"
      aria-label={`Composite diagnostic score ${clamped} out of 100, ${RISK_LABEL[riskLevel]}`}
    >
      <svg
        width={size}
        height={size * 0.62}
        viewBox="0 0 200 130"
        role="img"
        aria-hidden="true"
      >
        {/* Background arc */}
        <path
          d={describeArc(cx, cy, arcRadius, -90, 90)}
          fill="none"
          stroke="rgba(235,233,228,0.12)"
          strokeWidth="2"
          strokeLinecap="round"
        />
        {/* Tick marks */}
        {ticks.map((t, i) => (
          <line
            key={`tick-${i}`}
            x1={t.x1}
            y1={t.y1}
            x2={t.x2}
            y2={t.y2}
            stroke="rgba(235,233,228,0.28)"
            strokeWidth={t.major ? 1.25 : 0.75}
            strokeLinecap="round"
          />
        ))}
        {/* Tick labels (major only) */}
        {ticks.map((t, i) =>
          t.label ? (
            <text
              key={`label-${i}`}
              x={t.labelX}
              y={t.labelY}
              fontFamily="Merriweather, serif"
              fontSize="9"
              fill="rgba(235,233,228,0.44)"
              textAnchor="middle"
              dominantBaseline="middle"
              style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
            >
              {t.label}
            </text>
          ) : null,
        )}
        {/* Needle pivot */}
        <circle cx={cx} cy={cy} r={4} fill={needleColor} />
        {/* Needle */}
        <line
          x1={cx}
          y1={cy}
          x2={needleTipX}
          y2={needleTipY}
          stroke={needleColor}
          strokeWidth="2.5"
          strokeLinecap="round"
        />
        {/* Centre readout */}
        <text
          x={cx}
          y={cy - 22}
          textAnchor="middle"
          fontFamily="Merriweather, serif"
          fontWeight="700"
          fontSize="26"
          fill="#EBE9E4"
          style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
        >
          {Math.round(clamped)}
        </text>
      </svg>
      <figcaption className="mt-1 text-center">
        <span
          className="font-sans text-[10px] uppercase tracking-[0.16em]"
          style={{ color: needleColor }}
        >
          {RISK_LABEL[riskLevel]}
        </span>
      </figcaption>
    </figure>
  )
}

/* ─── SVG arc helper ───────────────────────────────────────────── */

function describeArc(cx: number, cy: number, r: number, startDeg: number, endDeg: number): string {
  const toRad = (d: number) => d * (Math.PI / 180)
  const start = { x: cx + r * Math.cos(toRad(startDeg)), y: cy + r * Math.sin(toRad(startDeg)) }
  const end = { x: cx + r * Math.cos(toRad(endDeg)), y: cy + r * Math.sin(toRad(endDeg)) }
  const large = endDeg - startDeg <= 180 ? 0 : 1
  return `M ${start.x} ${start.y} A ${r} ${r} 0 ${large} 1 ${end.x} ${end.y}`
}

/* ─── Hook: prefers-reduced-motion ─────────────────────────────── */

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(false)
  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)')
    setReduced(mq.matches)
    const handler = (e: MediaQueryListEvent) => setReduced(e.matches)
    mq.addEventListener('change', handler)
    return () => mq.removeEventListener('change', handler)
  }, [])
  return reduced
}
