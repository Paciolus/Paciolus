/**
 * Shared components barrel export
 *
 * Contains reusable components used across multiple feature areas.
 * Sprint 41: Performance Quick Wins - Shared Component Extraction
 * Sprint 81: ToolNav extraction (eliminates 5 duplicated navbars)
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

export { ToolNav, type ToolKey } from './ToolNav'

export { FileDropZone } from './FileDropZone'

export { GuestCTA } from './GuestCTA'
export { ZeroStorageNotice } from './ZeroStorageNotice'
export { DisclaimerBox } from './DisclaimerBox'
export { BrandIcon, type BrandIconName, type IconSize, type IconTone, type IconState } from './BrandIcon'

export {
  SkeletonPage,
  CardGridSkeleton,
  FormSkeleton,
  ListSkeleton,
  UploadZoneSkeleton,
} from './skeletons'

export { ProofSummaryBar, ProofPanel } from './proof'
export type { ProofSummaryBarProps, ProofPanelProps } from './proof'

export { GlobalCommandPalette } from './CommandPalette'

export { ToolStatePresence } from './ToolStatePresence'
export { UpgradeGate } from './UpgradeGate'
