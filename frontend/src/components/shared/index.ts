/**
 * Shared components barrel export
 *
 * Contains reusable components used across multiple feature areas.
 * Sprint 41: Performance Quick Wins - Shared Component Extraction
 * Sprint 81: ToolNav extraction (eliminates 5 duplicated navbars)
 * Sprint 475: ToolNav superseded by AuthenticatedShell / UnifiedToolbar.
 * Sprint 788: ToolNav deleted — it rendered nowhere but carried a stale
 *   12-tool list that read as authoritative. Tool navigation now derives
 *   from UnifiedToolbar/toolbarConfig.ts, checked against content/tool-ledger.ts.
 */

export { SectionHeader, default as SectionHeaderDefault } from './SectionHeader'

export {
  CollapsibleSection,
  default as CollapsibleSectionDefault,
} from './CollapsibleSection'

export {
  EmptyStateCard,
  ChartIcon,
  TrendIcon,
  IndustryIcon,
  RollingIcon,
  default as EmptyStateCardDefault,
} from './EmptyStateCard'


export { FileDropZone } from './FileDropZone'

export { GuestCTA } from './GuestCTA'
export { UnverifiedCTA } from './UnverifiedCTA'
export { ZeroStorageNotice } from './ZeroStorageNotice'
export { DisclaimerBox } from './DisclaimerBox'
export { BrandIcon, type BrandIconName, type IconSize, type IconTone, type IconState } from './BrandIcon'

export {
  SkeletonPage,
  CardGridSkeleton,
  FormSkeleton,
  ListSkeleton,
  UploadZoneSkeleton,
  ToolPageSkeleton,
} from './skeletons'

export { ProofSummaryBar, ProofPanel } from './proof'
export type { ProofSummaryBarProps, ProofPanelProps } from './proof'

export { GlobalCommandPalette } from './CommandPalette'

export { ToolStatePresence } from './ToolStatePresence'
export { UpgradeGate } from './UpgradeGate'
export { UnifiedToolbar } from './UnifiedToolbar'
export { ToolSettingsDrawer, type ToolSettingsKey } from './ToolSettingsDrawer'
export { Citation } from './Citation'
export { CitationFooter } from './CitationFooter'
export { ToastContainer } from './ToastContainer'
export { WelcomeModal } from './WelcomeModal'
export { SavedSettingsNotice } from './SavedSettingsNotice'
