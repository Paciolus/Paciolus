'use client'

/**
 * EngravedStat — Sprint 704 monument-style stat block.
 *
 * Replaces the flat `140+ / 12 / 7` stat-tile row with an
 * "engraved monument" treatment: oversized display-serif numeral with
 * oldstyle figures, a hairline underline, a Roman-numeral kicker
 * (I. / II. / III.) above, and a small-caps label below. Three stats
 * in a row restore the composition rhythm without feeling stat-tile
 * generic.
 *
 * Usage:
 *   <EngravedStat
 *     kicker="I."
 *     value="1,452"
 *     label="Automated Tests"
 *     sub="Across all 12 diagnostic tools"
 *   />
 *
 * Convention: use three instances in a row (`grid grid-cols-3` on
 * desktop, stacked on mobile). Numerals use oldstyle + proportional
 * figures to match the editorial direction from Sprint 703.
 */

interface EngravedStatProps {
  /** Roman-numeral kicker (e.g. "I.", "II.", "III."). Optional — omit
   *  for a single-use stat block or when the kicker would be visual noise. */
  kicker?: string
  /** The big number. Pass as a string so commas / "+" suffixes are
   *  author-controlled. */
  value: string
  /** Small-caps label below the value. */
  label: string
  /** Optional supporting sentence below the label. */
  sub?: string
  /** Additional classes merged onto the outer <figure> for grid
   *  placement at the call site. */
  className?: string
  /** Kicker + underline colour. Defaults to sage-500. */
  accent?: 'sage' | 'brass' | 'oatmeal'
}

const ACCENT_CLASSES: Record<NonNullable<EngravedStatProps['accent']>, {
  kicker: string
  rule: string
}> = {
  sage:    { kicker: 'text-sage-400',    rule: 'bg-sage-500/70' },
  brass:   { kicker: 'text-brass-400',   rule: 'bg-brass-400/70' },
  oatmeal: { kicker: 'text-oatmeal-400', rule: 'bg-oatmeal-400/60' },
}

export function EngravedStat({
  kicker,
  value,
  label,
  sub,
  className = '',
  accent = 'sage',
}: EngravedStatProps) {
  const palette = ACCENT_CLASSES[accent]
  return (
    <figure className={`flex flex-col items-center text-center ${className}`}>
      {kicker && (
        <span
          className={`font-sans text-[11px] uppercase tracking-[0.22em] ${palette.kicker} mb-2`}
        >
          {kicker}
        </span>
      )}
      <span
        className="font-serif text-5xl md:text-6xl font-semibold text-oatmeal-100 leading-none"
        style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
      >
        {value}
      </span>
      {/* Hairline underline — the "engraving" — scales to the value width. */}
      <span
        aria-hidden="true"
        className={`mt-3 h-px w-12 ${palette.rule}`}
      />
      <figcaption className="mt-3">
        <span className="font-sans text-[11px] uppercase tracking-[0.18em] text-oatmeal-300">
          {label}
        </span>
        {sub && (
          <span className="mt-1 block font-sans text-xs text-oatmeal-500 font-normal">
            {sub}
          </span>
        )}
      </figcaption>
    </figure>
  )
}
