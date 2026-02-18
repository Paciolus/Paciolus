'use client';

import { motion } from 'framer-motion';
import type { ConvergenceResponse } from '@/types/engagement';
import { TOOL_NAME_LABELS } from '@/types/engagement';
import type { ToolName } from '@/types/engagement';

interface ConvergenceTableProps {
  data: ConvergenceResponse;
  onExportCsv: () => void;
  isExporting?: boolean;
}

/**
 * Cross-Tool Account Convergence Index — Sprint 288
 *
 * Displays accounts flagged by multiple diagnostic tools within an engagement.
 * Convergence count indicates how many tools flagged each account.
 *
 * Guardrails:
 * - NO composite score, NO risk classification — raw convergence count only
 * - Non-dismissible disclaimer (Guardrail 5)
 * - Oat & Obsidian palette only
 */
export function ConvergenceTable({ data, onExportCsv, isExporting = false }: ConvergenceTableProps) {
  if (data.items.length === 0) {
    return (
      <div className="space-y-4">
        <ConvergenceDisclaimer />
        <div className="text-center py-12 bg-surface-card-secondary rounded-xl border border-theme">
          <svg className="w-12 h-12 mx-auto text-content-tertiary mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-content-tertiary font-sans text-sm">
            No convergence data available. Run diagnostic tools within this workspace to see cross-tool account convergence.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      <ConvergenceDisclaimer />

      {/* Header with export */}
      <div className="flex items-center justify-between">
        <p className="text-sm font-sans text-content-secondary">
          {data.total_accounts} account{data.total_accounts === 1 ? '' : 's'} flagged across tools
        </p>
        <button
          onClick={onExportCsv}
          disabled={isExporting}
          className="inline-flex items-center gap-2 px-4 py-2 text-sm font-sans text-content-secondary hover:text-content-primary border border-theme hover:border-sage-200 rounded-lg transition-colors disabled:opacity-50"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          {isExporting ? 'Exporting...' : 'Export CSV'}
        </button>
      </div>

      {/* Table */}
      <motion.div
        initial={{ opacity: 0, y: 8 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, type: 'tween' as const }}
        className="bg-surface-card rounded-xl border border-theme overflow-hidden shadow-theme-card"
      >
        <div className="overflow-x-auto">
          <table className="w-full text-left" role="table">
            <thead>
              <tr className="border-b border-theme bg-surface-card-secondary">
                <th className="px-4 py-3 text-xs font-sans font-semibold text-content-tertiary uppercase tracking-wider">
                  Account
                </th>
                <th className="px-4 py-3 text-xs font-sans font-semibold text-content-tertiary uppercase tracking-wider text-center w-32">
                  Convergence Count
                </th>
                <th className="px-4 py-3 text-xs font-sans font-semibold text-content-tertiary uppercase tracking-wider">
                  Tools
                </th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((item, i) => (
                <tr
                  key={item.account}
                  className={`border-b border-theme last:border-b-0 ${i % 2 === 0 ? '' : 'bg-surface-card-secondary/50'}`}
                >
                  <td className="px-4 py-3 font-mono text-sm text-content-primary">
                    {item.account}
                  </td>
                  <td className="px-4 py-3 text-center">
                    <ConvergenceCountBadge count={item.convergence_count} />
                  </td>
                  <td className="px-4 py-3">
                    <div className="flex flex-wrap gap-1.5">
                      {item.tools_flagging_it.map((tool) => (
                        <span
                          key={tool}
                          className="inline-flex items-center px-2 py-0.5 rounded text-xs font-sans bg-oatmeal-100 text-oatmeal-700 border border-oatmeal-200"
                        >
                          {TOOL_NAME_LABELS[tool as ToolName] ?? tool}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </motion.div>
    </div>
  );
}

function ConvergenceCountBadge({ count }: { count: number }) {
  let colorClasses: string;

  if (count >= 3) {
    colorClasses = 'bg-clay-50 text-clay-700 border-clay-200';
  } else if (count === 2) {
    colorClasses = 'bg-oatmeal-100 text-oatmeal-700 border-oatmeal-300';
  } else {
    colorClasses = 'bg-surface-card-secondary text-content-secondary border-theme';
  }

  return (
    <span className={`inline-flex items-center justify-center min-w-[28px] px-2 py-0.5 rounded-full text-xs font-mono font-semibold border ${colorClasses}`}>
      {count}
    </span>
  );
}

function ConvergenceDisclaimer() {
  return (
    <div className="p-3 bg-oatmeal-100 border border-oatmeal-300 rounded-xl">
      <p className="text-xs font-sans text-oatmeal-700 leading-relaxed">
        <span className="font-semibold">Cross-Tool Convergence Index &mdash; Informational Only.</span>{' '}
        Convergence counts indicate how many diagnostic tools flagged an account.
        This is NOT a risk score or risk classification. The practitioner is solely
        responsible for evaluating significance and determining appropriate procedures.
      </p>
    </div>
  );
}
