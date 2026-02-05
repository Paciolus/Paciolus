/**
 * BatchUploadControls Component - Sprint 39
 *
 * Control buttons for batch upload operations.
 * Process All, Clear Queue, Cancel Processing, Retry Failed.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Actions only, no data storage
 */

'use client';

import { useCallback } from 'react';
import { motion } from 'framer-motion';
import { useBatchUpload } from '@/hooks/useBatchUpload';
import { cx } from '@/utils/themeUtils';

interface BatchUploadControlsProps {
  /** Optional custom class name */
  className?: string;
  /** Layout direction */
  direction?: 'horizontal' | 'vertical';
  /** Button size */
  size?: 'sm' | 'md' | 'lg';
}

/**
 * Button component with Oat & Obsidian styling
 */
interface ButtonProps {
  onClick: () => void;
  disabled?: boolean;
  variant: 'primary' | 'secondary' | 'danger';
  size: 'sm' | 'md' | 'lg';
  loading?: boolean;
  children: React.ReactNode;
}

function Button({ onClick, disabled, variant, size, loading, children }: ButtonProps) {
  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-sm',
    lg: 'px-6 py-3 text-base',
  };

  const variantClasses = {
    primary: cx(
      'bg-sage-600 hover:bg-sage-500 text-white',
      'disabled:bg-obsidian-600 disabled:text-obsidian-400'
    ),
    secondary: cx(
      'bg-obsidian-700 hover:bg-obsidian-600 text-oatmeal-300',
      'border border-obsidian-500',
      'disabled:bg-obsidian-800 disabled:text-obsidian-500 disabled:border-obsidian-600'
    ),
    danger: cx(
      'bg-clay-600/20 hover:bg-clay-600/30 text-clay-400',
      'border border-clay-500/30',
      'disabled:bg-obsidian-800 disabled:text-obsidian-500 disabled:border-obsidian-600'
    ),
  };

  return (
    <motion.button
      onClick={onClick}
      disabled={disabled || loading}
      className={cx(
        'inline-flex items-center justify-center gap-2 rounded-lg font-medium',
        'transition-all duration-200',
        'disabled:cursor-not-allowed',
        sizeClasses[size],
        variantClasses[variant]
      )}
      whileHover={disabled ? undefined : { scale: 1.02 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
    >
      {loading && (
        <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
        </svg>
      )}
      {children}
    </motion.button>
  );
}

/**
 * Control buttons for batch upload operations.
 */
export function BatchUploadControls({
  className,
  direction = 'horizontal',
  size = 'md',
}: BatchUploadControlsProps) {
  const {
    processAll,
    clearQueue,
    cancelProcessing,
    retryFailed,
    canProcess,
    hasFailedFiles,
    hasFiles,
    isProcessing,
  } = useBatchUpload();

  const handleProcessAll = useCallback(async () => {
    try {
      await processAll();
    } catch (error) {
      console.error('Batch processing failed:', error);
    }
  }, [processAll]);

  const handleRetryFailed = useCallback(async () => {
    try {
      await retryFailed();
    } catch (error) {
      console.error('Retry failed:', error);
    }
  }, [retryFailed]);

  // Don't show if no files
  if (!hasFiles) {
    return null;
  }

  return (
    <div
      className={cx(
        'flex gap-3',
        direction === 'vertical' ? 'flex-col' : 'flex-row flex-wrap',
        className
      )}
    >
      {/* Process All */}
      {!isProcessing && canProcess && (
        <Button
          onClick={handleProcessAll}
          variant="primary"
          size={size}
          disabled={!canProcess}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          Process All
        </Button>
      )}

      {/* Cancel Processing */}
      {isProcessing && (
        <Button
          onClick={cancelProcessing}
          variant="danger"
          size={size}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 10a1 1 0 011-1h4a1 1 0 011 1v4a1 1 0 01-1 1h-4a1 1 0 01-1-1v-4z" />
          </svg>
          Cancel
        </Button>
      )}

      {/* Retry Failed */}
      {hasFailedFiles && !isProcessing && (
        <Button
          onClick={handleRetryFailed}
          variant="secondary"
          size={size}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Retry Failed
        </Button>
      )}

      {/* Clear Queue */}
      {!isProcessing && (
        <Button
          onClick={clearQueue}
          variant="secondary"
          size={size}
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
          Clear Queue
        </Button>
      )}
    </div>
  );
}

export default BatchUploadControls;
