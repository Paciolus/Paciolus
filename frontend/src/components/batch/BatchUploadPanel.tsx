/**
 * BatchUploadPanel Component - Sprint 39
 *
 * Composite component combining all batch upload UI elements.
 * Drop zone, file queue, progress bar, and controls.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - All files in React state (memory only)
 * - No persistence to localStorage/sessionStorage
 */

'use client';

import { motion } from 'framer-motion';
import { BatchUploadProvider } from '@/contexts/BatchUploadContext';
import { BatchDropZone } from './BatchDropZone';
import { FileQueueList } from './FileQueueList';
import { BatchProgressBar } from './BatchProgressBar';
import { BatchUploadControls } from './BatchUploadControls';
import { cx } from '@/utils/themeUtils';

interface BatchUploadPanelProps {
  /** Optional client ID to associate with uploaded files */
  clientId?: number;
  /** Optional custom class name */
  className?: string;
  /** Title to display above the panel */
  title?: string;
  /** Description text */
  description?: string;
}

/**
 * Inner panel content (requires BatchUploadProvider context)
 */
function BatchUploadPanelContent({
  clientId,
  title = 'Batch Upload',
  description = 'Upload multiple trial balance files for batch processing.',
}: Omit<BatchUploadPanelProps, 'className'>) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="font-serif text-2xl text-oatmeal-100">{title}</h2>
        <p className="text-oatmeal-500 mt-1">{description}</p>
      </div>

      {/* Drop Zone */}
      <BatchDropZone clientId={clientId} />

      {/* Progress Bar */}
      <BatchProgressBar />

      {/* File Queue */}
      <FileQueueList maxHeight="350px" />

      {/* Controls */}
      <BatchUploadControls size="md" />

      {/* Zero-Storage Notice */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.5 }}
        className="flex items-start gap-3 p-4 bg-obsidian-800/30 rounded-lg border border-obsidian-700"
      >
        <svg className="w-5 h-5 text-sage-500 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
        <div>
          <p className="text-sm text-oatmeal-300 font-medium">Zero-Storage Processing</p>
          <p className="text-xs text-oatmeal-500 mt-1">
            Files are processed in memory only. No file data is stored on our servers.
            Queue is cleared when you leave this page.
          </p>
        </div>
      </motion.div>
    </div>
  );
}

/**
 * Complete batch upload panel with context provider.
 *
 * Usage:
 * ```tsx
 * <BatchUploadPanel
 *   clientId={123}
 *   title="Upload Trial Balances"
 *   description="Batch process multiple files at once"
 * />
 * ```
 */
export function BatchUploadPanel({ className, ...props }: BatchUploadPanelProps) {
  return (
    <BatchUploadProvider>
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className={cx(
          'p-6 bg-obsidian-900 rounded-2xl border border-obsidian-700',
          className
        )}
      >
        <BatchUploadPanelContent {...props} />
      </motion.div>
    </BatchUploadProvider>
  );
}

export default BatchUploadPanel;
