/**
 * useBatchUpload Hook - Sprint 38
 *
 * Convenient hook for batch file upload operations.
 * Wraps BatchUploadContext with additional helpers and derived state.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - All file data in React state (memory only)
 * - No persistence to localStorage/sessionStorage
 */

'use client';

import { useCallback, useMemo } from 'react';
import { useBatchUploadContext } from '@/contexts/BatchUploadContext';
import {
  type FileQueueItem,
  type FileStatus,
  type BatchStatus,
  FILE_SIZE_LIMITS,
  formatFileSize,
} from '@/types/batch';

/**
 * Statistics about the current batch
 */
export interface BatchStats {
  totalFiles: number;
  pendingFiles: number;
  readyFiles: number;
  processingFiles: number;
  completedFiles: number;
  failedFiles: number;
  cancelledFiles: number;
  totalSize: number;
  totalSizeFormatted: string;
  remainingSlots: number;
  canAddMore: boolean;
}

/**
 * Hook return type
 */
export interface UseBatchUploadReturn {
  // State
  files: FileQueueItem[];
  status: BatchStatus;
  isProcessing: boolean;
  overallProgress: number;
  stats: BatchStats;

  // Derived state
  hasFiles: boolean;
  hasReadyFiles: boolean;
  hasFailedFiles: boolean;
  canProcess: boolean;
  isEmpty: boolean;

  // Actions
  addFiles: (files: File[], clientId?: number) => void;
  removeFile: (fileId: string) => void;
  clearQueue: () => void;
  processAll: () => Promise<void>;
  processFile: (fileId: string) => Promise<void>;
  cancelProcessing: () => void;
  retryFailed: () => Promise<void>;

  // Helpers
  getFileById: (fileId: string) => FileQueueItem | undefined;
  getFilesByStatus: (status: FileStatus) => FileQueueItem[];
  getStatusLabel: (status: BatchStatus) => string;
  getFileStatusLabel: (status: FileStatus) => string;
}

/**
 * Get human-readable label for batch status
 */
function getBatchStatusLabel(status: BatchStatus): string {
  switch (status) {
    case 'idle':
      return 'No files';
    case 'queued':
      return 'Ready to process';
    case 'validating':
      return 'Validating...';
    case 'processing':
      return 'Processing...';
    case 'completed':
      return 'All complete';
    case 'partial':
      return 'Partially complete';
    case 'failed':
      return 'All failed';
    default:
      return 'Unknown';
  }
}

/**
 * Get human-readable label for file status
 */
function getFileStatusLabel(status: FileStatus): string {
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
 * Hook for batch file upload operations.
 *
 * Usage:
 * ```tsx
 * const {
 *   files,
 *   status,
 *   isProcessing,
 *   stats,
 *   addFiles,
 *   processAll,
 *   clearQueue,
 * } = useBatchUpload();
 *
 * // Add files from input
 * const handleFileSelect = (e: ChangeEvent<HTMLInputElement>) => {
 *   if (e.target.files) {
 *     addFiles(Array.from(e.target.files));
 *   }
 * };
 *
 * // Process all ready files
 * const handleProcess = async () => {
 *   await processAll();
 * };
 * ```
 */
export function useBatchUpload(): UseBatchUploadReturn {
  const context = useBatchUploadContext();

  const { files } = context;

  // Calculate statistics
  const stats = useMemo<BatchStats>(() => {
    const pendingFiles = files.filter(f => f.status === 'pending').length;
    const readyFiles = files.filter(f => f.status === 'ready').length;
    const processingFiles = files.filter(f => f.status === 'processing').length;
    const completedFiles = files.filter(f => f.status === 'completed').length;
    const failedFiles = files.filter(f => f.status === 'error').length;
    const cancelledFiles = files.filter(f => f.status === 'cancelled').length;
    const totalSize = files.reduce((sum, f) => sum + f.fileSize, 0);
    const remainingSlots = Math.max(0, FILE_SIZE_LIMITS.MAX_FILES - files.length);

    return {
      totalFiles: files.length,
      pendingFiles,
      readyFiles,
      processingFiles,
      completedFiles,
      failedFiles,
      cancelledFiles,
      totalSize,
      totalSizeFormatted: formatFileSize(totalSize),
      remainingSlots,
      canAddMore: remainingSlots > 0,
    };
  }, [files]);

  // Derived state
  const hasFiles = files.length > 0;
  const hasReadyFiles = stats.readyFiles > 0;
  const hasFailedFiles = stats.failedFiles > 0;
  const canProcess = hasReadyFiles && !context.isProcessing;
  const isEmpty = files.length === 0;

  // Helpers
  const getFileById = useCallback((fileId: string): FileQueueItem | undefined => {
    return files.find(f => f.id === fileId);
  }, [files]);

  const getFilesByStatus = useCallback((status: FileStatus): FileQueueItem[] => {
    return files.filter(f => f.status === status);
  }, [files]);

  const getStatusLabel = useCallback((status: BatchStatus): string => {
    return getBatchStatusLabel(status);
  }, []);

  const getFileStatusLabelFn = useCallback((status: FileStatus): string => {
    return getFileStatusLabel(status);
  }, []);

  return {
    // State from context
    files,
    status: context.status,
    isProcessing: context.isProcessing,
    overallProgress: context.overallProgress,
    stats,

    // Derived state
    hasFiles,
    hasReadyFiles,
    hasFailedFiles,
    canProcess,
    isEmpty,

    // Actions from context
    addFiles: context.addFiles,
    removeFile: context.removeFile,
    clearQueue: context.clearQueue,
    processAll: context.processAll,
    processFile: context.processFile,
    cancelProcessing: context.cancelProcessing,
    retryFailed: context.retryFailed,

    // Helpers
    getFileById,
    getFilesByStatus,
    getStatusLabel,
    getFileStatusLabel: getFileStatusLabelFn,
  };
}

export default useBatchUpload;
