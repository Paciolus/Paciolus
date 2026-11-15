/**
 * ProcessTimeline — "How It Works" (Sprint 861 copy, Sprint 864 layout).
 *
 * Three numbered steps on hairline rules. The icon tiles, glow shadows,
 * spin-in number badges, count-ups and drawn connector lines were removed
 * (reports/website-review-2026-11-14.md G-02, G-06, G-07); the step numbers are static.
 */

interface ProcessStep {
  id: string
  number: string
  title: string
  description: string
  detail: string
}

const steps: ProcessStep[] = [
  {
    id: 'upload',
    number: '01',
    title: 'Upload',
    description: 'Raw trial balance data',
    detail: 'Ten formats: CSV, Excel (.xlsx/.xls), TSV, TXT, QBO, OFX, IIF, PDF and ODS. Multi-sheet workbooks supported.',
  },
  {
    id: 'analyze',
    number: '02',
    title: 'Analyze',
    description: 'Tests run on your file',
    detail: 'Accounts are classified by keyword rules, then each tool runs its tests and flags items for your review.',
  },
  {
    id: 'export',
    number: '03',
    title: 'Export',
    description: 'Memos and workpapers',
    detail: 'PDF memos and Excel/CSV workpapers for your review. Your firm keeps them in its own documentation system. Custom branding on Enterprise.',
  },
]

export function ProcessTimeline() {
  return (
    <section className="py-24 px-6">
      <div className="max-w-5xl mx-auto">
        <span className="block font-sans text-xs uppercase tracking-[0.2em] text-sage-400 mb-3">
          How It Works
        </span>
        <h2 className="font-serif text-3xl sm:text-4xl font-bold text-oatmeal-100 mb-4">
          From Your File to Flagged Items and Exports
        </h2>
        <p className="font-sans text-lg text-oatmeal-400 max-w-2xl mb-12">
          Upload your source document. Paciolus runs the tests and gives you the items to review and the exports to keep.
        </p>

        <ol className="grid md:grid-cols-3 gap-x-8">
          {steps.map(step => (
            <li key={step.id} className="border-t-2 border-sage-500/70 pt-4 pb-8">
              <span className="font-mono text-sm text-sage-400 tabular-nums">{step.number}</span>
              <h3 className="font-serif text-xl font-semibold text-oatmeal-100 mt-1">{step.title}</h3>
              <p className="font-sans text-sm font-medium text-sage-400 mt-1 mb-3">{step.description}</p>
              <p className="font-sans text-sm text-oatmeal-400 leading-relaxed">{step.detail}</p>
            </li>
          ))}
        </ol>
      </div>
    </section>
  )
}

export default ProcessTimeline
