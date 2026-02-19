'use client'

import { motion } from 'framer-motion'
import type { SamplingEvaluationResult } from '@/types/statisticalSampling'
import { SAMPLING_CONCLUSION_COLORS, SAMPLING_CONCLUSION_BG } from '@/types/statisticalSampling'

interface SamplingResultCardProps {
  result: SamplingEvaluationResult
  onExportMemo: () => void
  exporting: boolean
}

export function SamplingResultCard({ result, onExportMemo, exporting }: SamplingResultCardProps) {
  const conclusionColor = SAMPLING_CONCLUSION_COLORS[result.conclusion]
  const conclusionBg = SAMPLING_CONCLUSION_BG[result.conclusion]

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Conclusion Banner */}
      <div className={`rounded-2xl border p-6 text-center ${conclusionBg}`}>
        <h3 className={`font-serif text-2xl font-bold ${conclusionColor}`}>
          {result.conclusion === 'pass' ? 'PASS' : 'FAIL'}
        </h3>
        <p className="font-sans text-sm text-content-secondary mt-2 max-w-2xl mx-auto">
          {result.conclusion_detail}
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="theme-card rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-serif text-lg text-content-primary">Evaluation Summary</h3>
          <button
            onClick={onExportMemo}
            disabled={exporting}
            className="btn-secondary text-xs px-3 py-1.5"
          >
            {exporting ? 'Exporting...' : 'Export Memo'}
          </button>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Errors Found" value={result.errors_found.toString()} highlight={result.errors_found > 0} />
          <MetricCard label="Total Misstatement" value={`$${result.total_misstatement.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          <MetricCard label="Projected Misstatement" value={`$${result.projected_misstatement.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          <MetricCard label="Basic Precision" value={`$${result.basic_precision.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          {result.incremental_allowance > 0 && (
            <MetricCard label="Incremental Allowance" value={`$${result.incremental_allowance.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          )}
          <MetricCard
            label="Upper Error Limit"
            value={`$${result.upper_error_limit.toLocaleString(undefined, { minimumFractionDigits: 2 })}`}
            highlight={result.conclusion === 'fail'}
          />
          <MetricCard label="Tolerable Misstatement" value={`$${result.tolerable_misstatement.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          <MetricCard label="Confidence" value={`${(result.confidence_level * 100).toFixed(0)}%`} />
        </div>
      </div>

      {/* Error Details */}
      {result.errors.length > 0 && (
        <div className="theme-card rounded-2xl p-6">
          <h3 className="font-serif text-lg text-content-primary mb-4">Error Details</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-theme bg-surface-elevated sticky top-0">
                  <th className="text-left py-2 font-sans text-content-secondary font-medium">#</th>
                  <th className="text-left py-2 font-sans text-content-secondary font-medium">Item ID</th>
                  <th className="text-right py-2 font-sans text-content-secondary font-medium">Recorded</th>
                  <th className="text-right py-2 font-sans text-content-secondary font-medium">Audited</th>
                  <th className="text-right py-2 font-sans text-content-secondary font-medium">Misstatement</th>
                  <th className="text-right py-2 font-sans text-content-secondary font-medium">Tainting</th>
                </tr>
              </thead>
              <tbody>
                {result.errors.map((err, i) => (
                  <tr key={i} className="border-b border-theme/30 even:bg-oatmeal-50/50">
                    <td className="py-1.5 font-mono text-content-tertiary text-xs">{i + 1}</td>
                    <td className="py-1.5 font-mono text-content-primary text-xs">{err.item_id}</td>
                    <td className="py-1.5 font-mono text-content-primary text-xs text-right">
                      ${err.recorded_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-1.5 font-mono text-content-primary text-xs text-right">
                      ${err.audited_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-1.5 font-mono text-clay-500 text-xs text-right">
                      ${err.misstatement.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                    </td>
                    <td className="py-1.5 font-mono text-content-secondary text-xs text-right">
                      {(err.tainting * 100).toFixed(1)}%
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </motion.div>
  )
}

function MetricCard({ label, value, highlight = false }: { label: string; value: string; highlight?: boolean }) {
  return (
    <div className={`card-inset p-3 border-l-4 ${highlight ? 'border-l-clay-500' : 'border-l-oatmeal-300'}`}>
      <p className="font-sans text-xs text-content-tertiary mb-1">{label}</p>
      <p className={`font-mono text-sm font-medium text-right ${highlight ? 'text-clay-500' : 'text-content-primary'}`}>
        {value}
      </p>
    </div>
  )
}
