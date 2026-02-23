/**
 * BatchDropZone Component - Sprint 39
 *
 * Multi-file drop zone for batch uploads.
 * Supports drag-and-drop with file type validation.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Files passed to parent via callback
 * - No local file storage
 */

'use client';

import { useCallback, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useBatchUpload } from '@/hooks/useBatchUpload';
import { isValidFileType, isValidFileSize, formatFileSize, FILE_SIZE_LIMITS } from '@/types/batch';
import { ACCEPTED_FILE_EXTENSIONS_STRING } from '@/utils/fileFormats';
import { cx } from '@/utils/themeUtils';

interface BatchDropZoneProps {
  /** Optional client ID to associate with uploaded files */
  clientId?: number;
  /** Whether the drop zone is disabled */
  disabled?: boolean;
  /** Optional custom class name */
  className?: string;
}

/**
 * Multi-file drop zone with validation and Oat & Obsidian styling.
 */
export function BatchDropZone({ clientId, disabled = false, className }: BatchDropZoneProps) {
  const { addFiles, stats, isProcessing } = useBatchUpload();
  const [isDragging, setIsDragging] = useState(false);
  const [validationErrors, setValidationErrors] = useState<string[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isDisabled = disabled || isProcessing || !stats.canAddMore;

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (!isDisabled) {
      setIsDragging(true);
    }
  }, [isDisabled]);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const validateFiles = useCallback((files: File[]): { valid: File[]; errors: string[] } => {
    const valid: File[] = [];
    const errors: string[] = [];

    for (const file of files) {
      if (!isValidFileType(file)) {
        errors.push(`${file.name}: Invalid file type (use CSV, XLSX, or XLS)`);
        continue;
      }
      if (!isValidFileSize(file)) {
        errors.push(`${file.name}: File too large (max ${formatFileSize(FILE_SIZE_LIMITS.MAX_FILE_SIZE)})`);
        continue;
      }
      valid.push(file);
    }

    // Check total files limit
    const remainingSlots = stats.remainingSlots;
    if (valid.length > remainingSlots) {
      errors.push(`Can only add ${remainingSlots} more file(s) (max ${FILE_SIZE_LIMITS.MAX_FILES})`);
      return { valid: valid.slice(0, remainingSlots), errors };
    }

    return { valid, errors };
  }, [stats.remainingSlots]);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    if (isDisabled) return;

    const droppedFiles = Array.from(e.dataTransfer.files);
    const { valid, errors } = validateFiles(droppedFiles);

    setValidationErrors(errors);
    if (valid.length > 0) {
      addFiles(valid, clientId);
    }

    // Clear errors after 5 seconds
    if (errors.length > 0) {
      setTimeout(() => setValidationErrors([]), 5000);
    }
  }, [isDisabled, validateFiles, addFiles, clientId]);

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || isDisabled) return;

    const selectedFiles = Array.from(e.target.files);
    const { valid, errors } = validateFiles(selectedFiles);

    setValidationErrors(errors);
    if (valid.length > 0) {
      addFiles(valid, clientId);
    }

    // Reset input so same file can be selected again
    e.target.value = '';

    // Clear errors after 5 seconds
    if (errors.length > 0) {
      setTimeout(() => setValidationErrors([]), 5000);
    }
  }, [isDisabled, validateFiles, addFiles, clientId]);

  const handleClick = useCallback(() => {
    if (!isDisabled && fileInputRef.current) {
      fileInputRef.current.click();
    }
  }, [isDisabled]);

  return (
    <div className={cx('relative', className)}>
      {/* Drop Zone */}
      <motion.div
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
        onClick={handleClick}
        className={cx(
          'relative border-2 border-dashed rounded-xl p-8 text-center transition-all duration-200',
          isDisabled
            ? 'border-theme bg-surface-card-secondary/30 cursor-not-allowed opacity-50'
            : isDragging
              ? 'border-sage-500 bg-sage-500/10 scale-[1.02]'
              : 'border-oatmeal-300 bg-surface-card-secondary/50 hover:border-oatmeal-500 hover:bg-surface-card cursor-pointer'
        )}
        animate={{
          scale: isDragging ? 1.02 : 1,
        }}
        transition={{ type: 'spring', stiffness: 300, damping: 25 }}
      >
        {/* Hidden File Input */}
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept={ACCEPTED_FILE_EXTENSIONS_STRING}
          onChange={handleFileSelect}
          className="hidden"
          disabled={isDisabled}
        />

        {/* Icon */}
        <div className={cx(
          'mx-auto w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors',
          isDragging ? 'bg-sage-500/20' : 'bg-surface-card-secondary'
        )}>
          <svg
            className={cx(
              'w-8 h-8 transition-colors',
              isDragging ? 'text-sage-400' : 'text-content-secondary'
            )}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12"
            />
          </svg>
        </div>

        {/* Text */}
        <h3 className="font-serif text-lg text-content-primary mb-2">
          {isDragging ? 'Drop files here' : 'Drop files or click to browse'}
        </h3>
        <p className="text-sm text-content-tertiary mb-3">
          CSV, XLSX, or XLS files up to {formatFileSize(FILE_SIZE_LIMITS.MAX_FILE_SIZE)}
        </p>

        {/* Stats */}
        <div className="flex items-center justify-center gap-4 text-xs text-content-disabled">
          <span>
            {stats.remainingSlots} of {FILE_SIZE_LIMITS.MAX_FILES} slots available
          </span>
          {stats.totalFiles > 0 && (
            <>
              <span className="text-content-disabled">|</span>
              <span>{stats.totalFiles} file(s) queued</span>
            </>
          )}
        </div>

        {/* Processing indicator */}
        {isProcessing && (
          <div className="mt-4 flex items-center justify-center gap-2 text-content-secondary">
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
            <span className="text-sm">Processing...</span>
          </div>
        )}
      </motion.div>

      {/* Validation Errors */}
      <AnimatePresence>
        {validationErrors.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -10 }}
            className="mt-3 p-3 bg-clay-500/10 border border-clay-500/30 rounded-lg"
          >
            <div className="flex items-start gap-2">
              <svg className="w-5 h-5 text-clay-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <ul className="text-sm text-clay-300 space-y-1">
                {validationErrors.map((error, i) => (
                  <li key={i}>{error}</li>
                ))}
              </ul>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

export default BatchDropZone;
