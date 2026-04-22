'use client'

/**
 * ToolLedger — Sprint 706 bound-ledger grid for the homepage.
 *
 * Replaces the pre-Sprint-706 <ToolSlideshow> one-card-at-a-time carousel
 * (users hit "01 / 12 ‹ ›" and bounce on the first card) with the full
 * catalog rendered as a ledger-style grid: all 12 tools visible at once,
 * rows expand in place on click.
 *
 * Layout:
 *   - md+: 4-column header (№ · Name · Tests · Standards) followed by
 *     12 rows with hairline rules between. Row click expands an
 *     accordion body with the one-line summary + standards + a link to
 *     the tool catalog card.
 *   - Below md: simplified vertical list (one row per tool, tap to
 *     expand) — keeps the same data, drops the 4-column header.
 *
 * A11y: each row is a <button> with `aria-expanded` + `aria-controls`;
 * the expanded panel is keyboard-focusable; motion-reduce honored on
 * the accordion transition.
 *
 * Data source: `@/content/tool-ledger`. Adding / removing a tool
 * touches the data file only; a runtime assertion ensures
 * `TOOL_LEDGER.length === CANONICAL_TOOL_COUNT`.
 */

import { useState, useCallback, type KeyboardEvent } from 'react'
import Link from 'next/link'
import { Reveal } from '@/components/ui/Reveal'
import {
  CANONICAL_TOOL_COUNT,
  TOOL_LEDGER,
  type LedgerEntry,
} from '@/content/tool-ledger'

const ROMAN: Record<number, string> = {
  1: 'I', 2: 'II', 3: 'III', 4: 'IV', 5: 'V', 6: 'VI',
  7: 'VII', 8: 'VIII', 9: 'IX', 10: 'X', 11: 'XI', 12: 'XII',
}

export function ToolLedger() {
  const [expanded, setExpanded] = useState<string | null>(null)

  const toggle = useCallback((id: string) => {
    setExpanded(cur => (cur === id ? null : id))
  }, [])

  const onKey = useCallback(
    (e: KeyboardEvent<HTMLButtonElement>, id: string) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault()
        toggle(id)
      }
    },
    [toggle],
  )

  return (
    <section
      aria-label="Twelve audit tools — catalog ledger"
      className="max-w-6xl mx-auto px-6 py-16"
    >
      <Reveal className="text-center mb-8">
        <span className="inline-block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
          Catalog
        </span>
        <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-100 mb-2">
          Twelve Tools · One Platform
        </h2>
        <p className="font-sans text-sm text-oatmeal-400 max-w-xl mx-auto">
          Every paid tier unlocks the full suite. Click any row for the one-line scope.
        </p>
      </Reveal>

      {/* md+ ledger header */}
      <Reveal>
        <div className="hidden md:grid grid-cols-[3rem_minmax(0,1fr)_5rem_minmax(0,16rem)] gap-x-6 px-4 pb-2 border-b border-obsidian-500/60 font-sans text-[10px] uppercase tracking-[0.18em] text-oatmeal-500">
          <span className="text-right">№</span>
          <span>Tool</span>
          <span className="text-right">Tests</span>
          <span>Standards</span>
        </div>
      </Reveal>

      {/* Rows — same DOM for mobile + desktop; layout flips via grid rules */}
      <div role="list" className="divide-y divide-obsidian-600/40">
        {TOOL_LEDGER.map(entry => (
          <LedgerRow
            key={entry.id}
            entry={entry}
            isExpanded={expanded === entry.id}
            onToggle={() => toggle(entry.id)}
            onKey={e => onKey(e, entry.id)}
          />
        ))}
      </div>

      <Reveal delay={0.05}>
        <p className="mt-8 text-center font-sans text-[10px] uppercase tracking-[0.18em] text-oatmeal-500">
          {CANONICAL_TOOL_COUNT} tools · every paid plan · every result cited
        </p>
      </Reveal>
    </section>
  )
}

function LedgerRow({
  entry,
  isExpanded,
  onToggle,
  onKey,
}: {
  entry: LedgerEntry
  isExpanded: boolean
  onToggle: () => void
  onKey: (e: KeyboardEvent<HTMLButtonElement>) => void
}) {
  const panelId = `tool-ledger-panel-${entry.id}`
  const buttonId = `tool-ledger-button-${entry.id}`

  return (
    <div role="listitem">
      <button
        type="button"
        id={buttonId}
        aria-expanded={isExpanded}
        aria-controls={panelId}
        onClick={onToggle}
        onKeyDown={onKey}
        className={`
          w-full grid gap-x-6 px-4 py-4 text-left
          grid-cols-[2rem_minmax(0,1fr)] md:grid-cols-[3rem_minmax(0,1fr)_5rem_minmax(0,16rem)]
          hover:bg-obsidian-800/40 focus:outline-hidden
          focus-visible:ring-2 focus-visible:ring-sage-500 focus-visible:ring-offset-1 focus-visible:ring-offset-obsidian-900
          transition-colors motion-reduce:transition-none
        `}
      >
        <span
          className="text-right font-mono text-sm text-sage-400 self-center"
          style={{ fontVariantNumeric: 'tabular-nums lining-nums' }}
          aria-hidden="true"
        >
          <span className="md:hidden">{entry.number}.</span>
          <span className="hidden md:inline">{ROMAN[entry.number]}.</span>
        </span>

        <span className="font-serif text-base md:text-lg text-oatmeal-100 self-center">
          {entry.name}
        </span>

        <span
          className="hidden md:block text-right text-oatmeal-400 self-center font-mono text-sm"
          style={{ fontVariantNumeric: 'tabular-nums lining-nums' }}
        >
          {entry.testCount ?? '—'}
        </span>

        <span className="hidden md:flex flex-wrap gap-1 self-center">
          {entry.standards.map(code => (
            <span
              key={code}
              className="font-sans text-[10px] uppercase tracking-wider text-oatmeal-400 border border-obsidian-500/40 rounded-full px-2 py-0.5"
            >
              {code}
            </span>
          ))}
        </span>
      </button>

      {/* Accordion panel */}
      <div
        id={panelId}
        role="region"
        aria-labelledby={buttonId}
        hidden={!isExpanded}
        className="px-4 pb-5 pt-1"
      >
        {isExpanded && (
          <div className="grid grid-cols-1 md:grid-cols-[3rem_minmax(0,1fr)] gap-x-6 text-sm">
            <span className="hidden md:block" aria-hidden="true" />
            <div>
              <p className="font-serif text-oatmeal-200 leading-relaxed">
                {entry.summary}
              </p>
              {/* Mobile-only standards pills (desktop shows them in the row) */}
              <div className="md:hidden mt-3 flex flex-wrap gap-1">
                {entry.standards.map(code => (
                  <span
                    key={code}
                    className="font-sans text-[10px] uppercase tracking-wider text-oatmeal-400 border border-obsidian-500/40 rounded-full px-2 py-0.5"
                  >
                    {code}
                  </span>
                ))}
              </div>
              <div className="mt-4">
                <Link
                  href={entry.href}
                  className="inline-flex items-center gap-1 font-sans text-sm text-sage-400 hover:text-sage-300 transition-colors motion-reduce:transition-none"
                >
                  Open tool
                  <span aria-hidden="true">→</span>
                </Link>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}
