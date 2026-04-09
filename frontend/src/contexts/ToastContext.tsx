'use client'

/**
 * ToastContext — Sprint 582: Global Toast Notification System
 *
 * Provides a global toast notification system. Toast types:
 * - success (sage): file uploads, exports, saves
 * - error (clay): operation failures
 * - info (oatmeal): neutral information
 *
 * Follows Oat & Obsidian design tokens.
 * Zero-Storage: no persistence — toasts are ephemeral UI state.
 */

import {
  createContext,
  useContext,
  useCallback,
  useState,
  type ReactNode,
} from 'react'

export type ToastType = 'success' | 'error' | 'info'

export interface Toast {
  id: string
  type: ToastType
  title: string
  description?: string
  duration?: number
}

interface ToastContextValue {
  toasts: Toast[]
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  success: (title: string, description?: string) => void
  error: (title: string, description?: string) => void
  info: (title: string, description?: string) => void
}

const ToastContext = createContext<ToastContextValue | null>(null)

let toastCounter = 0

export function ToastProvider({ children }: { children: ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([])

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id))
  }, [])

  const addToast = useCallback((toast: Omit<Toast, 'id'>) => {
    const id = `toast-${++toastCounter}`
    const duration = toast.duration ?? (toast.type === 'error' ? 6000 : 4000)
    setToasts(prev => [...prev, { ...toast, id, duration }])
    setTimeout(() => removeToast(id), duration)
  }, [removeToast])

  const success = useCallback((title: string, description?: string) => {
    addToast({ type: 'success', title, description })
  }, [addToast])

  const error = useCallback((title: string, description?: string) => {
    addToast({ type: 'error', title, description })
  }, [addToast])

  const info = useCallback((title: string, description?: string) => {
    addToast({ type: 'info', title, description })
  }, [addToast])

  return (
    <ToastContext.Provider value={{ toasts, addToast, removeToast, success, error, info }}>
      {children}
    </ToastContext.Provider>
  )
}

/** No-op fallback when used outside ToastProvider (e.g., in tests) */
const NOOP_TOAST: ToastContextValue = {
  toasts: [],
  addToast: () => {},
  removeToast: () => {},
  success: () => {},
  error: () => {},
  info: () => {},
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext)
  return ctx ?? NOOP_TOAST
}
