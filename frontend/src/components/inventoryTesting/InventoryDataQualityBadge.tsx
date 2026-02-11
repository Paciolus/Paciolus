'use client'

import { DataQualityBadge } from '@/components/shared/testing/DataQualityBadge'
import type { InvDataQuality } from '@/types/inventoryTesting'

interface InventoryDataQualityBadgeProps {
  quality: InvDataQuality
}

export function InventoryDataQualityBadge({ quality }: InventoryDataQualityBadgeProps) {
  return (
    <DataQualityBadge
      completeness_score={quality.completeness_score}
      field_fill_rates={quality.field_fill_rates}
      detected_issues={quality.detected_issues}
      total_rows={quality.total_rows}
      entity_label="inventory items"
    />
  )
}
