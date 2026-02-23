/**
 * FileQueueList Component - Sprint 39
 *
 * Container for file queue items with animations and empty state.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Display only, no file storage
 */

'use client';

import { AnimatePresence, motion } from 'framer-motion';
import { useBatchUpload } from '@/hooks/useBatchUpload';
import { cx } from '@/utils/themeUtils';
import { FileQueueItem } from './FileQueueItem';

interface FileQueueListProps {
  /** Optional custom class name */
  className?: string;
  /** Maximum height before scrolling */
  maxHeight?: string;
}

/**
 * List of files in the batch queue with status indicators.
 */
export function FileQueueList({ className, maxHeight = '400px' }: FileQueueListProps) {
  const { files, removeFile, isProcessing, stats } = useBatchUpload();

  // Empty state
  if (files.length === 0) {
    return (
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        className={cx(
          'flex flex-col items-center justify-center py-12 px-4',
          'bg-surface-card-secondary/30 rounded-xl border border-dashed border-theme',
          className
        )}
      >
        <div className="w-12 h-12 rounded-full bg-surface-card-secondary/50 flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-content-tertiary" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
        </div>
        <p className="text-content-secondary font-serif text-lg mb-1">No files in queue</p>
        <p className="text-content-disabled text-sm">Drop files above or click to browse</p>
      </motion.div>
    );
  }

  return (
    <div className={cx('space-y-2', className)}>
      {/* Header */}
      <div className="flex items-center justify-between px-1 mb-3">
        <h3 className="font-serif text-content-primary">
          File Queue
          <span className="ml-2 text-sm font-sans text-content-tertiary">
            ({stats.totalFiles} file{stats.totalFiles !== 1 ? 's' : ''})
          </span>
        </h3>
        <div className="flex items-center gap-3 text-xs text-content-tertiary">
          {stats.completedFiles > 0 && (
            <span className="text-sage-400">
              {stats.completedFiles} complete
            </span>
          )}
          {stats.failedFiles > 0 && (
            <span className="text-clay-400">
              {stats.failedFiles} failed
            </span>
          )}
          {stats.readyFiles > 0 && (
            <span>
              {stats.readyFiles} ready
            </span>
          )}
        </div>
      </div>

      {/* Scrollable List */}
      <div
        className="overflow-y-auto scrollbar-thin scrollbar-thumb-oatmeal-300 scrollbar-track-transparent"
        style={{ maxHeight }}
      >
        <AnimatePresence mode="popLayout">
          {files.map((file, index) => (
            <motion.div
              key={file.id}
              layout
              exit={{ opacity: 0, x: 20 }}
              transition={{ type: 'spring' as const, stiffness: 300, damping: 25 }}
              className="mb-2 last:mb-0"
            >
              <FileQueueItem
                file={file}
                index={index}
                onRemove={removeFile}
                removeDisabled={isProcessing}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Summary Footer */}
      {files.length > 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="pt-3 mt-3 border-t border-theme-divider flex items-center justify-between text-sm"
        >
          <span className="text-content-tertiary">
            Total size: <span className="font-mono text-content-secondary">{stats.totalSizeFormatted}</span>
          </span>
          {isProcessing && (
            <span className="flex items-center gap-2 text-content-secondary">
              <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
              Processing...
            </span>
          )}
        </motion.div>
      )}
    </div>
  );
}

export default FileQueueList;
