/**
 * BrandIcon — Sprint 384
 *
 * Shared icon component for the Paciolus design system.
 * Renders stroke-based SVG icons with optional size tokens, tone colors, and motion states.
 *
 * Backward compatible: omitting size/state/tone produces identical output to Sprint 333.
 */

import { motion, MotionConfig } from 'framer-motion'
import type { BrandIconProps, IconDefinition, IconSize, IconTone, SvgElement } from './types'
import { ICON_REGISTRY } from './iconRegistry'
import { iconStateVariants } from './stateVariants'

/** Size token → pixel dimension */
const SIZE_PX: Record<IconSize, number> = {
  xs: 14,
  sm: 16,
  md: 24,
  lg: 32,
  xl: 48,
}

/** Tone → CSS color value (uses theme custom properties for theme-awareness) */
const TONE_COLORS: Record<IconTone, string> = {
  default: 'currentColor',
  sage: 'var(--sage-400, #8FBF9F)',
  clay: 'var(--clay-400, #D4686A)',
  oatmeal: 'var(--oatmeal-400, #C5C1B8)',
  muted: 'var(--oatmeal-600, #8A8780)',
}

/** Render SVG children from an IconDefinition */
function renderElements(definition: IconDefinition, strokeWidth: number): React.ReactNode {
  if (typeof definition === 'string') {
    return (
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={strokeWidth}
        d={definition}
      />
    )
  }

  return definition.map((el: SvgElement, i: number) => {
    const { tag: Tag, attrs } = el
    const props = {
      ...attrs,
      strokeLinecap: (attrs.strokeLinecap as string) || 'round',
      strokeLinejoin: (attrs.strokeLinejoin as string) || 'round',
      strokeWidth: attrs.strokeWidth ?? strokeWidth,
      key: i,
    }
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return <Tag {...(props as any)} />
  })
}

export function BrandIcon({
  name,
  size,
  state,
  tone,
  className = 'w-6 h-6',
  label,
}: BrandIconProps) {
  const definition = ICON_REGISTRY[name]
  if (!definition) return null

  const strokeWidth = 1.5

  // Accessibility
  const a11yProps = label
    ? { 'aria-label': label, role: 'img' as const }
    : { 'aria-hidden': true as const }

  // Size: named token overrides className sizing
  const sizeStyle = size
    ? { width: SIZE_PX[size], height: SIZE_PX[size] }
    : undefined

  // Tone: explicit color overrides currentColor inheritance
  const stroke = tone ? TONE_COLORS[tone] : 'currentColor'

  // When state is provided, render as motion.svg with variants
  if (state) {
    return (
      <MotionConfig reducedMotion="user">
        <motion.svg
          viewBox="0 0 24 24"
          fill="none"
          stroke={stroke}
          className={size ? undefined : className}
          style={sizeStyle}
          variants={iconStateVariants}
          animate={state}
          {...a11yProps}
        >
          {renderElements(definition, strokeWidth)}
        </motion.svg>
      </MotionConfig>
    )
  }

  // Static SVG — zero motion overhead
  return (
    <svg
      viewBox="0 0 24 24"
      fill="none"
      stroke={stroke}
      className={size ? undefined : className}
      style={sizeStyle}
      {...a11yProps}
    >
      {renderElements(definition, strokeWidth)}
    </svg>
  )
}
