'use client'

/**
 * StandardsSpecimen — Sprint 705 "the one thing."
 *
 * Replaces the pre-Sprint-705 pill strip ("ISA 240 — Fraud Risk in
 * Revenue", "ISA 530 — Audit Sampling", …) on the homepage with a
 * two-column specimen page from a bound auditing-reference volume.
 *
 * Layout:
 *   - At `md+`: two columns with a hairline vertical rule between.
 *     Entries grouped by governing body; body headings set in small caps.
 *     Each entry renders as a <dt> (code + paragraph citation) + <dd>
 *     (scope line).
 *   - Below `md`: falls back to the original horizontal pill strip via
 *     `<FallbackPills>` so small screens don't collapse the specimen
 *     layout into unreadable column stacks.
 *
 * Accessibility: semantic <dl>/<dt>/<dd> pairs; keyboard-focusable entry
 * rows with visible focus rings; `prefers-reduced-motion` respected on
 * the hover expansion.
 *
 * Data source: `@/content/standards-specimen` — adding a new standard
 * touches the data file only.
 */

import { useMemo } from 'react'
import Link from 'next/link'
import {
  STANDARDS_SPECIMEN,
  BODY_ORDER,
  BODY_LABELS,
  type SpecimenEntry,
} from '@/content/standards-specimen'

/* ─── Helper: map tool IDs to their catalog href ─────────────────── */

const TOOL_HREF: Record<string, string> = {
  trial_balance: '/tools/trial-balance',
  multi_period: '/tools/multi-period',
  journal_entry_testing: '/tools/journal-entry-testing',
  ap_testing: '/tools/ap-testing',
  bank_reconciliation: '/tools/bank-rec',
  payroll_testing: '/tools/payroll-testing',
  three_way_match: '/tools/three-way-match',
  revenue_testing: '/tools/revenue-testing',
  ar_aging: '/tools/ar-aging',
  fixed_asset_testing: '/tools/fixed-assets',
  inventory_testing: '/tools/inventory-testing',
  statistical_sampling: '/tools/statistical-sampling',
  composite_risk: '/tools/composite-risk',
  account_risk_heatmap: '/tools/account-risk-heatmap',
}

function firstToolHref(ids: string[]): string {
  for (const id of ids) {
    const href = TOOL_HREF[id]
    if (href) return href
  }
  return '/tools'
}

/* ─── Small components ───────────────────────────────────────────── */

function BodyHeading({ body }: { body: SpecimenEntry['body'] }) {
  return (
    <h3 className="mt-8 mb-4 font-sans text-[11px] uppercase tracking-[0.2em] text-sage-400 border-b border-obsidian-600/60 pb-2">
      {BODY_LABELS[body]}
    </h3>
  )
}

function EntryRow({ entry, isFirst }: { entry: SpecimenEntry; isFirst: boolean }) {
  const toolHref = firstToolHref(entry.tools)
  // Drop-cap: only on the first entry of each column (we'll set it via a
  // `:first-child` selector on `.specimen-column`). Here, `isFirst`
  // controls whether this entry is the column-opener for the author; the
  // actual drop-cap rendering uses CSS.
  return (
    <Link
      href={toolHref}
      className={`block group py-3 border-b border-obsidian-600/40 last:border-b-0 focus:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-500 focus-visible:ring-offset-1 focus-visible:ring-offset-obsidian-900 rounded-sm`}
    >
      <div className="flex items-baseline gap-2">
        <dt
          className="font-serif font-bold text-oatmeal-200 text-base whitespace-nowrap"
          style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
        >
          {entry.code}
        </dt>
        {entry.paragraphs && (
          <sup
            className="font-sans text-[10px] text-sage-400 uppercase tracking-wider"
            style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
          >
            {entry.paragraphs}
          </sup>
        )}
      </div>
      <dd
        className={`mt-1 font-serif text-sm text-oatmeal-400 leading-snug ${isFirst ? 'specimen-first-of-column' : ''}`}
      >
        {entry.scope}
      </dd>
      <p className="mt-1 font-sans text-[10px] uppercase tracking-[0.12em] text-oatmeal-500/70 group-hover:text-sage-400 transition-colors motion-reduce:transition-none">
        → cited in {entry.tools.length} tool{entry.tools.length === 1 ? '' : 's'}
      </p>
    </Link>
  )
}

/* ─── Main component ─────────────────────────────────────────────── */

