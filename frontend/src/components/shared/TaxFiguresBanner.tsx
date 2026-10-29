interface TaxFiguresBannerProps {
  children: string
  className?: string
}

/**
 * TaxFiguresBanner — non-dismissible notice that a tool's built-in statutory
 * figures await practitioner confirmation (Sprint 856 / 793b).
 *
 * Pass the tool's text from `@/content/tax-figures`. Deliberately has no close
 * control: the same line is printed in the tool's export.
 */
export function TaxFiguresBanner({ children, className = '' }: TaxFiguresBannerProps) {
  return (
    <div
      role="note"
      aria-label="Tax figures notice"
      className={`bg-clay-500/5 border border-clay-500/30 border-l-4 border-l-clay-500 rounded-xl p-4 ${className}`}
    >
      <p className="font-sans text-sm text-content-secondary leading-relaxed">
        <span className="font-medium text-clay-700 dark:text-clay-400">Tax figures:</span> {children}
      </p>
    </div>
  )
}
