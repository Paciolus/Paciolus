/**
 * Batch Upload Types - Sprint 38
 *
 * Type definitions for multi-file batch upload infrastructure.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - All file data stored in React state (memory only)
 * - Files are processed individually, never persisted
 * - Queue state is ephemeral (lost on page refresh)
 */

import { isAcceptedFileType as _isAcceptedFileType } from '@/utils/fileFormats'

/**
 * Status of an individual file in the queue
 */
export type FileStatus =
  | 'pending'      // Added to queue, not yet validated
  | 'validating'   // Currently being validated
  | 'ready'        // Validated and ready for processing
  | 'processing'   // Currently being processed/uploaded
  | 'completed'    // Successfully processed
  | 'error'        // Failed with error
  | 'cancelled';   // Cancelled by user

/**
 * Overall batch processing status
 */
export type BatchStatus =
  | 'idle'         // No files in queue
  | 'queued'       // Files in queue, not processing
  | 'validating'   // Validating files
  | 'processing'   // Processing files
  | 'completed'    // All files processed
  | 'partial'      // Some files succeeded, some failed
  | 'failed';      // All files failed

/**
 * Error information for a failed file
 */
export interface FileError {
  code: string;
  message: string;
  details?: string;
}

/**
 * Common error codes for batch processing
 */
export const FILE_ERROR_CODES = {
  INVALID_TYPE: 'INVALID_TYPE',
  FILE_TOO_LARGE: 'FILE_TOO_LARGE',
  VALIDATION_FAILED: 'VALIDATION_FAILED',
  PROCESSING_FAILED: 'PROCESSING_FAILED',
  NETWORK_ERROR: 'NETWORK_ERROR',
  AUTH_ERROR: 'AUTH_ERROR',
  CANCELLED: 'CANCELLED',
} as const;

/**
 * Supported file types for batch upload.
 * Re-exported from fileFormats for backward compatibility.
 */
export { ACCEPTED_FILE_EXTENSIONS_STRING, ACCEPTED_MIME_TYPES, isAcceptedFileType } from '@/utils/fileFormats'

export const SUPPORTED_FILE_TYPES = {
  CSV: 'text/csv',
  TSV: 'text/tab-separated-values',
  TXT: 'text/plain',
  EXCEL_XLSX: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
  EXCEL_XLS: 'application/vnd.ms-excel',
  ODS: 'application/vnd.oasis.opendocument.spreadsheet',
  QBO: 'application/x-ofx',
  OFX: 'application/ofx',
  IIF: 'application/x-iif',
  PDF: 'application/pdf',
} as const;

/**
 * File size limits
 */
export const FILE_SIZE_LIMITS = {
  MAX_FILE_SIZE: 50 * 1024 * 1024,  // 50MB per file
  MAX_BATCH_SIZE: 200 * 1024 * 1024, // 200MB total
  MAX_FILES: 10, // Maximum files in a batch
} as const;

/**
 * Individual file in the upload queue
 */
export interface FileQueueItem {
  /** Unique identifier for this queue item */
  id: string;
  /** Original File object (in-memory only) */
  file: File;
  /** Display name */
  fileName: string;
  /** File size in bytes */
  fileSize: number;
  /** MIME type */
  mimeType: string;
  /** Current status */
  status: FileStatus;
  /** Progress percentage (0-100) */
  progress: number;
  /** Error information if status is 'error' */
  error?: FileError;
  /** Processing result if status is 'completed' */
  result?: FileProcessingResult;
  /** Timestamp when added to queue */
  addedAt: Date;
  /** Timestamp when processing started */
  startedAt?: Date;
  /** Timestamp when processing completed */
  completedAt?: Date;
  /** Client ID to associate with (optional) */
  clientId?: number;
}

/**
 * Result of processing a single file
 */
export interface FileProcessingResult {
  /** Whether processing succeeded */
  success: boolean;
  /** Number of rows processed */
  rowCount?: number;
  /** Number of anomalies found */
  anomalyCount?: number;
  /** Summary message */
  message?: string;
  /** Audit result data (for display) */
  auditData?: unknown;
}

/**
 * Batch upload state
 */
