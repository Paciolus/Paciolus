import type { Metadata } from 'next'
import { PolicyMarkdown } from '@/components/policy/PolicyMarkdown'
import { SUBPROCESSOR_LIST_MD } from '@/content/policies.generated'

/**
 * Subprocessor List — Sprint 862. Rendered from docs/04-compliance/ via
 * scripts/sync_policy_docs.py; edit the markdown, not this page.
 */
export const metadata: Metadata = {
  title: 'Subprocessor List — Paciolus',
  description: 'The third parties that process data for Paciolus, what each one processes, and where.',
}

export default function Page() {
  return (
    <main id="main-content" className="relative z-10 min-h-screen bg-obsidian-800 pt-32 pb-24 px-6">
      <article className="max-w-4xl mx-auto">
        <PolicyMarkdown markdown={SUBPROCESSOR_LIST_MD} />
      </article>
    </main>
  )
}
