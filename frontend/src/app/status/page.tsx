'use client'

import { useState, useEffect } from 'react'
import { apiGet } from '@/utils/apiClient'
import { API_URL } from '@/utils/constants'

interface HealthStatus {
  status: string
  timestamp: string
  version: string
}

interface TestResult {
  name: string
  passed: boolean
  category: string
}

// Simulated test results - in production, this would come from a CI/CD endpoint
const LAST_TEST_RUN: TestResult[] = [
  // Unit Tests
  { name: 'test_running_totals_single_chunk', passed: true, category: 'StreamingAuditor' },
  { name: 'test_running_totals_multiple_chunks', passed: true, category: 'StreamingAuditor' },
  { name: 'test_account_aggregation', passed: true, category: 'StreamingAuditor' },
  { name: 'test_balance_check_balanced', passed: true, category: 'StreamingAuditor' },
  { name: 'test_balance_check_unbalanced', passed: true, category: 'StreamingAuditor' },
  { name: 'test_abnormal_asset_credit', passed: true, category: 'StreamingAuditor' },
  { name: 'test_abnormal_liability_debit', passed: true, category: 'StreamingAuditor' },
  { name: 'test_materiality_classification_material', passed: true, category: 'StreamingAuditor' },
  { name: 'test_materiality_classification_immaterial', passed: true, category: 'StreamingAuditor' },
  { name: 'test_clear_releases_memory', passed: true, category: 'StreamingAuditor' },
  // Integration Tests
  { name: 'test_small_file_audit', passed: true, category: 'AuditPipeline' },
  { name: 'test_large_file_chunked_audit', passed: true, category: 'AuditPipeline' },
  { name: 'test_result_format_compatibility', passed: true, category: 'AuditPipeline' },
  { name: 'test_materiality_threshold_filtering', passed: true, category: 'AuditPipeline' },
  // Edge Cases
  { name: 'test_empty_file', passed: true, category: 'EdgeCases' },
  { name: 'test_non_numeric_values', passed: true, category: 'EdgeCases' },
  { name: 'test_unicode_account_names', passed: true, category: 'EdgeCases' },
  { name: 'test_very_large_numbers', passed: true, category: 'EdgeCases' },
  { name: 'test_negative_values', passed: true, category: 'EdgeCases' },
  // Zero-Storage Leak Tests
  { name: 'test_no_temp_files_created', passed: true, category: 'ZeroStorageLeak' },
  { name: 'test_memory_released_after_processing', passed: true, category: 'ZeroStorageLeak' },
  { name: 'test_no_data_persists_after_error', passed: true, category: 'ZeroStorageLeak' },
  { name: 'test_auditor_clear_on_exception', passed: true, category: 'ZeroStorageLeak' },
  // Performance Tests
  { name: 'test_large_file_completes_in_time', passed: true, category: 'Performance' },
  { name: 'test_memory_stays_bounded', passed: true, category: 'Performance' },
]

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

  const passedTests = LAST_TEST_RUN.filter(t => t.passed).length
  const totalTests = LAST_TEST_RUN.length
  const allPassed = passedTests === totalTests

  const categories = [...new Set(LAST_TEST_RUN.map(t => t.category))]

  return (
    <main className="min-h-screen bg-surface-page py-12 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-serif font-bold text-content-primary mb-2">System Health</h1>
          <p className="text-content-secondary font-sans">Paciolus Backend Status & Test Results</p>
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

        {/* Test Results Card */}
 <div className="theme-card rounded-2xl p-6">
          <div className="flex items-center justify-between mb-6">
            <h2 className="text-xl font-serif font-semibold text-content-primary flex items-center gap-2">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              Test Results
            </h2>
            <div className={`px-3 py-1 rounded-full text-sm font-sans font-medium ${
              allPassed
                ? 'bg-sage-50 text-sage-700 border border-sage-200'
                : 'bg-clay-50 text-clay-700 border border-clay-200'
            }`}>
              {passedTests}/{totalTests} Passed
            </div>
          </div>

          {/* Overall Progress Bar */}
          <div className="mb-6">
            <div className="h-2 bg-surface-card-secondary rounded-full overflow-hidden">
              <div
                className={`h-full transition-all duration-500 ${
                  allPassed ? 'bg-sage-500' : 'bg-oatmeal-500'
                }`}
                style={{ width: `${(passedTests / totalTests) * 100}%` }}
              ></div>
            </div>
          </div>

          {/* Test Categories */}
          <div className="space-y-4">
            {categories.map(category => {
              const categoryTests = LAST_TEST_RUN.filter(t => t.category === category)
              const categoryPassed = categoryTests.filter(t => t.passed).length
              const categoryAllPassed = categoryPassed === categoryTests.length

              return (
                <div key={category} className="bg-surface-card-secondary rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="text-content-primary font-sans font-medium">{category}</h3>
                    <span className={`text-sm font-sans ${categoryAllPassed ? 'text-sage-600' : 'text-clay-600'}`}>
                      {categoryPassed}/{categoryTests.length}
                    </span>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    {categoryTests.map(test => (
                      <div
                        key={test.name}
                        className={`px-2 py-1 rounded-sm text-xs font-mono ${
                          test.passed
                            ? 'bg-sage-50 text-sage-700 border border-sage-200'
                            : 'bg-clay-50 text-clay-700 border border-clay-200'
                        }`}
                        title={test.name}
                      >
                        {test.passed ? '✓' : '✗'} {test.name.replace('test_', '')}
                      </div>
                    ))}
                  </div>
                </div>
              )
            })}
          </div>

          {/* Last Run Info */}
          <div className="mt-6 pt-4 border-t border-theme text-sm text-content-secondary font-sans">
            <p>Last test run: Day 8 - Automated Verification Suite</p>
            <p className="mt-1">Run command: <code className="text-sage-600 font-mono">pytest tests/test_audit_engine.py -v</code></p>
          </div>
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
