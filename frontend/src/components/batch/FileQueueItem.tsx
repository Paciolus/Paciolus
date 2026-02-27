/**
 * FileQueueItem Component - Sprint 39
 *
 * Individual file row in the batch queue.
 * Shows file info, status badge, progress bar, and remove action.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display only, no file storage
 */

'use client';

import { memo, useCallback } from 'react';
import { motion } from 'framer-motion';
import { type FileQueueItem as FileQueueItemType, type FileStatus, formatFileSize } from '@/types/batch';
import { cx, getBadgeClasses, type BadgeVariant } from '@/utils/themeUtils';

interface FileQueueItemProps {
  /** The file queue item to display */
  file: FileQueueItemType;
  /** Animation index for stagger */
  index: number;
  /** Called when remove button is clicked */
  onRemove: (fileId: string) => void;
  /** Whether removal is disabled (e.g., during processing) */
  removeDisabled?: boolean;
}

/**
 * Map file status to badge variant
 */
function getStatusBadgeVariant(status: FileStatus): BadgeVariant {
  switch (status) {
    case 'completed':
      return 'success';
    case 'error':
      return 'error';
    case 'processing':
    case 'validating':
      return 'warning';
    case 'cancelled':
      return 'neutral';
    case 'ready':
      return 'info';
    case 'pending':
    default:
      return 'neutral';
  }
}

/**
 * Get human-readable status label
 */
function getStatusLabel(status: FileStatus): string {
  switch (status) {
    case 'pending':
      return 'Pending';
    case 'validating':
      return 'Validating';
    case 'ready':
      return 'Ready';
    case 'processing':
      return 'Processing';
    case 'completed':
      return 'Complete';
    case 'error':
      return 'Error';
    case 'cancelled':
      return 'Cancelled';
    default:
      return 'Unknown';
  }
}

/**
 * Get file type icon based on MIME type
 */
function getFileIcon(mimeType: string, fileName: string) {
  const isExcel = mimeType.includes('spreadsheet') || mimeType.includes('excel') ||
    fileName.endsWith('.xlsx') || fileName.endsWith('.xls');

  if (isExcel) {
    return (
      <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 17V7m0 10a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2h2a2 2 0 012 2m0 10a2 2 0 002 2h2a2 2 0 002-2M9 7a2 2 0 012-2h2a2 2 0 012 2m0 10V7m0 10a2 2 0 002 2h2a2 2 0 002-2V7a2 2 0 00-2-2h-2a2 2 0 00-2 2" />
      </svg>
    );
  }

  // CSV icon
  return (
    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
    </svg>
  );
}

/**
 * Individual file in the batch queue with status and progress.
 */
export const FileQueueItem = memo(function FileQueueItem({
  file,
  index,
  onRemove,
  removeDisabled = false,
}: FileQueueItemProps) {
  const handleRemove = useCallback(() => {
    if (!removeDisabled) {
      onRemove(file.id);
    }
  }, [file.id, onRemove, removeDisabled]);

  const isProcessing = file.status === 'processing' || file.status === 'validating';
  const canRemove = !removeDisabled && file.status !== 'processing';
  const showProgress = file.status === 'processing' && file.progress > 0;

  return (
    <motion.div
      initial={{ opacity: 0, x: -20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: 20, height: 0 }}
      transition={{
        type: 'spring',
        stiffness: 300,
        damping: 25,
        delay: index * 0.05,
      }}
      className={cx(
        'group relative p-4 rounded-lg border transition-all duration-200',
        file.status === 'error'
          ? 'bg-clay-500/10 border-clay-500/30'
          : file.status === 'completed'
            ? 'bg-sage-500/10 border-sage-500/30'
            : 'bg-surface-card-secondary/50 border-theme hover:border-oatmeal-400'
      )}
    >
      <div className="flex items-center gap-4">
        {/* File Icon */}
        <div className={cx(
          'flex-shrink-0 w-10 h-10 rounded-lg flex items-center justify-center',
          file.status === 'error'
            ? 'bg-clay-500/10 text-clay-400'
            : file.status === 'completed'
              ? 'bg-sage-500/10 text-sage-400'
              : 'bg-surface-card-secondary text-content-secondary'
        )}>
          {isProcessing ? (
            <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : file.status === 'completed' ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ) : file.status === 'error' ? (
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ) : (
            getFileIcon(file.mimeType, file.fileName)
          )}
        </div>

        {/* File Info */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className="font-mono text-sm text-content-primary truncate">
              {file.fileName}
            </span>
            <span className={cx(
              'inline-flex items-center px-2 py-0.5 rounded-sm text-xs font-medium',
              getBadgeClasses(getStatusBadgeVariant(file.status))
            )}>
              {getStatusLabel(file.status)}
            </span>
          </div>

          <div className="flex items-center gap-3 text-xs text-content-tertiary">
            <span>{formatFileSize(file.fileSize)}</span>
            {file.result?.rowCount !== undefined && (
              <>
                <span className="text-content-disabled">|</span>
                <span>{file.result.rowCount.toLocaleString()} rows</span>
              </>
            )}
            {file.result?.anomalyCount !== undefined && file.result.anomalyCount > 0 && (
              <>
                <span className="text-content-disabled">|</span>
                <span className="text-clay-400">{file.result.anomalyCount} anomalies</span>
              </>
            )}
          </div>

          {/* Error Message */}
          {file.error && (
            <div className="mt-2 text-xs text-clay-400">
              {file.error.message}
              {file.error.details && (
                <span className="text-clay-500"> - {file.error.details}</span>
              )}
            </div>
          )}
        </div>

        {/* Remove Button */}
        <button
          onClick={handleRemove}
          disabled={!canRemove}
          className={cx(
            'flex-shrink-0 p-2 rounded-lg transition-all duration-200',
            canRemove
              ? 'text-content-tertiary hover:text-clay-400 hover:bg-clay-500/10 opacity-0 group-hover:opacity-100'
              : 'text-content-disabled cursor-not-allowed'
          )}
          title={canRemove ? 'Remove file' : 'Cannot remove while processing'}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </button>
      </div>

      {/* Progress Bar */}
      {showProgress && (
        <div className="mt-3">
          <div className="h-1.5 bg-oatmeal-200 rounded-full overflow-hidden">
            <motion.div
              initial={{ scaleX: 0 }}
              animate={{ scaleX: file.progress / 100 }}
              style={{ transformOrigin: 'left' }}
              className="h-full w-full bg-gradient-to-r from-sage-600 to-sage-400 rounded-full"
              transition={{ type: 'spring', stiffness: 100, damping: 20 }}
            />
          </div>
          <div className="mt-1 text-xs text-content-tertiary text-right">
            {file.progress}%
          </div>
        </div>
      )}
    </motion.div>
  );
});

export default FileQueueItem;
