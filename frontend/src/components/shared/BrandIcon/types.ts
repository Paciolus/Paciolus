/**
 * BrandIcon Type Definitions — Sprint 384
 *
 * Shared types for the icon registry, renderer, and consumers.
 */

/** All available icon names — legacy 21 + 6 bespoke additions */
export type BrandIconName =
  | 'bar-chart'
  | 'warning-triangle'
  | 'circle-check'
  | 'clipboard-check'
  | 'calculator'
  | 'trend-chart'
  | 'shield-check'
  | 'currency-circle'
  | 'users'
  | 'document-duplicate'
  | 'arrows-vertical'
  | 'clock'
  | 'building'
  | 'cube'
  | 'archive'
  | 'chevron-right'
  | 'padlock'
  | 'sliders'
  | 'document'
  | 'cloud-upload'
  | 'file-download'
  // Bespoke additions (Sprint 384)
  | 'chevron-down'
  | 'checkmark'
  | 'x-mark'
  | 'file-plus'
  | 'document-blank'
  | 'spreadsheet'
  | 'download-arrow'

/** Named size tokens → pixel values */
export type IconSize = 'xs' | 'sm' | 'md' | 'lg' | 'xl'

/** Tone mapping for stroke color */
export type IconTone = 'default' | 'sage' | 'clay' | 'oatmeal' | 'muted'

/** Motion state for animated icons */
export type IconState = 'idle' | 'hover' | 'active' | 'complete'

/** A single SVG element within a multi-element icon */
export interface SvgElement {
  tag: 'path' | 'circle' | 'rect' | 'line'
  attrs: Record<string, string | number>
}

/**
 * Icon definition: either a legacy single-path `d` string
 * or an array of SvgElement for multi-element bespoke icons.
 */
export type IconDefinition = string | SvgElement[]

export interface BrandIconProps {
  name: BrandIconName
  /** Named size token. When omitted, falls back to className sizing (default: 'w-6 h-6'). */
  size?: IconSize
  /** Motion state. When omitted, icon renders as static SVG (zero overhead). */
  state?: IconState
  /** Stroke color tone. When omitted, uses currentColor. */
  tone?: IconTone
  /** CSS class for spacing, overrides. Default: 'w-6 h-6' (ignored when `size` is set). */
  className?: string
  /** Sets aria-label + role="img" instead of aria-hidden. */
  label?: string
}
