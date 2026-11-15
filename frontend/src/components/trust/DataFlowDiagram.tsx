import { SHARE_RETENTION } from '@/content/storage-statement'

/**
 * DataFlowDiagram — Sprint 862 (WEBSITE_REVIEW.md S-02).
 *
 * The two paths customer data can take, drawn as numbered stages with hairline
 * arrows so a reader can cite them ("stage B2"). Static: no motion, no glow.
 * Built in HTML rather than an SVG image so it reflows on small screens and
 * screen readers read it as two ordered lists.
 *
 * Facts (re-check before editing): the preview cache is 10 minutes
 * (`backend/shared/preflight_cache.py`); share retention is per plan
 * (`backend/routes/export_sharing.py`).
 */

interface Stage {
  ref: string
  title: string
  detail: string
}

const UPLOAD_PATH: Stage[] = [
  { ref: 'A1', title: 'Upload', detail: 'Your file is sent to us over HTTPS.' },
  { ref: 'A2', title: 'Processed in memory', detail: 'A previewed PDF or workbook can stay in memory for up to 10 minutes so the tool can reuse it.' },
  { ref: 'A3', title: 'Results returned', detail: 'Results go to your browser; a summary is saved to your history.' },
  { ref: 'A4', title: 'Uploaded file discarded', detail: 'The file is not saved to our database or file storage.' },
]

const SHARE_PATH: Stage[] = [
  { ref: 'B1', title: 'Share link created', detail: 'Professional and Enterprise plans, only when you choose to share a report.' },
  { ref: 'B2', title: 'Report stored', detail: `The complete file is stored with our storage provider for ${SHARE_RETENTION.replace(', then deleted', '')}.` },
  { ref: 'B3', title: 'Deleted', detail: 'The file is deleted when the link expires.' },
]

function Path({ label, accent, stages }: { label: string; accent: 'sage' | 'oatmeal'; stages: Stage[] }) {
  const rule = accent === 'sage' ? 'border-sage-500' : 'border-oatmeal-400'
  const refColor = accent === 'sage' ? 'text-sage-400' : 'text-oatmeal-300'
  return (
    <div>
      <h3 className="font-serif text-lg text-oatmeal-100 mb-4">{label}</h3>
      <ol className="grid gap-0 md:grid-flow-col md:auto-cols-fr">
        {stages.map((stage, i) => (
          <li key={stage.ref} className="relative flex md:block">
            <div className={`flex-1 border-t-2 ${rule} pt-3 pr-4 pb-6`}>
              <span className={`font-mono text-xs tabular-nums ${refColor}`}>{stage.ref}</span>
              <p className="font-serif text-oatmeal-100 mt-1">{stage.title}</p>
              <p className="font-sans text-sm text-oatmeal-400 mt-1 leading-relaxed">{stage.detail}</p>
            </div>
            {i < stages.length - 1 && (
              <span aria-hidden="true" className={`hidden md:block absolute -top-[0.7rem] right-1 font-mono text-sm ${refColor}`}>→</span>
            )}
          </li>
        ))}
      </ol>
    </div>
  )
}

export function DataFlowDiagram() {
  return (
    <figure className="space-y-10" aria-label="Data flow: what happens to an upload and to a shared report">
      <Path label="A. A file you upload" accent="sage" stages={UPLOAD_PATH} />
      <Path label="B. A report you share by link" accent="oatmeal" stages={SHARE_PATH} />
      <figcaption className="font-sans text-xs text-oatmeal-500 border-t border-obsidian-600 pt-3">
        Separately, your account, client list, analysis summaries and engagement entries are kept in our database, and
        the database is backed up daily (30 daily and 12 monthly copies).
      </figcaption>
    </figure>
  )
}
