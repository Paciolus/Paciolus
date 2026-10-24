import type { Metadata } from 'next'
import Link from 'next/link'
import { AUTHORITIES, authorityForCode } from '@/content/authorities'
import { METHODOLOGY_SOURCES, type SourceKind } from '@/content/methodology-sources'

/**
 * Sources & Methodology — Sprint 835.
 *
 * Paciolus is not an accounting authority. This page shows, for every tool and
 * test, the rule applied, the authority it comes from, and which numbers are
 * Paciolus's own choices. Data: `content/methodology-sources.ts` (checked
 * against `backend/standards_registry.py` in CI) and `content/authorities.ts`.
 */

export const metadata: Metadata = {
  title: 'Sources & Methodology — Paciolus',
  description:
    'Every Paciolus test, the rule it applies, the standard or statute it comes from, and which thresholds are our own choices.',
  openGraph: {
    title: 'Sources & Methodology — Paciolus',
    description: 'Where every Paciolus rule comes from, and which numbers are ours.',
  },
}

const KIND_LABELS: Record<SourceKind, { label: string; description: string; badge: string }> = {
  requirement: {
    label: 'Required by a standard or statute',
    description: 'The rule or figure is set by the cited source, such as a filing threshold in the tax code.',
    badge: 'bg-sage-500/15 text-sage-300 border-sage-500/30',
  },
  guidance: {
    label: 'Described by a standard',
    description:
      'The cited source names this as an indicator or a procedure to consider, without prescribing the test or its thresholds.',
    badge: 'bg-sage-500/10 text-sage-200 border-sage-500/20',
  },
  'published-method': {
    label: 'Published method',
    description: 'A statistical or forensic method from published literature, applied as published.',
    badge: 'bg-oatmeal-500/10 text-oatmeal-200 border-oatmeal-500/30',
  },
  convention: {
    label: 'Paciolus convention',
    description:
      'Our own choice: a threshold, weight, band or cut-off that no authority sets. These are defaults for your judgment, not rules.',
    badge: 'bg-clay-500/10 text-clay-300 border-clay-500/30',
  },
}

const KIND_ORDER: SourceKind[] = ['requirement', 'guidance', 'published-method', 'convention']

function countByKind(): Record<SourceKind, number> {
  const counts: Record<SourceKind, number> = { requirement: 0, guidance: 0, 'published-method': 0, convention: 0 }
  for (const tool of METHODOLOGY_SOURCES) for (const rule of tool.rules) counts[rule.kind] += 1
  return counts
}

function citedCodesByAuthority(): Map<string, string[]> {
  const byAuthority = new Map<string, Set<string>>()
  for (const tool of METHODOLOGY_SOURCES) {
    for (const rule of tool.rules) {
      for (const code of rule.sources) {
        const authority = authorityForCode(code)
        if (!authority) continue
        if (!byAuthority.has(authority.key)) byAuthority.set(authority.key, new Set())
        byAuthority.get(authority.key)!.add(code)
      }
    }
  }
  return new Map([...byAuthority].map(([key, codes]) => [key, [...codes].sort()]))
}

