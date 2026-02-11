'use client';

import { motion } from 'framer-motion';
import { CONTAINER_VARIANTS, createCardStaggerVariants } from '@/utils/themeUtils';
import type { WorkpaperIndex as WorkpaperIndexType, WorkpaperEntry } from '@/types/engagement';
import { DISPOSITION_LABELS, FollowUpDisposition } from '@/types/engagement';

interface WorkpaperIndexProps {
  index: WorkpaperIndexType;
}

function StatusBadge({ status }: { status: 'completed' | 'not_started' }) {
  if (status === 'completed') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-sans bg-sage-50 text-sage-700 border border-sage-200">
        Completed
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-sans bg-oatmeal-100 text-content-tertiary border border-theme">
      Not Started
    </span>
  );
}

export function WorkpaperIndex({ index }: WorkpaperIndexProps) {
  const completedTools = index.document_register.filter(e => e.status === 'completed').length;
  const totalTools = index.document_register.length;

  return (
    <div className="space-y-8">
      {/* Header */}
 <div className="theme-card p-6">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-4">
          <div>
            <h3 className="font-serif font-semibold text-content-primary text-lg">
              Workpaper Index
            </h3>
            <p className="text-xs font-sans text-content-tertiary mt-1">
              {index.client_name} &mdash;{' '}
              <span className="font-mono">
                {new Date(index.period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                {' \u2013 '}
                {new Date(index.period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
              </span>
            </p>
          </div>
          <div className="text-right">
            <p className="text-xs font-sans text-content-tertiary">Tools Completed</p>
            <p className="text-lg font-mono font-semibold text-content-primary">
              {completedTools} / {totalTools}
            </p>
          </div>
        </div>

        <p className="text-xs font-sans text-content-tertiary">
          Generated: {new Date(index.generated_at).toLocaleString('en-US', { dateStyle: 'medium', timeStyle: 'short' })}
        </p>
      </div>

      {/* Document Register */}
      <div>
        <h4 className="font-serif font-semibold text-content-primary mb-4">Document Register</h4>
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-sans">
            <thead>
              <tr className="border-b border-theme">
                <th className="text-left py-2 px-3 text-content-tertiary font-medium">Tool</th>
                <th className="text-left py-2 px-3 text-content-tertiary font-medium">Status</th>
                <th className="text-left py-2 px-3 text-content-tertiary font-medium">Runs</th>
                <th className="text-left py-2 px-3 text-content-tertiary font-medium">Last Run</th>
                <th className="text-left py-2 px-3 text-content-tertiary font-medium">Lead Sheet Ref</th>
              </tr>
            </thead>
            <tbody>
              {index.document_register.map((entry, i) => (
                <motion.tr
                  key={entry.tool_name}
                  initial={{ opacity: 0, y: 10 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ delay: i * 0.04 }}
                  className="border-b border-theme-divider"
                >
                  <td className="py-2.5 px-3 text-content-secondary font-medium">{entry.tool_label}</td>
                  <td className="py-2.5 px-3"><StatusBadge status={entry.status} /></td>
                  <td className="py-2.5 px-3 text-content-secondary font-mono">{entry.run_count}</td>
                  <td className="py-2.5 px-3 text-content-tertiary font-mono text-xs">
                    {entry.last_run_date
                      ? new Date(entry.last_run_date).toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
                      : '\u2014'}
                  </td>
                  <td className="py-2.5 px-3 text-content-tertiary text-xs">
                    {entry.lead_sheet_refs.join(', ')}
                  </td>
                </motion.tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* Follow-Up Summary */}
      {index.follow_up_summary.total_count > 0 && (
        <div>
          <h4 className="font-serif font-semibold text-content-primary mb-4">Follow-Up Summary</h4>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
            {/* By Severity */}
            <div className="bg-surface-card-secondary rounded-xl border border-theme p-4">
              <p className="text-xs font-sans text-content-tertiary mb-2">By Severity</p>
              <div className="space-y-1.5">
                {Object.entries(index.follow_up_summary.by_severity).map(([sev, count]) => (
                  <div key={sev} className="flex justify-between items-center">
                    <span className="text-sm font-sans text-content-secondary capitalize">{sev}</span>
                    <span className="text-sm font-mono text-content-primary">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* By Disposition */}
            <div className="bg-surface-card-secondary rounded-xl border border-theme p-4">
              <p className="text-xs font-sans text-content-tertiary mb-2">By Disposition</p>
              <div className="space-y-1.5">
                {Object.entries(index.follow_up_summary.by_disposition).map(([disp, count]) => (
                  <div key={disp} className="flex justify-between items-center">
                    <span className="text-sm font-sans text-content-secondary">
                      {DISPOSITION_LABELS[disp as FollowUpDisposition] || disp}
                    </span>
                    <span className="text-sm font-mono text-content-primary">{count}</span>
                  </div>
                ))}
              </div>
            </div>

            {/* By Tool Source */}
            <div className="bg-surface-card-secondary rounded-xl border border-theme p-4">
              <p className="text-xs font-sans text-content-tertiary mb-2">By Tool</p>
              <div className="space-y-1.5">
                {Object.entries(index.follow_up_summary.by_tool_source).map(([src, count]) => (
                  <div key={src} className="flex justify-between items-center">
                    <span className="text-sm font-sans text-content-secondary">{src}</span>
                    <span className="text-sm font-mono text-content-primary">{count}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Auditor Sign-Off (BLANK by design) */}
      <div className="bg-surface-card-secondary rounded-xl border border-theme p-6">
        <h4 className="font-serif font-semibold text-content-primary mb-4">Sign-Off</h4>
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div>
            <label className="block text-xs font-sans text-content-tertiary mb-1">Prepared By</label>
            <div className="h-8 border-b border-theme" />
          </div>
          <div>
            <label className="block text-xs font-sans text-content-tertiary mb-1">Reviewed By</label>
            <div className="h-8 border-b border-theme" />
          </div>
          <div>
            <label className="block text-xs font-sans text-content-tertiary mb-1">Date</label>
            <div className="h-8 border-b border-theme" />
          </div>
        </div>
      </div>
    </div>
  );
}
