'use client'

/**
 * EmptyState — Sprint 397: Phase LV
 *
 * Context-aware empty state for the command palette.
 * Shows relevant suggestions based on current pathname.
 */

import { usePathname } from 'next/navigation'

interface EmptyStateProps {
  query: string
}

export function EmptyState({ query }: EmptyStateProps) {
  const pathname = usePathname()

  let suggestion = 'Try "tools", "settings", or a client name'
  if (pathname.startsWith('/tools')) {
    suggestion = 'Try searching for a tool name or "export"'
  } else if (pathname === '/portfolio' || pathname === '/engagements') {
    suggestion = 'Try a client name or "new workspace"'
  }

  return (
    <div className="px-4 py-8 text-center">
      <p className="text-sm font-sans text-oatmeal-400">
        {query ? 'No results found' : 'No commands available'}
      </p>
      <p className="text-[10px] font-sans text-oatmeal-500 mt-1">
        {suggestion}
      </p>
    </div>
  )
}
