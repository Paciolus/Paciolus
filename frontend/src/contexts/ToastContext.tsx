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
  useMemo,
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

/**
 * Sprint 820: actions and state live in separate contexts. The actions are
 * stable for the provider's lifetime, so the components that only *raise*
 * toasts (pages, upload and export hooks) no longer re-render every time a
 * toast appears or expires — only the container, which reads the list, does.
 */
export interface ToastActions {
  addToast: (toast: Omit<Toast, 'id'>) => void
  removeToast: (id: string) => void
  success: (title: string, description?: string) => void
  error: (title: string, description?: string) => void
  info: (title: string, description?: string) => void
}

const ToastActionsContext = createContext<ToastActions | null>(null)
const ToastStateContext = createContext<Toast[] | null>(null)

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

  const actions = useMemo<ToastActions>(() => ({
    addToast,
    removeToast,
    success: (title, description) => addToast({ type: 'success', title, description }),
    error: (title, description) => addToast({ type: 'error', title, description }),
    info: (title, description) => addToast({ type: 'info', title, description }),
  }), [addToast, removeToast])

  return (
    <ToastActionsContext.Provider value={actions}>
      <ToastStateContext.Provider value={toasts}>
        {children}
      </ToastStateContext.Provider>
    </ToastActionsContext.Provider>
  )
}

/** No-op fallback when used outside ToastProvider (e.g., in tests) */
const NOOP_ACTIONS: ToastActions = {
  addToast: () => {},
  removeToast: () => {},
  success: () => {},
  error: () => {},
  info: () => {},
}
const NO_TOASTS: Toast[] = []

/** Raise toasts. Stable across renders; does not subscribe to the toast list. */
export function useToast(): ToastActions {
  return useContext(ToastActionsContext) ?? NOOP_ACTIONS
}

/** The current toast list — for the container that renders them. */
export function useToastState(): Toast[] {
  return useContext(ToastStateContext) ?? NO_TOASTS
}
