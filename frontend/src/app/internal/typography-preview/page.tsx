'use client'

/**
 * Typography Preview — Sprint 703 decision aid
 *
 * Renders the same three compositions in four candidate body serifs so
 * the CEO can pick visually rather than blind. Three compositions:
 *
 *   1. Pull-quote (italic, the About-page "defensible answer" line)
 *   2. Stats block with oldstyle figures + small-caps labels
 *   3. Report-style heading + body paragraph
 *
 * Four candidates:
 *
 *   - Merriweather (current body serif) — baseline for comparison
 *   - Source Serif 4 (free, Google Fonts) — open-source option
 *   - Lora (free, Google Fonts) — warm/Tiempos-like proxy
 *   - Playfair Display (free, Google Fonts) — sharp/Sectra-like proxy
 *
 * NOTE ON LICENSING:
 *   Tiempos Text (Typotheque) and GT Sectra (Grilli Type) both require
 *   paid licenses to serve in production. Lora and Playfair Display are
 *   shown here as *visual approximations* so the typographic DIRECTION
 *   can be evaluated. The final production switch to Tiempos or Sectra
 *   would require acquiring the license. Vendor specimens are linked at
 *   the bottom of the page for validation against the real typefaces.
 */

import { useState } from 'react'
import Link from 'next/link'
import { Reveal } from '@/components/ui/Reveal'

type CandidateKey = 'merriweather' | 'source-serif-4' | 'lora' | 'playfair-display'

const CANDIDATES: {
  key: CandidateKey
  label: string
  cssFamily: string
  license: 'current' | 'free' | 'paid-proxy'
  proxyFor?: string
  vendor?: string
  vendorUrl?: string
  note: string
}[] = [
  {
    key: 'merriweather',
    label: 'Merriweather',
    cssFamily: "'Merriweather', 'Source Serif 4', Georgia, serif",
    license: 'current',
    note:
      'Currently shipping on all Paciolus surfaces. Baseline — everything else is compared against this.',
  },
  {
    key: 'source-serif-4',
    label: 'Source Serif 4',
    cssFamily: "'Source Serif 4', Georgia, serif",
    license: 'free',
    note:
      'Adobe open-source. Neutral, editorial, optical-sized. Safe default if licensing is a blocker.',
  },
  {
    key: 'lora',
    label: 'Lora',
    cssFamily: "'Lora', 'Tiempos Text', Georgia, serif",
    license: 'paid-proxy',
    proxyFor: 'Tiempos Text',
    vendor: 'Typotheque',
    vendorUrl: 'https://www.typotheque.com/fonts/tiempos_text',
    note:
      'Free proxy for Tiempos Text. Similar brushed curves and warm feel; real Tiempos is more refined and has truer oldstyle figures. Use this to judge the direction — warmth + readability at body size.',
  },
  {
    key: 'playfair-display',
    label: 'Playfair Display',
    cssFamily: "'Playfair Display', 'GT Sectra', Georgia, serif",
    license: 'paid-proxy',
    proxyFor: 'GT Sectra',
    vendor: 'Grilli Type',
    vendorUrl: 'https://www.grillitype.com/typeface/gt-sectra',
    note:
      'Free proxy for GT Sectra. High-contrast Didone-adjacent display serif; use this to judge the sharper, more modern editorial direction. Note: Playfair is more ornate than Sectra; Sectra is crisper at text size.',
  },
]

const LICENSE_BADGE: Record<CandidateKey, { label: string; className: string }> = {
  merriweather: { label: 'Current', className: 'bg-oatmeal-100 text-obsidian-800 border-oatmeal-400' },
  'source-serif-4': { label: 'Free', className: 'bg-sage-50 text-sage-700 border-sage-300' },
  lora: { label: 'Proxy', className: 'bg-clay-50 text-clay-700 border-clay-300' },
  'playfair-display': { label: 'Proxy', className: 'bg-clay-50 text-clay-700 border-clay-300' },
}

/* ─── Fixed test copy — same across every candidate ────────────── */

const PULL_QUOTE =
  'The moment when you need a defensible answer is the moment when you should not be hunting through spreadsheet tabs.'
const PULL_QUOTE_ATTR = 'Paciolus — About page, 2026'

const REPORT_HEADING = 'Trial Balance Diagnostic'
const REPORT_SUBHEAD = 'Material Misstatement Risk: Elevated'
const REPORT_BODY =
  'Three accounts in the revenue ledger exhibit an unusually narrow variance band relative to the industry benchmark (1.2σ vs. 3.4σ), consistent with period-end smoothing rather than normal operating fluctuation. Recommend substantive procedures under ISA 240 paragraphs A24–A27; reference the Revenue Testing report (RT-09 cut-off, RT-17 contract validity) for sample selection.'

const STATS = [
  { value: '1,452', label: 'Automated Tests' },
  { value: '12', label: 'Diagnostic Tools' },
  { value: '7', label: 'Audit Frameworks' },
]

/* ─── Component ─────────────────────────────────────────────────── */