export interface BatchUploadState {
  /** All files in the queue */
  files: FileQueueItem[];
  /** Overall batch status */
  status: BatchStatus;
  /** Total files in queue */
  totalFiles: number;
  /** Number of completed files */
  completedFiles: number;
  /** Number of failed files */
  failedFiles: number;
  /** Whether batch processing is in progress */
  isProcessing: boolean;
  /** Overall progress (0-100) */
  overallProgress: number;
}

/**
 * Actions for batch upload state management
 */
export interface BatchUploadActions {
  /** Add files to the queue */
  addFiles: (files: File[], clientId?: number) => void;
  /** Remove a file from the queue */
  removeFile: (fileId: string) => void;
  /** Clear all files from the queue */
  clearQueue: () => void;
  /** Start processing all ready files */
  processAll: () => Promise<void>;
  /** Process a single file */
  processFile: (fileId: string) => Promise<void>;
  /** Cancel processing */
  cancelProcessing: () => void;
  /** Retry failed files */
  retryFailed: () => Promise<void>;
  /** Update file status */
  updateFileStatus: (fileId: string, status: FileStatus, error?: FileError) => void;
  /** Update file progress */
  updateFileProgress: (fileId: string, progress: number) => void;
}

/**
 * Combined batch upload context type
 */
export interface BatchUploadContextType extends BatchUploadState, BatchUploadActions {}

/**
 * Generate unique ID for queue items
 */
export function generateFileId(): string {
  return `file-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
}

/**
 * Validate file type.
 * Delegates to isAcceptedFileType from fileFormats for centralized logic.
 */
export function isValidFileType(file: File): boolean {
  return _isAcceptedFileType(file);
}

/**
 * Validate file size
 */
export function isValidFileSize(file: File): boolean {
  return file.size <= FILE_SIZE_LIMITS.MAX_FILE_SIZE;
}

/**
 * Get file extension
 */
export function getFileExtension(fileName: string): string {
  const parts = fileName.split('.');
  return parts.length > 1 ? (parts[parts.length - 1] ?? '').toLowerCase() : '';
}

/**
 * Format file size for display
 */
export function formatFileSize(bytes: number): string {
  if (bytes === 0) return '0 B';
  const k = 1024;
  const sizes = ['B', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${sizes[i]}`;
}

/**
 * Create FileQueueItem from File
 */
export function createFileQueueItem(file: File, clientId?: number): FileQueueItem {
  return {
    id: generateFileId(),
    file,
    fileName: file.name,
    fileSize: file.size,
    mimeType: file.type,
    status: 'pending',
    progress: 0,
    addedAt: new Date(),
    clientId,
  };
}

/**
 * Validate file and return error if invalid
 */
export function validateFile(file: File): FileError | null {
  if (!isValidFileType(file)) {
    return {
      code: FILE_ERROR_CODES.INVALID_TYPE,
      message: 'Invalid file type',
      details: `Supported types: CSV, TSV, TXT, XLSX, XLS, ODS, QBO, OFX, IIF, PDF. Got: ${file.type || getFileExtension(file.name)}`,
    };
  }

  if (!isValidFileSize(file)) {
    return {
      code: FILE_ERROR_CODES.FILE_TOO_LARGE,
      message: 'File too large',
      details: `Maximum size: ${formatFileSize(FILE_SIZE_LIMITS.MAX_FILE_SIZE)}. Got: ${formatFileSize(file.size)}`,
    };
  }

  return null;
}

/**
 * Calculate overall batch progress
 */
export function calculateBatchProgress(files: FileQueueItem[]): number {
  if (files.length === 0) return 0;
  const totalProgress = files.reduce((sum, file) => sum + file.progress, 0);
  return Math.round(totalProgress / files.length);
}

/**
 * Determine batch status from file states
 */
export function determineBatchStatus(files: FileQueueItem[]): BatchStatus {
  if (files.length === 0) return 'idle';

  const statuses = files.map(f => f.status);

  if (statuses.every(s => s === 'completed')) return 'completed';
  if (statuses.every(s => s === 'error')) return 'failed';
  if (statuses.some(s => s === 'completed') && statuses.some(s => s === 'error')) return 'partial';
  if (statuses.some(s => s === 'processing')) return 'processing';
  if (statuses.some(s => s === 'validating')) return 'validating';
  if (statuses.some(s => s === 'ready' || s === 'pending')) return 'queued';

  return 'idle';
}
