import Link from 'next/link'
import { STORAGE_DETAIL_HREF, STORAGE_DETAIL_LABEL, STORAGE_STATEMENT } from '@/content/storage-statement'

interface UploadHandlingNoticeProps {
  className?: string
}

/**
 * UploadHandlingNotice — Lock icon + the approved storage statement.
 *
 * Sprint 861: renamed from DataHandlingNotice (the retired term kept being
 * copied forward) and now shows both halves of the CEO-approved wording.
 *
 * Sprint 841: says only what is true of uploads and links to the Trust page's
 * list of what is kept (the old wording read as a promise about
 * all data).
 *
 * Displayed below upload zones on all tool pages.
 * Standardizes the icon color to the semantic success token.
 *
 * Sprint 239: Extracted from 11 duplicated inline blocks.
 */
export function UploadHandlingNotice({ className = '' }: UploadHandlingNoticeProps) {
  return (
    <div className={`flex items-center justify-center gap-2 ${className}`}>
      <svg className="w-4 h-4 text-theme-success-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
      <span className="font-sans text-xs text-content-tertiary">
        {STORAGE_STATEMENT}{' '}
        <Link href={STORAGE_DETAIL_HREF} className="underline hover:text-content-secondary">
          {STORAGE_DETAIL_LABEL}
        </Link>
      </span>
    </div>
  )
}
