'use client';

/**
 * BatchUploadContext - Sprint 38
 *
 * React Context for managing multi-file batch uploads.
 * Provides centralized state management for file queue operations.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - All file data stored in React state (memory only)
 * - Files are processed individually via API
 * - No persistence to localStorage/sessionStorage
 * - Queue cleared on unmount or page refresh
 */

import {
  createContext,
  useContext,
  useReducer,
  useCallback,
  type ReactNode,
} from 'react';
import { useAuth } from '@/context/AuthContext';
import {
  type FileQueueItem,
  type FileStatus,
  type FileError,
  type BatchStatus,
  type BatchUploadContextType,
  type FileProcessingResult,
  FILE_ERROR_CODES,
  FILE_SIZE_LIMITS,
  createFileQueueItem,
  validateFile,
  calculateBatchProgress,
  determineBatchStatus,
} from '@/types/batch';

// =============================================================================
// State and Actions
// =============================================================================

interface BatchState {
  files: FileQueueItem[];
  isProcessing: boolean;
  abortController: AbortController | null;
}

type BatchAction =
  | { type: 'ADD_FILES'; payload: { files: FileQueueItem[] } }
  | { type: 'REMOVE_FILE'; payload: { fileId: string } }
  | { type: 'CLEAR_QUEUE' }
  | { type: 'UPDATE_FILE_STATUS'; payload: { fileId: string; status: FileStatus; error?: FileError } }
  | { type: 'UPDATE_FILE_PROGRESS'; payload: { fileId: string; progress: number } }
  | { type: 'UPDATE_FILE_RESULT'; payload: { fileId: string; result: FileProcessingResult } }
  | { type: 'START_PROCESSING'; payload: { abortController: AbortController } }
  | { type: 'STOP_PROCESSING' }
  | { type: 'SET_FILE_STARTED'; payload: { fileId: string } }
  | { type: 'SET_FILE_COMPLETED'; payload: { fileId: string } };

function batchReducer(state: BatchState, action: BatchAction): BatchState {
  switch (action.type) {
    case 'ADD_FILES': {
      // Check max files limit
      const newTotal = state.files.length + action.payload.files.length;
      if (newTotal > FILE_SIZE_LIMITS.MAX_FILES) {
        // Only add files up to the limit
        const remaining = FILE_SIZE_LIMITS.MAX_FILES - state.files.length;
        return {
          ...state,
          files: [...state.files, ...action.payload.files.slice(0, remaining)],
        };
      }
      return {
        ...state,
        files: [...state.files, ...action.payload.files],
      };
    }

    case 'REMOVE_FILE':
      return {
        ...state,
        files: state.files.filter(f => f.id !== action.payload.fileId),
      };

    case 'CLEAR_QUEUE':
      return {
        ...state,
        files: [],
        isProcessing: false,
        abortController: null,
      };

    case 'UPDATE_FILE_STATUS':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.payload.fileId
            ? { ...f, status: action.payload.status, error: action.payload.error }
            : f
        ),
      };

    case 'UPDATE_FILE_PROGRESS':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.payload.fileId
            ? { ...f, progress: action.payload.progress }
            : f
        ),
      };

    case 'UPDATE_FILE_RESULT':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.payload.fileId
            ? { ...f, result: action.payload.result }
            : f
        ),
      };

    case 'START_PROCESSING':
      return {
        ...state,
        isProcessing: true,
        abortController: action.payload.abortController,
      };

    case 'STOP_PROCESSING':
      return {
        ...state,
        isProcessing: false,
        abortController: null,
      };

    case 'SET_FILE_STARTED':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.payload.fileId
            ? { ...f, startedAt: new Date() }
            : f
        ),
      };

    case 'SET_FILE_COMPLETED':
      return {
        ...state,
        files: state.files.map(f =>
          f.id === action.payload.fileId
            ? { ...f, completedAt: new Date() }
            : f
        ),
      };

    default:
      return state;
  }
}

// =============================================================================
// Context
// =============================================================================

const BatchUploadContext = createContext<BatchUploadContextType | null>(null);

interface BatchUploadProviderProps {
  children: ReactNode;
}

