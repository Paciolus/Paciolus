'use client'

/**
 * Sprint 890 (CEO brief 15B): the backend's effective upload limits and enabled
 * formats, fetched once per page load from `GET /upload/capabilities`.
 * Until the response arrives the backend's defaults apply.
 */
import { useEffect, useSyncExternalStore } from 'react'
import { apiGet } from '@/utils/apiClient'
import {
  acceptString,
  fileTooLargeMessage,
  formatsLabel,
  getUploadCapabilities,
  isAcceptedFileType,
  setUploadCapabilities,
  sizeLimitLabel,
  subscribeUploadCapabilities,
  type UploadCapabilities,
} from '@/utils/fileFormats'

let inFlight: Promise<void> | null = null

/** Fetch once; later calls share the same request. Exported for tests. */
export function loadUploadCapabilities(): Promise<void> {
  if (!inFlight) {
    inFlight = apiGet<UploadCapabilities>('/upload/capabilities', null)
      .then(res => {
        if (res.ok && res.data && Array.isArray(res.data.formats)) setUploadCapabilities(res.data)
      })
      .catch(() => {
        /* keep the defaults */
      })
  }
  return inFlight
}

/** Test hook: forget the cached request. */
export function resetUploadCapabilitiesForTests(): void {
  inFlight = null
}

export interface UseUploadCapabilitiesReturn {
  capabilities: UploadCapabilities
  /** `<input accept>` value */
  accept: string
  isAccepted: (file: File) => boolean
  formatsLabel: string
  /** e.g. "100 MB" */
  sizeLabel: string
  tooLargeMessage: string
  isTooLarge: (file: File) => boolean
}

export function useUploadCapabilities(): UseUploadCapabilitiesReturn {
  const capabilities = useSyncExternalStore(subscribeUploadCapabilities, getUploadCapabilities, getUploadCapabilities)
  useEffect(() => {
    void loadUploadCapabilities()
  }, [])
  return {
    capabilities,
    accept: acceptString(capabilities),
    isAccepted: (file: File) => isAcceptedFileType(file, capabilities),
    formatsLabel: formatsLabel(capabilities),
    sizeLabel: sizeLimitLabel(capabilities),
    tooLargeMessage: fileTooLargeMessage(capabilities),
    isTooLarge: (file: File) => file.size > capabilities.max_file_size_bytes,
  }
}
