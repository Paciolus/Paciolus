'use client'

// Sprint 861: the hard-coded "simulated" test results were removed — this
// page showed them to the public as a live "25/25 Passed". It now shows only
// the live health check.

import { useState, useEffect } from 'react'
import { apiGet } from '@/utils/apiClient'
import { API_URL } from '@/utils/constants'

interface HealthStatus {
  status: string
  timestamp: string
  version: string
}

export default function StatusPage() {
  const [health, setHealth] = useState<HealthStatus | null>(null)
  const [healthError, setHealthError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const checkHealth = async () => {
      if (!API_URL) {
        setHealthError('API URL not configured')
        setLoading(false)
        return
      }

      try {
        const response = await apiGet<HealthStatus>('/health', null, { skipCache: true })
        if (response.ok && response.data) {
          setHealth(response.data)
        } else {
          setHealthError('Backend unavailable')
        }
      } catch (error) {
        setHealthError('Cannot connect to backend')
      } finally {
        setLoading(false)
      }
    }

    checkHealth()
    // Refresh every 30 seconds
    const interval = setInterval(checkHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  return (
    <main id="main-content" className="min-h-screen bg-surface-page py-12 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-serif font-bold text-content-primary mb-2">System Health</h1>
          <p className="text-content-secondary font-sans">Paciolus backend status</p>
        </div>

        {/* Backend Health Card */}
 <div className="theme-card rounded-2xl p-6 mb-8">
          <h2 className="text-xl font-serif font-semibold text-content-primary mb-4 flex items-center gap-2">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
            </svg>
            Backend Status
          </h2>

          {loading ? (
            <div className="flex items-center gap-2 text-content-secondary font-sans">
              <div className="w-4 h-4 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin"></div>
              Checking...
            </div>
          ) : health ? (
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-3 h-3 bg-sage-500 rounded-full animate-pulse"></div>
                <span className="text-sage-600 font-sans font-medium">Healthy</span>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm font-sans">
                <div>
                  <span className="text-content-secondary">Version:</span>
                  <span className="text-content-primary ml-2 font-mono">{health.version}</span>
                </div>
                <div>
                  <span className="text-content-secondary">Last Check:</span>
                  <span className="text-content-primary ml-2 font-mono">
                    {new Date(health.timestamp).toLocaleTimeString()}
                  </span>
                </div>
              </div>
            </div>
          ) : (
            <div className="flex items-center gap-3">
              <div className="w-3 h-3 bg-clay-500 rounded-full"></div>
              <span className="text-clay-600 font-sans font-medium">{healthError}</span>
            </div>
          )}
        </div>

        {/* Back Link */}
        <div className="mt-8 text-center">
          <a
            href="/"
            className="text-sage-600 hover:text-sage-700 text-sm font-sans font-medium transition-colors"
          >
            ← Back to Home
          </a>
        </div>
      </div>
    </main>
  )
}
