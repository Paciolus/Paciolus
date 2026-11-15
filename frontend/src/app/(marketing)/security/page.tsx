import type { Metadata } from 'next'
import { PolicyMarkdown } from '@/components/policy/PolicyMarkdown'
import { SECURITY_POLICY_MD } from '@/content/policies.generated'

/**
 * Security Policy — Sprint 862. Rendered from docs/04-compliance/ via
 * scripts/sync_policy_docs.py; edit the markdown, not this page.
 */
export const metadata: Metadata = {
  title: 'Security Policy — Paciolus',
  description: 'What is in place to protect your data, stated so you can rely on every sentence: certifications we do not hold, controls, backups and incident handling.',
}

export default function Page() {
  return (
    <main id="main-content" className="relative z-10 min-h-screen bg-obsidian-800 pt-32 pb-24 px-6">
      <article className="max-w-4xl mx-auto">
        <PolicyMarkdown markdown={SECURITY_POLICY_MD} />
      </article>
    </main>
  )
}
