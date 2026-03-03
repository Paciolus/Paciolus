'use client'

import { getCitation } from '@/lib/citations'

interface CitationFooterProps {
  standards: string[]
}

/**
 * Footer section listing all standards cited on a page,
 * with official and free links.
 */
export function CitationFooter({ standards }: CitationFooterProps) {
  const citations = standards
    .map((code) => getCitation(code))
    .filter((c): c is NonNullable<typeof c> => c != null)

  if (citations.length === 0) return null

  return (
    <div className="mt-8 pt-6 border-t border-theme">
      <h3 className="font-serif text-xs text-content-secondary uppercase tracking-wider mb-3">
        Standards Referenced
      </h3>
      <ul className="space-y-2">
        {citations.map((citation) => (
          <li key={citation.code} className="flex flex-col gap-0.5">
            <div className="flex items-baseline gap-2">
              <span className="font-mono text-xs text-content-primary font-medium">
                {citation.code}
              </span>
              <span className="font-sans text-xs text-content-secondary">
                {citation.fullName}
              </span>
            </div>
            <div className="flex items-center gap-3 pl-0">
              <a
                href={citation.officialUrl}
                target="_blank"
                rel="noopener noreferrer"
                className="font-sans text-[11px] text-sage-600 hover:text-sage-700 underline"
              >
                {citation.officialNote}
              </a>
              {citation.freeUrl && (
                <a
                  href={citation.freeUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="font-sans text-[11px] text-sage-600 hover:text-sage-700 underline"
                >
                  {citation.freeNote}
                </a>
              )}
            </div>
          </li>
        ))}
      </ul>
    </div>
  )
}
