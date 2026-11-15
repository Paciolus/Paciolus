import { RESPONSIBILITY_STATEMENT, STORAGE_STATEMENT, UPLOAD_HANDLING } from '@/content/storage-statement'

/**
 * FeaturePillars — "What You Get" (Sprint 861 copy, Sprint 864 layout).
 *
 * Three numbered rows on hairline rules, set like a workpaper index — no icon
 * cards, hover lifts, gradient overlays or clip-path reveals
 * (WEBSITE_REVIEW.md G-02, G-06, G-07). Copy states only what can be shown.
 */

interface Pillar {
  ref: string
  title: string
  tagline: string
  description: string
}

const pillars: Pillar[] = [
  {
    ref: '1',
    title: 'Uploads Not Kept',
    tagline: 'Processed in memory.',
    description: `${STORAGE_STATEMENT} The Trust page lists exactly what.`,
  },
  {
    ref: '2',
    title: 'Your Materiality, Your Thresholds',
    tagline: 'Set per engagement.',
    description:
      'You set materiality for each engagement. Where a tool lets you change a threshold for a run, the Sources page says so, and every default Paciolus sets is marked there as our own convention.',
  },
  {
    ref: '3',
    title: 'PDF Memos and Excel Workpapers',
    tagline: 'For your review.',
    description: `PDF memos cite the rule behind each test; Excel and CSV exports hold the results. ${RESPONSIBILITY_STATEMENT}`,
  },
]

export function FeaturePillars() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <span className="block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
          Why Paciolus
        </span>
        <h2 className="font-serif text-3xl sm:text-4xl font-bold text-oatmeal-100 mb-4">
          What You Get
        </h2>
        <p className="font-sans text-lg text-oatmeal-400 max-w-2xl mb-12">
          {UPLOAD_HANDLING} The conclusions you draw from the results are yours.
        </p>

        <ol className="border-t border-obsidian-500/60">
          {pillars.map(pillar => (
            <li
              key={pillar.ref}
              className="grid grid-cols-[2.5rem_minmax(0,1fr)] md:grid-cols-[2.5rem_minmax(0,18rem)_minmax(0,1fr)] gap-x-6 gap-y-2 py-6 border-b border-obsidian-500/60"
            >
              <span className="font-mono text-sm text-sage-400 tabular-nums pt-1">{pillar.ref}.</span>
              <div>
                <h3 className="font-serif text-xl font-semibold text-oatmeal-100">{pillar.title}</h3>
                <p className="font-sans text-sm font-medium text-sage-400 mt-1">{pillar.tagline}</p>
              </div>
              <p className="col-start-2 md:col-start-3 font-sans text-sm text-oatmeal-400 leading-relaxed">
                {pillar.description}
              </p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

export default FeaturePillars