export default function TypographyPreviewPage() {
  const [selectedLeft, setSelectedLeft] = useState<CandidateKey>('merriweather')
  const [selectedRight, setSelectedRight] = useState<CandidateKey>('source-serif-4')

  // Note: No auth gate — this is a decision-aid page (typography mockups, no
  // sensitive data). The /internal path prefix is a discoverability convention;
  // AuthenticatedShell in the layout renders the nav chrome but doesn't
  // redirect. A prior auth gate here raced the session-load and left the page
  // blank when the hook was still loading.

  return (
    <>
      {/* Google Fonts — React 19 hoists <link> into <head> automatically. */}
      <link rel="preconnect" href="https://fonts.googleapis.com" />
      <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      <link
        rel="stylesheet"
        href="https://fonts.googleapis.com/css2?family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=Lora:ital,wght@0,400;0,600;1,400&family=Playfair+Display:ital,wght@0,400;0,600;1,400&display=swap"
      />

      <main id="main-content" className="min-h-screen bg-surface-page">
        <div className="max-w-7xl mx-auto px-6 py-10">
          <Reveal>
            <header className="mb-8">
              <div className="flex items-center gap-2 text-xs font-sans uppercase tracking-wider text-content-tertiary mb-2">
                <span>Sprint 703</span>
                <span className="text-content-muted">·</span>
                <span>Internal decision aid</span>
              </div>
              <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary mb-2">
                Body serif selection
              </h1>
              <p className="text-sm font-sans text-content-secondary max-w-3xl">
                Same three compositions rendered in four candidate body serifs. Pick the pair on the compare bar
                below to view any two side-by-side. Lora and Playfair Display are free visual proxies for the
                paid Tiempos Text and GT Sectra — vendor specimens linked at the bottom for validation against
                the real typefaces.
              </p>
            </header>
          </Reveal>

          {/* Candidate summary strip */}
          <Reveal delay={0.05}>
            <section className="theme-card p-5 mb-8">
              <h2 className="font-serif text-sm font-bold text-content-primary mb-4">Candidates</h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {CANDIDATES.map(c => (
                  <div
                    key={c.key}
                    className="border border-theme rounded-lg p-3 bg-surface-card-secondary"
                  >
                    <div className="flex items-center justify-between mb-2">
                      <span
                        className="text-lg font-semibold text-content-primary"
                        style={{ fontFamily: c.cssFamily }}
                      >
                        {c.label}
                      </span>
                      <span
                        className={`text-[10px] font-sans font-medium px-2 py-0.5 rounded border ${LICENSE_BADGE[c.key].className}`}
                      >
                        {LICENSE_BADGE[c.key].label}
                      </span>
                    </div>
                    {c.proxyFor && (
                      <p className="text-[11px] font-sans text-content-tertiary mb-1">
                        Proxy for <span className="font-semibold">{c.proxyFor}</span> ({c.vendor})
                      </p>
                    )}
                    <p className="text-xs font-sans text-content-secondary leading-relaxed">{c.note}</p>
                  </div>
                ))}
              </div>
            </section>
          </Reveal>

          {/* Side-by-side compare selector */}
          <Reveal delay={0.1}>
            <div className="theme-card p-4 mb-6 flex flex-wrap items-center gap-4">
              <span className="text-xs font-sans font-medium text-content-secondary uppercase tracking-wider">
                Compare
              </span>
              <label className="flex items-center gap-2">
                <span className="text-xs font-sans text-content-tertiary">Left</span>
                <select
                  value={selectedLeft}
                  onChange={e => setSelectedLeft(e.target.value as CandidateKey)}
                  className="px-3 py-1.5 rounded bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                >
                  {CANDIDATES.map(c => (
                    <option key={c.key} value={c.key}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </label>
              <label className="flex items-center gap-2">
                <span className="text-xs font-sans text-content-tertiary">Right</span>
                <select
                  value={selectedRight}
                  onChange={e => setSelectedRight(e.target.value as CandidateKey)}
                  className="px-3 py-1.5 rounded bg-surface-input border border-theme text-content-primary font-sans text-sm focus:outline-hidden focus:ring-2 focus:ring-sage-500"
                >
                  {CANDIDATES.map(c => (
                    <option key={c.key} value={c.key}>
                      {c.label}
                    </option>
                  ))}
                </select>
              </label>
            </div>
          </Reveal>

          {/* Side-by-side render */}
          <Reveal delay={0.15}>
            <section className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-12">
              <CandidatePanel candidate={CANDIDATES.find(c => c.key === selectedLeft)!} />
              <CandidatePanel candidate={CANDIDATES.find(c => c.key === selectedRight)!} />
            </section>
          </Reveal>

          {/* Full stack render (one column per candidate) */}
          <Reveal delay={0.2}>
            <header className="mb-4">
              <h2 className="font-serif text-xl font-bold text-content-primary">All four, stacked</h2>
              <p className="text-xs font-sans text-content-secondary">
                Scroll through every candidate against the identical composition. Easier for judging
                rhythm over a longer reading stretch.
              </p>
            </header>
          </Reveal>

          <div className="space-y-8">
            {CANDIDATES.map((c, idx) => (
              <Reveal key={c.key} delay={0.25 + idx * 0.05}>
                <CandidatePanel candidate={c} />
              </Reveal>
            ))}
          </div>

          {/* Vendor specimen links */}
          <Reveal delay={0.5}>
            <section className="theme-card p-6 mt-12">
              <h2 className="font-serif text-lg font-bold text-content-primary mb-3">Validate the proxies</h2>
              <p className="text-sm font-sans text-content-secondary mb-4">
                Lora and Playfair Display are free stand-ins to judge direction. Before committing to Tiempos or
                Sectra, look at the real typeface specimens:
              </p>
              <ul className="space-y-2 text-sm font-sans">
                <li>
                  <a
                    href="https://www.typotheque.com/fonts/tiempos_text"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sage-700 hover:text-sage-800 underline"
                  >
                    Tiempos Text — Typotheque specimen ↗
                  </a>
                  <span className="text-content-tertiary"> — licensing ~$600/yr for a production webfont subscription.</span>
                </li>
                <li>
                  <a
                    href="https://www.grillitype.com/typeface/gt-sectra"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sage-700 hover:text-sage-800 underline"
                  >
                    GT Sectra — Grilli Type specimen ↗
                  </a>
                  <span className="text-content-tertiary"> — licensing ~$400/yr for a production webfont subscription.</span>
                </li>
                <li>
                  <a
                    href="https://fonts.google.com/specimen/Source+Serif+4"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sage-700 hover:text-sage-800 underline"
                  >
                    Source Serif 4 — Google Fonts specimen ↗
                  </a>
                  <span className="text-content-tertiary"> — free, already rendered above.</span>
                </li>
              </ul>
            </section>
          </Reveal>

          <Reveal delay={0.55}>
            <section className="theme-card p-6 mt-6 mb-4">
              <h2 className="font-serif text-lg font-bold text-content-primary mb-2">Your pick</h2>
              <p className="text-sm font-sans text-content-secondary">
                Drop your decision in <Link href="/internal/admin" className="text-sage-700 underline">the CEO action
                log</Link>, or reply on PR #89 with the candidate key. Sprint 703 will integrate the chosen serif
                via <code className="font-mono text-xs bg-surface-card-secondary px-1 rounded">next/font</code> in
                the root layout; every downstream design sprint (704–708) composes against it.
              </p>
            </section>
          </Reveal>
        </div>
      </main>
    </>
  )
}

/* ─── Composition panel (pull-quote + stats + report) ───────────── */

function CandidatePanel({
  candidate,
}: {
  candidate: typeof CANDIDATES[number]
}) {
  const { label, cssFamily, license, proxyFor, vendor } = candidate
  return (
    <section className="theme-card p-8 bg-surface-card" style={{ fontFamily: cssFamily }}>
      <header className="mb-6 pb-4 border-b border-theme">
        <div className="flex items-center justify-between">
          <span className="font-sans text-sm font-medium text-content-secondary uppercase tracking-wider">
            {label}
          </span>
          <span
            className={`text-[10px] font-sans font-medium px-2 py-0.5 rounded border ${LICENSE_BADGE[candidate.key].className}`}
          >
            {license === 'paid-proxy' ? `Proxy for ${proxyFor} (${vendor})` : license === 'free' ? 'Free' : 'Current'}
          </span>
        </div>
      </header>

      {/* Pull quote — italic */}
      <blockquote className="mb-8 border-l-2 border-sage-500 pl-6 py-2">
        <p
          className="text-2xl md:text-3xl leading-snug text-content-primary"
          style={{ fontStyle: 'italic', fontWeight: 400 }}
        >
          &ldquo;{PULL_QUOTE}&rdquo;
        </p>
        <footer className="mt-3 text-xs font-sans text-content-tertiary not-italic">
          — {PULL_QUOTE_ATTR}
        </footer>
      </blockquote>

      {/* Stats — oldstyle figures + small-caps labels */}
      <div className="mb-8 grid grid-cols-3 gap-6 text-center">
        {STATS.map(s => (
          <div key={s.label}>
            <div
              className="text-4xl md:text-5xl font-semibold text-content-primary"
              style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
            >
              {s.value}
            </div>
            <div
              className="mt-1 text-[11px] text-content-secondary uppercase"
              style={{
                fontVariant: 'small-caps',
                letterSpacing: '0.1em',
              }}
            >
              {s.label}
            </div>
          </div>
        ))}
      </div>

      {/* Report heading + body */}
      <article>
        <h3 className="text-xl md:text-2xl font-semibold text-content-primary mb-1">
          {REPORT_HEADING}
        </h3>
        <p
          className="text-base font-medium text-clay-700 mb-4"
          style={{ fontStyle: 'italic' }}
        >
          {REPORT_SUBHEAD}
        </p>
        <p
          className="text-base leading-relaxed text-content-secondary"
          style={{ fontVariantNumeric: 'oldstyle-nums proportional-nums' }}
        >
          {REPORT_BODY}
        </p>
      </article>
    </section>
  )
}