export function BatchUploadProvider({ children }: BatchUploadProviderProps) {
  const { token } = useAuth();

  const [state, dispatch] = useReducer(batchReducer, {
    files: [],
    isProcessing: false,
    abortController: null,
  });

  // Calculate derived state
  const status: BatchStatus = determineBatchStatus(state.files);
  const totalFiles = state.files.length;
  const completedFiles = state.files.filter(f => f.status === 'completed').length;
  const failedFiles = state.files.filter(f => f.status === 'error').length;
  const overallProgress = calculateBatchProgress(state.files);

  // =============================================================================
  // Actions
  // =============================================================================

  const addFiles = useCallback((files: File[], clientId?: number) => {
    const queueItems: FileQueueItem[] = [];

    for (const file of files) {
      const item = createFileQueueItem(file, clientId);

      // Validate file
      const error = validateFile(file);
      if (error) {
        item.status = 'error';
        item.error = error;
      } else {
        item.status = 'ready';
      }

      queueItems.push(item);
    }

    dispatch({ type: 'ADD_FILES', payload: { files: queueItems } });
  }, []);

  const removeFile = useCallback((fileId: string) => {
    dispatch({ type: 'REMOVE_FILE', payload: { fileId } });
  }, []);

  const clearQueue = useCallback(() => {
    // Cancel any in-progress processing
    if (state.abortController) {
      state.abortController.abort();
    }
    dispatch({ type: 'CLEAR_QUEUE' });
  }, [state.abortController]);

  const updateFileStatus = useCallback((
    fileId: string,
    status: FileStatus,
    error?: FileError
  ) => {
    dispatch({ type: 'UPDATE_FILE_STATUS', payload: { fileId, status, error } });
  }, []);

  const updateFileProgress = useCallback((fileId: string, progress: number) => {
    dispatch({ type: 'UPDATE_FILE_PROGRESS', payload: { fileId, progress } });
  }, []);

  const processFile = useCallback(async (fileId: string) => {
    const file = state.files.find(f => f.id === fileId);
    if (!file || file.status !== 'ready') return;

    if (!token) {
      updateFileStatus(fileId, 'error', {
        code: FILE_ERROR_CODES.AUTH_ERROR,
        message: 'Authentication required',
      });
      return;
    }

    // Update status to processing
    updateFileStatus(fileId, 'processing');
    dispatch({ type: 'SET_FILE_STARTED', payload: { fileId } });
    updateFileProgress(fileId, 10);

    try {
      // Create form data for upload
      const formData = new FormData();
      formData.append('file', file.file);
      if (file.clientId) {
        formData.append('client_id', file.clientId.toString());
      }

      // Make API request
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiUrl}/audit/trial-balance`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
        },
        body: formData,
      });

      updateFileProgress(fileId, 50);

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new Error(errorData.detail || `HTTP ${response.status}`);
      }

      const result = await response.json();
      updateFileProgress(fileId, 90);

      // Update with result
      const processingResult: FileProcessingResult = {
        success: true,
        rowCount: result.total_rows || 0,
        anomalyCount: result.abnormal_balances?.length || 0,
        message: `Processed ${result.total_rows || 0} rows`,
        auditData: result,
      };

      dispatch({ type: 'UPDATE_FILE_RESULT', payload: { fileId, result: processingResult } });
      updateFileStatus(fileId, 'completed');
      updateFileProgress(fileId, 100);
      dispatch({ type: 'SET_FILE_COMPLETED', payload: { fileId } });

    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Processing failed';
      updateFileStatus(fileId, 'error', {
        code: FILE_ERROR_CODES.PROCESSING_FAILED,
        message: 'Processing failed',
        details: errorMessage,
      });
      updateFileProgress(fileId, 0);
    }
  }, [state.files, token, updateFileStatus, updateFileProgress]);

  const processAll = useCallback(async () => {
    const readyFiles = state.files.filter(f => f.status === 'ready');
    if (readyFiles.length === 0) return;

    const abortController = new AbortController();
    dispatch({ type: 'START_PROCESSING', payload: { abortController } });

    try {
      // Process files sequentially to avoid overwhelming the server
      for (const file of readyFiles) {
        if (abortController.signal.aborted) {
          // Mark remaining files as cancelled
          updateFileStatus(file.id, 'cancelled', {
            code: FILE_ERROR_CODES.CANCELLED,
            message: 'Cancelled by user',
          });
          continue;
        }

        await processFile(file.id);
      }
    } finally {
      dispatch({ type: 'STOP_PROCESSING' });
    }
  }, [state.files, processFile, updateFileStatus]);

  const cancelProcessing = useCallback(() => {
    if (state.abortController) {
      state.abortController.abort();
    }
    dispatch({ type: 'STOP_PROCESSING' });

    // Mark processing files as cancelled
    state.files
      .filter(f => f.status === 'processing')
      .forEach(f => {
        updateFileStatus(f.id, 'cancelled', {
          code: FILE_ERROR_CODES.CANCELLED,
          message: 'Cancelled by user',
        });
      });
  }, [state.abortController, state.files, updateFileStatus]);

  const retryFailed = useCallback(async () => {
    // Reset failed files to ready
    state.files
      .filter(f => f.status === 'error' || f.status === 'cancelled')
      .forEach(f => {
        // Re-validate in case it was a validation error
        const error = validateFile(f.file);
        if (error) {
          updateFileStatus(f.id, 'error', error);
        } else {
          updateFileStatus(f.id, 'ready');
          updateFileProgress(f.id, 0);
        }
      });

    // Process all ready files
    await processAll();
  }, [state.files, updateFileStatus, updateFileProgress, processAll]);

  // =============================================================================
  // Context Value
  // =============================================================================

  const contextValue: BatchUploadContextType = {
    // State
    files: state.files,
    status,
    totalFiles,
    completedFiles,
    failedFiles,
    isProcessing: state.isProcessing,
    overallProgress,
    // Actions
    addFiles,
    removeFile,
    clearQueue,
    processAll,
    processFile,
    cancelProcessing,
    retryFailed,
    updateFileStatus,
    updateFileProgress,
  };

  return (
    <BatchUploadContext.Provider value={contextValue}>
      {children}
    </BatchUploadContext.Provider>
  );
}

// =============================================================================
// Hook
// =============================================================================

export function useBatchUploadContext(): BatchUploadContextType {
  const context = useContext(BatchUploadContext);
  if (!context) {
    throw new Error('useBatchUploadContext must be used within a BatchUploadProvider');
  }
  return context;
}

export default BatchUploadContext;
