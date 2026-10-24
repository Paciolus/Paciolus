/**
 * W-2 tax-year support messages — Sprint 839.
 */

/**
 * Sprint 839: the web form cannot send per-request statutory limits, so a tax
 * year with no built-in table is refused. The backend's refusal names the
 * tabulated years ("Tables available: 2025.") and tells API callers to use the
 * `statutory_limits` override, which the app does not offer; this turns it
 * into a message a preparer can act on.
 */
export function describeW2Error(raw: string | undefined, taxYear: number): string | undefined {
  if (!raw || !raw.startsWith('No statutory limit table')) return raw
  const listed = /Tables available: ([\d, ]+)\./.exec(raw)?.[1]?.trim()
  return unsupportedTaxYearMessage(taxYear, listed ? listed.split(/,\s*/).map(Number) : [])
}

export function unsupportedTaxYearMessage(taxYear: number, supportedYears: number[]): string {
  const years =
    supportedYears.length === 0
      ? 'no tax year yet'
      : `tax year${supportedYears.length === 1 ? '' : 's'} ${supportedYears.join(', ')}`
  return (
    `Tax year ${taxYear} cannot be reconciled in the app yet. Paciolus has built-in wage-base and ` +
    `contribution limits only for ${years}; a ${taxYear} run needs that year's figures, ` +
    `which are added once confirmed. Choose a supported tax year, or check back once ${taxYear} is added.`
  )
}
