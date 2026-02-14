interface ZeroStorageNoticeProps {
  className?: string
}

/**
 * ZeroStorageNotice — Lock icon + "Zero-Storage" reassurance text.
 *
 * Displayed below upload zones on all tool pages.
 * Standardizes the icon color to the semantic success token.
 *
 * Sprint 239: Extracted from 11 duplicated inline blocks.
 */
export function ZeroStorageNotice({ className = '' }: ZeroStorageNoticeProps) {
  return (
    <div className={`flex items-center justify-center gap-2 ${className}`}>
      <svg className="w-4 h-4 text-theme-success-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
      <span className="font-sans text-xs text-content-tertiary">
        Zero-Storage: Your data is processed in-memory and never saved.
      </span>
    </div>
  )
}
