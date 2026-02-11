'use client'

import { DataQualityBadge } from '@/components/shared/testing/DataQualityBadge'
import type { FADataQuality } from '@/types/fixedAssetTesting'

interface FixedAssetDataQualityBadgeProps {
  quality: FADataQuality
}

export function FixedAssetDataQualityBadge({ quality }: FixedAssetDataQualityBadgeProps) {
  return (
    <DataQualityBadge
      completeness_score={quality.completeness_score}
      field_fill_rates={quality.field_fill_rates}
      detected_issues={quality.detected_issues}
      total_rows={quality.total_rows}
      entity_label="fixed asset entries"
    />
  )
}
