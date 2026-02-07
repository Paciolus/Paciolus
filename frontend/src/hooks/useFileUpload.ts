import { useState, useCallback, useRef } from 'react'

/**
 * Shared hook for file drag-and-drop + file input selection.
 *
 * Eliminates duplicated drag/drop handlers across tool pages.
 * Sprint 81: Extracted from JE Testing, AP Testing, Trial Balance.
 *
 * @param onFileSelected - Callback when a file is selected (drop or input)
 */
export function useFileUpload(onFileSelected: (file: File) => void) {
  const [isDragging, setIsDragging] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const file = e.dataTransfer.files[0]
    if (file) onFileSelected(file)
  }, [onFileSelected])

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }, [])

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
  }, [])

  const handleFileSelect = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) onFileSelected(file)
  }, [onFileSelected])

  const resetFileInput = useCallback(() => {
    if (fileInputRef.current) fileInputRef.current.value = ''
  }, [])

  return {
    isDragging,
    fileInputRef,
    handleDrop,
    handleDragOver,
    handleDragLeave,
    handleFileSelect,
    resetFileInput,
  }
}

export type UseFileUploadReturn = ReturnType<typeof useFileUpload>
