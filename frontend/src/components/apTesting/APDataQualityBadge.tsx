'use client'

import { DataQualityBadge } from '@/components/shared/testing/DataQualityBadge'
import type { APDataQuality } from '@/types/apTesting'

interface APDataQualityBadgeProps {
  quality: APDataQuality
}

export function APDataQualityBadge({ quality }: APDataQualityBadgeProps) {
  return (
    <DataQualityBadge
      completeness_score={quality.completeness_score}
      field_fill_rates={quality.field_fill_rates}
      detected_issues={quality.detected_issues}
      total_rows={quality.total_rows}
      entity_label="payments"
    />
  )
}