export function StandardsSpecimen() {
  // Partition entries into two columns, keeping body groupings intact.
  // Simple heuristic: split the flattened (body-heading + entries) list
  // roughly in half by token count, preferring to keep a body's entries
  // in the same column.
  const { leftEntries, rightEntries } = useMemo(() => partitionByBody(STANDARDS_SPECIMEN), [])

  return (
    <>
      {/* md+ specimen layout */}
      <section
        aria-label="Standards cited by Paciolus tools"
        className="hidden md:block relative mx-auto max-w-5xl mt-10 pt-8 pb-6 px-6 border-t border-b border-obsidian-600/60"
      >
        <p className="absolute -top-3 left-1/2 -translate-x-1/2 px-3 bg-obsidian-800 font-sans text-[10px] uppercase tracking-[0.2em] text-oatmeal-500">
          Standards Specimen · Every Citation
        </p>

        <div className="grid grid-cols-2 gap-10 relative">
          {/* Vertical hairline between the two columns */}
          <div
            aria-hidden="true"
            className="absolute top-0 bottom-0 left-1/2 -translate-x-px w-px bg-obsidian-600/60"
          />

          <dl className="specimen-column pr-4">
            <RenderColumn entries={leftEntries} />
          </dl>
          <dl className="specimen-column pl-4">
            <RenderColumn entries={rightEntries} />
          </dl>
        </div>

        <p className="mt-6 text-center font-sans text-[10px] uppercase tracking-[0.16em] text-oatmeal-500">
          {STANDARDS_SPECIMEN.length} standards · {new Set(STANDARDS_SPECIMEN.flatMap(e => e.tools)).size} tools cite them
        </p>
      </section>

      {/* Mobile fallback — the original horizontal pill strip */}
      <div className="md:hidden mt-10">
        <FallbackPills entries={STANDARDS_SPECIMEN} />
      </div>
    </>
  )
}

function RenderColumn({ entries }: { entries: ColumnItem[] }) {
  // Find the first actual entry in the column so we can place the drop-cap.
  const firstEntryIndex = entries.findIndex(item => item.type === 'entry')
  return (
    <>
      {entries.map((item, idx) => {
        if (item.type === 'heading') {
          return <BodyHeading key={`h-${item.body}-${idx}`} body={item.body} />
        }
        return <EntryRow key={`e-${item.entry.code}-${idx}`} entry={item.entry} isFirst={idx === firstEntryIndex} />
      })}
    </>
  )
}

function FallbackPills({ entries }: { entries: SpecimenEntry[] }) {
  return (
    <div className="flex flex-wrap justify-center gap-2 px-4">
      {entries.map(e => (
        <Link
          key={e.code}
          href={firstToolHref(e.tools)}
          className="px-3 py-1.5 rounded-full font-sans text-xs text-oatmeal-400 bg-obsidian-800/50 border border-obsidian-500/25 hover:border-sage-500/40 hover:text-oatmeal-200 transition-colors motion-reduce:transition-none"
        >
          {e.code}
        </Link>
      ))}
    </div>
  )
}

/* ─── Column partitioning ────────────────────────────────────────── */

type ColumnItem =
  | { type: 'heading'; body: SpecimenEntry['body'] }
  | { type: 'entry'; entry: SpecimenEntry }

function partitionByBody(entries: SpecimenEntry[]): { leftEntries: ColumnItem[]; rightEntries: ColumnItem[] } {
  // Build a single flat list with headings interspersed, grouped by BODY_ORDER.
  const flat: ColumnItem[] = []
  for (const body of BODY_ORDER) {
    const group = entries.filter(e => e.body === body)
    if (group.length === 0) continue
    flat.push({ type: 'heading', body })
    for (const entry of group) {
      flat.push({ type: 'entry', entry })
    }
  }

  // Split at the boundary nearest to half-count, on a body-heading split
  // point so one body's entries aren't broken across columns.
  const target = Math.ceil(flat.filter(i => i.type === 'entry').length / 2)
  let entriesSeen = 0
  let splitIdx = flat.length
  for (let i = 0; i < flat.length; i++) {
    const item = flat[i]
    if (item && item.type === 'entry') entriesSeen++
    if (item && item.type === 'heading' && entriesSeen >= target) {
      splitIdx = i
      break
    }
  }

  return {
    leftEntries: flat.slice(0, splitIdx),
    rightEntries: flat.slice(splitIdx),
  }
}
