'use client'

import Link from 'next/link'

/**
 * Journal Entry Testing — Placeholder (Sprint 66)
 *
 * This route is scaffolded in Sprint 62 but the full tool
 * will be implemented in Sprint 66.
 */
export default function JournalEntryTestingPage() {
  return (
    <main className="min-h-screen bg-gradient-obsidian">
      <nav className="fixed top-0 w-full bg-obsidian-900/90 backdrop-blur-lg border-b border-obsidian-600/30 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3 group">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
            />
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/tools/trial-balance"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              TB Diagnostics
            </Link>
            <Link
              href="/tools/multi-period"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Multi-Period
            </Link>
            <span className="text-sm font-sans text-sage-400 border-b border-sage-400/50">
              JE Testing
            </span>
          </div>
        </div>
      </nav>

      <div className="pt-24 pb-16 px-6 max-w-4xl mx-auto text-center">
        <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-500/10 border border-sage-500/20 mb-8">
          <div className="w-2 h-2 bg-sage-400 rounded-full"></div>
          <span className="text-sage-300 text-sm font-sans font-medium">Coming Soon</span>
        </div>

        <h1 className="font-serif text-4xl text-oatmeal-100 mb-4">
          Journal Entry Testing
        </h1>
        <p className="font-sans text-oatmeal-400 text-lg max-w-2xl mx-auto mb-8">
          Automated journal entry analysis with Benford&apos;s Law, statistical anomaly detection,
          and a 17-test battery across structural, statistical, and advanced tiers.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12 max-w-3xl mx-auto">
          <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
            <div className="text-2xl mb-3">T1-T5</div>
            <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Structural Tests</h3>
            <p className="font-sans text-oatmeal-500 text-xs">
              Unbalanced entries, missing fields, duplicates, round amounts, unusual amounts
            </p>
          </div>
          <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
            <div className="text-2xl mb-3">T6-T8</div>
            <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Statistical Tests</h3>
            <p className="font-sans text-oatmeal-500 text-xs">
              Benford&apos;s Law analysis, weekend postings, month-end clustering
            </p>
          </div>
          <div className="bg-obsidian-800/50 border border-obsidian-600/30 rounded-xl p-6">
            <div className="text-2xl mb-3">T9-T17</div>
            <h3 className="font-serif text-oatmeal-200 text-sm mb-2">Advanced Tests</h3>
            <p className="font-sans text-oatmeal-500 text-xs">
              User analysis, backdating, reciprocal entries, threshold splitting
            </p>
          </div>
        </div>

        <Link
          href="/tools/trial-balance"
          className="inline-block mt-12 px-6 py-3 bg-sage-500/20 border border-sage-500/40 rounded-lg text-sage-300 font-sans text-sm hover:bg-sage-500/30 transition-colors"
        >
          Try TB Diagnostics in the meantime
        </Link>
      </div>
    </main>
  )
}
