import type { Metadata } from 'next'
import { PolicyMarkdown } from '@/components/policy/PolicyMarkdown'
import { DATA_HANDLING_ARCHITECTURE_MD } from '@/content/policies.generated'

/**
 * Data Handling Architecture — Sprint 862. Rendered from docs/04-compliance/ via
 * scripts/sync_policy_docs.py; edit the markdown, not this page.
 */
export const metadata: Metadata = {
  title: 'Data Handling Architecture — Paciolus',
  description: 'What happens to a file you upload, every table that stores your data, how long it is kept, and what deletion removes.',
}

export default function Page() {
  return (
    <main id="main-content" className="relative z-10 min-h-screen bg-obsidian-800 pt-32 pb-24 px-6">
      <article className="max-w-4xl mx-auto">
        <PolicyMarkdown markdown={DATA_HANDLING_ARCHITECTURE_MD} />
      </article>
    </main>
  )
}
