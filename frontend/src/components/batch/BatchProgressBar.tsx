/**
 * BatchProgressBar Component - Sprint 39
 *
 * Overall batch progress visualization with animated progress bar.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display only, no data storage
 */

'use client';

import { motion } from 'framer-motion';
import { useBatchUpload } from '@/hooks/useBatchUpload';
import { cx } from '@/utils/themeUtils';

interface BatchProgressBarProps {
  /** Optional custom class name */
  className?: string;
  /** Whether to show detailed stats */
  showDetails?: boolean;
}

/**
 * Get status color based on batch status
 */
function getProgressColor(status: string): string {
  switch (status) {
    case 'completed':
      return 'from-sage-600 to-sage-400';
    case 'failed':
      return 'from-clay-600 to-clay-400';
    case 'partial':
      return 'from-oatmeal-600 to-oatmeal-400';
    case 'processing':
    case 'validating':
      return 'from-sage-600 via-sage-500 to-sage-400';
    default:
      return 'from-oatmeal-400 to-oatmeal-300';
  }
}

/**
 * Overall batch progress visualization.
 */
export function BatchProgressBar({ className, showDetails = true }: BatchProgressBarProps) {
  const { status, overallProgress, stats, getStatusLabel } = useBatchUpload();

  const statusLabel = getStatusLabel(status);
  const progressColor = getProgressColor(status);
  const isActive = status === 'processing' || status === 'validating';

  // Don't show if no files
  if (stats.totalFiles === 0) {
    return null;
  }

  return (
    <div className={cx('space-y-3', className)}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="font-serif text-content-primary">{statusLabel}</span>
          {isActive && (
            <svg className="w-4 h-4 animate-spin text-sage-400" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          )}
        </div>
        <span className="font-mono text-sm text-content-secondary">
          {overallProgress}%
        </span>
      </div>

      {/* Progress Bar */}
      <div className="relative h-3 bg-oatmeal-200 rounded-full overflow-hidden">
        <motion.div
          initial={{ scaleX: 0 }}
          animate={{ scaleX: overallProgress / 100 }}
          style={{ transformOrigin: 'left' }}
          className={cx(
            'h-full w-full rounded-full bg-gradient-to-r',
            progressColor
          )}
          transition={{ type: 'spring', stiffness: 100, damping: 20 }}
        />
        {isActive && (
          <motion.div
            className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent"
            animate={{ x: ['-100%', '100%'] }}
            transition={{
              duration: 1.5,
              repeat: Infinity,
              ease: 'linear',
            }}
          />
        )}
      </div>

      {/* Details */}
      {showDetails && (
        <div className="flex items-center justify-between text-xs text-content-tertiary">
          <div className="flex items-center gap-4">
            {stats.completedFiles > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-sage-500" />
                <span className="text-sage-400">{stats.completedFiles}</span>
                <span>complete</span>
              </span>
            )}
            {stats.processingFiles > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-oatmeal-500 animate-pulse" />
                <span className="text-content-secondary">{stats.processingFiles}</span>
                <span>processing</span>
              </span>
            )}
            {stats.failedFiles > 0 && (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-clay-500" />
                <span className="text-clay-400">{stats.failedFiles}</span>
                <span>failed</span>
              </span>
            )}
            {stats.readyFiles > 0 && status !== 'processing' && (
              <span className="flex items-center gap-1">
                <span className="w-2 h-2 rounded-full bg-oatmeal-400" />
                <span>{stats.readyFiles}</span>
                <span>ready</span>
              </span>
            )}
          </div>
          <span>
            {stats.completedFiles} / {stats.totalFiles} files
          </span>
        </div>
      )}
    </div>
  );
}

export default BatchProgressBar;
