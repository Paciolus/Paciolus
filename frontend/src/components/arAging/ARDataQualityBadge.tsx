'use client'

import { DataQualityBadge } from '@/components/shared/testing/DataQualityBadge'
import type { ARDataQuality } from '@/types/arAging'

interface ARDataQualityBadgeProps {
  quality: ARDataQuality
}

export function ARDataQualityBadge({ quality }: ARDataQualityBadgeProps) {
  const extraStats = (
    <div className="flex items-center gap-6 mb-4">
      <div>
        <span className="font-mono text-sm text-content-primary">{quality.total_tb_accounts}</span>
        <p className="text-content-tertiary text-[10px] font-sans">TB Accounts</p>
      </div>
      {quality.has_subledger && (
        <div>
          <span className="font-mono text-sm text-content-primary">{quality.total_subledger_entries.toLocaleString()}</span>
          <p className="text-content-tertiary text-[10px] font-sans">Sub-Ledger Entries</p>
        </div>
      )}
    </div>
  )

  return (
    <DataQualityBadge
      completeness_score={quality.completeness_score}
      field_fill_rates={quality.field_fill_rates}
      detected_issues={quality.detected_issues}
      total_rows={quality.has_subledger ? quality.total_subledger_entries : quality.total_tb_accounts}
      entity_label={quality.has_subledger ? 'entries' : 'accounts'}
      header_subtitle={quality.has_subledger ? 'TB + Sub-Ledger' : 'TB Only'}
      extra_stats={extraStats}
    />
  )
}
