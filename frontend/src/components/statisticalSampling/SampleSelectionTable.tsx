'use client'

import { motion } from 'framer-motion'
import type { SamplingDesignResult } from '@/types/statisticalSampling'
import { SAMPLING_METHOD_LABELS } from '@/types/statisticalSampling'

interface SampleSelectionTableProps {
  result: SamplingDesignResult
  onExportCSV: () => void
  onExportMemo: () => void
  exporting: boolean
}

export function SampleSelectionTable({ result, onExportCSV, onExportMemo, exporting }: SampleSelectionTableProps) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="space-y-6"
    >
      {/* Summary Metrics */}
      <div className="theme-card rounded-2xl p-6">
        <h3 className="font-serif text-lg text-content-primary mb-4">Design Summary</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <MetricCard label="Population Size" value={result.population_size.toLocaleString()} />
          <MetricCard label="Population Value" value={`$${result.population_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          <MetricCard label="Sample Size" value={result.actual_sample_size.toLocaleString()} />
          <MetricCard label="Method" value={result.method === 'mus' ? 'MUS' : 'Random'} />
          <MetricCard label="Confidence" value={`${(result.confidence_level * 100).toFixed(0)}%`} />
          <MetricCard label="Tolerable" value={`$${result.tolerable_misstatement.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          {result.sampling_interval != null && (
            <MetricCard label="Interval" value={`$${result.sampling_interval.toLocaleString(undefined, { minimumFractionDigits: 2 })}`} />
          )}
          {result.high_value_count > 0 && (
            <MetricCard label="High-Value Items" value={result.high_value_count.toLocaleString()} />
          )}
        </div>
      </div>

      {/* Strata Summary */}
      {result.strata_summary.length > 0 && (
        <div className="theme-card rounded-2xl p-6">
          <h3 className="font-serif text-lg text-content-primary mb-4">Stratification</h3>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-theme">
                  <th className="text-left py-2 font-sans text-content-secondary font-medium">Stratum</th>
                  <th className="text-left py-2 font-sans text-content-secondary font-medium">Threshold</th>
                  <th className="text-right py-2 font-sans text-content-secondary font-medium">Count</th>
                  <th className="text-right py-2 font-sans text-content-secondary font-medium">Value</th>
                  <th className="text-right py-2 font-sans text-content-secondary font-medium">Sample</th>
                </tr>
              </thead>
              <tbody>
                {result.strata_summary.map((s, i) => (
                  <tr key={i} className="border-b border-theme/50">
                    <td className="py-2 font-sans text-content-primary">{s.stratum}</td>
                    <td className="py-2 font-sans text-content-secondary">{s.threshold}</td>
                    <td className="py-2 font-mono text-content-primary text-right">{s.count.toLocaleString()}</td>
                    <td className="py-2 font-mono text-content-primary text-right">${s.total_value.toLocaleString(undefined, { minimumFractionDigits: 2 })}</td>
                    <td className="py-2 font-mono text-content-primary text-right">{s.sample_size.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Selected Items */}
      <div className="theme-card rounded-2xl p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="font-serif text-lg text-content-primary">
            Selected Items ({result.actual_sample_size})
          </h3>
          <div className="flex gap-2">
            <button
              onClick={onExportCSV}
              disabled={exporting}
              className="btn-secondary text-xs px-3 py-1.5"
            >
              {exporting ? 'Exporting...' : 'Download CSV'}
            </button>
            <button
              onClick={onExportMemo}
              disabled={exporting}
              className="btn-secondary text-xs px-3 py-1.5"
            >
              {exporting ? 'Exporting...' : 'Export Memo'}
            </button>
          </div>
        </div>

        <div className="overflow-x-auto max-h-96 overflow-y-auto">
          <table className="w-full text-sm">
            <thead className="sticky top-0 bg-surface-card">
              <tr className="border-b border-theme">
                <th className="text-left py-2 font-sans text-content-secondary font-medium">Row</th>
                <th className="text-left py-2 font-sans text-content-secondary font-medium">ID</th>
                <th className="text-left py-2 font-sans text-content-secondary font-medium">Description</th>
                <th className="text-right py-2 font-sans text-content-secondary font-medium">Amount</th>
                <th className="text-left py-2 font-sans text-content-secondary font-medium">Method</th>
              </tr>
            </thead>
            <tbody>
              {result.selected_items.slice(0, 100).map((item, i) => (
                <tr key={i} className="border-b border-theme/30 hover:bg-surface-card-secondary/50">
                  <td className="py-1.5 font-mono text-content-tertiary text-xs">{item.row_index}</td>
                  <td className="py-1.5 font-mono text-content-primary text-xs">{item.item_id}</td>
                  <td className="py-1.5 font-sans text-content-secondary text-xs max-w-xs truncate">{item.description}</td>
                  <td className="py-1.5 font-mono text-content-primary text-xs text-right">
                    ${item.recorded_amount.toLocaleString(undefined, { minimumFractionDigits: 2 })}
                  </td>
                  <td className="py-1.5">
                    <span className={`inline-block px-2 py-0.5 rounded-full text-xs font-sans ${
                      item.selection_method === 'high_value_100pct'
                        ? 'bg-sage-500/10 text-sage-500'
                        : 'bg-oatmeal-300/20 text-content-secondary'
                    }`}>
                      {item.selection_method === 'high_value_100pct' ? '100%' :
                       item.selection_method === 'mus_interval' ? 'MUS' : 'Random'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
          {result.selected_items.length > 100 && (
            <p className="text-center font-sans text-xs text-content-tertiary py-2">
              Showing first 100 of {result.selected_items.length} items. Download CSV for the full list.
            </p>
          )}
        </div>
      </div>
    </motion.div>
  )
}

function MetricCard({ label, value }: { label: string; value: string }) {
  return (
    <div className="p-3 rounded-xl bg-surface-card-secondary">
      <p className="font-sans text-xs text-content-tertiary mb-1">{label}</p>
      <p className="font-mono text-sm text-content-primary font-medium">{value}</p>
    </div>
  )
}
