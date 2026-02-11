'use client'

import { DataQualityBadge } from '@/components/shared/testing/DataQualityBadge'
import type { PayrollDataQuality } from '@/types/payrollTesting'

interface PayrollDataQualityBadgeProps {
  quality: PayrollDataQuality
}

export function PayrollDataQualityBadge({ quality }: PayrollDataQualityBadgeProps) {
  return (
    <DataQualityBadge
      completeness_score={quality.completeness_score}
      field_fill_rates={quality.field_fill_rates}
      detected_issues={quality.detected_issues}
      total_rows={quality.total_rows}
      entity_label="payroll entries"
    />
  )
}
