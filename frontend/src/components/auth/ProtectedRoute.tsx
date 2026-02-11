'use client'

import { useEffect } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'

interface ProtectedRouteProps {
  children: React.ReactNode
}

/**
 * ProtectedRoute - Day 13
 *
 * Wrapper component that redirects unauthenticated users to /login.
 * Preserves the intended destination for redirect after login.
 *
 * ZERO-STORAGE: Auth state comes from sessionStorage (client-side only).
 */
export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const { isAuthenticated, isLoading } = useAuth()
  const router = useRouter()
  const pathname = usePathname()

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      // Store intended destination for redirect after login
      sessionStorage.setItem('paciolus_redirect', pathname)
      router.push('/login')
    }
  }, [isLoading, isAuthenticated, router, pathname])

  // Show loading state while checking auth
  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-obsidian flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-oatmeal-400 font-sans">Loading your vault...</p>
        </div>
      </div>
    )
  }

  // Don't render children if not authenticated
  if (!isAuthenticated) {
    return null
  }

  return <>{children}</>
}

export default ProtectedRoute