export default function SourcesPage() {
  const counts = countByKind()
  const totalRules = KIND_ORDER.reduce((sum, kind) => sum + counts[kind], 0)
  const cited = citedCodesByAuthority()

  return (
    <main id="main-content" className="relative pt-32 pb-24 px-6">
      <div className="max-w-5xl mx-auto">
        <header className="mb-14">
          <h1 className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-5">Sources &amp; Methodology</h1>
          <p className="font-sans text-lg text-oatmeal-300 leading-relaxed max-w-3xl">
            Paciolus is not an accounting or auditing authority. Our tools apply rules published by the bodies that
            set them, and present the results conveniently. This page lists, for every test, the rule it applies, the
            source it comes from, and which numbers are our own choices, so you can check our work against the
            original.
          </p>
          <p className="font-sans text-sm text-oatmeal-400 mt-4 max-w-3xl">
            Nothing here is an audit opinion or a substitute for your professional judgment. Where a standard is
            cited, read the standard itself; we cite at the level of the standard and do not quote paragraph numbers
            we have not confirmed.
          </p>
        </header>

        <section className="mb-16" aria-labelledby="kinds-heading">
          <h2 id="kinds-heading" className="font-serif text-2xl text-oatmeal-100 mb-2">
            How to read each rule
          </h2>
          <p className="font-sans text-sm text-oatmeal-400 mb-6">
            <span className="font-mono">{totalRules}</span> rules across{' '}
            <span className="font-mono">{METHODOLOGY_SOURCES.length}</span> tools and scores, each marked with one of
            four kinds of basis.
          </p>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {KIND_ORDER.map(kind => (
              <div key={kind} className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-5">
                <div className="flex items-baseline justify-between gap-3 mb-2">
                  <span className={`font-sans text-xs uppercase tracking-wider px-2 py-0.5 rounded border ${KIND_LABELS[kind].badge}`}>
                    {KIND_LABELS[kind].label}
                  </span>
                  <span className="font-mono text-sm text-oatmeal-300">{counts[kind]}</span>
                </div>
                <p className="font-sans text-sm text-oatmeal-400">{KIND_LABELS[kind].description}</p>
              </div>
            ))}
          </div>
        </section>

        <section className="mb-16" aria-labelledby="authorities-heading">
          <h2 id="authorities-heading" className="font-serif text-2xl text-oatmeal-100 mb-6">
            The authorities we cite
          </h2>
          <ul className="space-y-4">
            {AUTHORITIES.filter(a => cited.has(a.key)).map(authority => (
              <li key={authority.key} className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-5">
                <h3 className="font-serif text-lg text-oatmeal-100">{authority.name}</h3>
                <p className="font-sans text-sm text-oatmeal-400 mt-1">{authority.description}</p>
                <p className="font-sans text-xs text-oatmeal-500 mt-2">
                  {authority.url ? (
                    <a href={authority.url} target="_blank" rel="noopener noreferrer" className="text-sage-400 hover:text-sage-300 underline">
                      Where to read it
                    </a>
                  ) : (
                    'Available from libraries and booksellers'
                  )}
                  {' · '}
                  {authority.access}
                </p>
                <p className="font-mono text-xs text-oatmeal-300 mt-3 leading-relaxed">{cited.get(authority.key)!.join(' · ')}</p>
              </li>
            ))}
          </ul>
        </section>

        <section aria-labelledby="tools-heading">
          <h2 id="tools-heading" className="font-serif text-2xl text-oatmeal-100 mb-2">
            Tool by tool
          </h2>
          <p className="font-sans text-sm text-oatmeal-400 mb-6">
            Open a tool to see each test. Thresholds marked as Paciolus conventions are starting points; where a tool
            lets you change one for a run, the rule says so.
          </p>
          <div className="space-y-3">
            {METHODOLOGY_SOURCES.map(tool => (
              <details key={tool.toolKey} className="group bg-obsidian-800 border border-obsidian-600 rounded-lg">
                <summary className="cursor-pointer list-none px-5 py-4 flex items-center justify-between gap-4">
                  <span className="font-serif text-lg text-oatmeal-100">{tool.toolName}</span>
                  <span className="font-mono text-xs text-oatmeal-400">{tool.rules.length} rules</span>
                </summary>
                <div className="px-5 pb-5 overflow-x-auto">
                  <table className="w-full text-left border-collapse">
                    <thead>
                      <tr className="border-b border-obsidian-600">
                        <th scope="col" className="font-sans text-xs uppercase tracking-wider text-oatmeal-400 py-2 pr-4">Test</th>
                        <th scope="col" className="font-sans text-xs uppercase tracking-wider text-oatmeal-400 py-2 pr-4">What it does</th>
                        <th scope="col" className="font-sans text-xs uppercase tracking-wider text-oatmeal-400 py-2">Basis</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tool.rules.map(rule => (
                        <tr key={rule.test} className="border-b border-obsidian-700 align-top">
                          <td className="font-sans text-sm text-oatmeal-200 py-3 pr-4 min-w-[10rem]">{rule.test}</td>
                          <td className="font-sans text-sm text-oatmeal-300 py-3 pr-4">
                            {rule.rule}
                            {rule.note && <p className="text-xs text-oatmeal-500 mt-1.5">{rule.note}</p>}
                            {rule.configurable && <p className="text-xs text-sage-400 mt-1.5">You can change this for a run.</p>}
                          </td>
                          <td className="py-3 min-w-[11rem]">
                            <span className={`inline-block font-sans text-[11px] px-2 py-0.5 rounded border ${KIND_LABELS[rule.kind].badge}`}>
                              {KIND_LABELS[rule.kind].label}
                            </span>
                            {rule.sources.length > 0 && (
                              <p className="font-mono text-xs text-oatmeal-300 mt-1.5">{rule.sources.join(', ')}</p>
                            )}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </details>
            ))}
          </div>
        </section>

        <p className="font-sans text-sm text-oatmeal-400 mt-14">
          Think a citation here is wrong or out of date? <Link href="/contact" className="text-sage-400 hover:text-sage-300 underline">Tell us</Link>{' '}
          and we will check it against the source and correct it.
        </p>
      </div>
    </main>
  )
}
