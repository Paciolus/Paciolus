import type { SplitSearchDisclosure } from '@/types/bankRec'

/**
 * Sprint 833: the split-match search (one bank item to 2–4 ledger items) is
 * bounded — a Paciolus convention, not an auditing-standard requirement.
 * Always shown so the bound is visible; emphasised when open bank items were
 * not searched exhaustively. Those items remain open reconciling items.
 */
export function SplitSearchNotice({ disclosure }: { disclosure: SplitSearchDisclosure }) {
  const limited = disclosure.limited_count > 0
  return (
    <div
      role="note"
      className={`border rounded-xl p-4 mb-4 ${limited ? 'bg-clay-50 border-clay-200' : 'bg-oatmeal-100 border-theme'}`}
    >
      <p className={`text-sm font-sans font-medium ${limited ? 'text-clay-700' : 'text-content-primary'}`}>
        {limited
          ? `Split matching was limited for ${disclosure.limited_count} open bank item${disclosure.limited_count === 1 ? '' : 's'}`
          : 'Split matching search bounds'}
      </p>
      <p className="text-xs font-sans text-content-secondary mt-1">{disclosure.note}</p>
    </div>
  )
}
