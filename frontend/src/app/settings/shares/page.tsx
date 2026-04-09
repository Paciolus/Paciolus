'use client'

/**
 * Export Sharing Page — Sprint 545c
 *
 * List active share links with revoke, expiry countdown, access count.
 * Professional+ tier (gated by FeatureGate).
 */

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { FeatureGate } from '@/components/shared/FeatureGate'
import { Reveal } from '@/components/ui/Reveal'
import { useExportSharing } from '@/hooks/useExportSharing'

function formatTimeRemaining(expiresAt: string): string {
  const diff = new Date(expiresAt).getTime() - Date.now()
  if (diff <= 0) return 'Expired'
  const hours = Math.floor(diff / (1000 * 60 * 60))
  const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60))
  if (hours > 0) return `${hours}h ${minutes}m`
  return `${minutes}m`
}

export default function ExportSharingPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuthSession()
  const {
    shares,
    isLoading,
    error,
    listShares,
    revokeShare,
  } = useExportSharing()

  const [revoking, setRevoking] = useState<string | null>(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      listShares()
    }
  }, [isAuthenticated, listShares])

  async function handleRevoke(token: string) {
    setRevoking(token)
    await revokeShare(token)
    setRevoking(null)
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="pt-8 pb-16 px-6">
        <div className="max-w-2xl mx-auto">
          {/* Breadcrumb + Header */}
          <div className="mb-8">
            <div className="flex items-center gap-2 text-content-tertiary text-sm font-sans mb-4">
              <Link href="/" className="hover:text-content-secondary transition-colors">Home</Link>
              <span>/</span>
              <Link href="/settings" className="hover:text-content-secondary transition-colors">Settings</Link>
              <span>/</span>
              <span className="text-content-secondary">Export Sharing</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
              Export Sharing
            </h1>
            <p className="text-content-secondary font-sans">
              Manage active share links for your exported reports.
            </p>
          </div>

          <FeatureGate feature="export_sharing">
            {/* Error Banner */}
            {error && (
              <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-6 text-sm font-sans" role="alert">
                {error}
              </div>
            )}

            <Reveal>
              <div className="bg-surface-card border border-theme rounded-xl overflow-hidden">
                {isLoading && !shares.length ? (
                  <div className="px-4 py-12 text-center text-content-muted text-sm font-sans">Loading...</div>
                ) : shares.length === 0 ? (
                  <div className="px-4 py-12 text-center">
                    <p className="text-content-muted text-sm font-sans mb-2">No active share links.</p>
                    <p className="text-content-tertiary text-xs font-sans">
                      Share links are created from the export toolbar on any tool page.
                    </p>
                  </div>
                ) : (
                  <table className="w-full text-sm font-sans">
                    <thead>
                      <tr className="border-b border-theme bg-surface-input/50">
                        <th className="text-left px-4 py-3 font-medium text-content-secondary">Tool</th>
                        <th className="text-left px-4 py-3 font-medium text-content-secondary">Format</th>
                        <th className="text-center px-4 py-3 font-medium text-content-secondary">Protection</th>
                        <th className="text-right px-4 py-3 font-medium text-content-secondary">Views</th>
                        <th className="text-left px-4 py-3 font-medium text-content-secondary">Expires</th>
                        <th className="text-right px-4 py-3 font-medium text-content-secondary"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {shares.map(share => {
                        const isExpired = new Date(share.expires_at).getTime() <= Date.now()
                        return (
                          <tr key={share.token} className="border-b border-theme last:border-0">
                            <td className="px-4 py-3 text-content-primary">{share.tool}</td>
                            <td className="px-4 py-3 text-content-secondary uppercase font-mono text-xs">{share.format}</td>
                            <td className="px-4 py-3 text-center">
                              <span className="inline-flex items-center gap-1">
                                {share.has_passcode && (
                                  <span title="Passcode-protected" className="text-sage-600 text-xs" aria-label="Passcode-protected">
                                    &#128274;
                                  </span>
                                )}
                                {share.single_use && (
                                  <span className="inline-block px-1.5 py-0.5 bg-oatmeal-200 text-obsidian-600 rounded text-[10px] font-medium font-sans">
                                    1x
                                  </span>
                                )}
                                {!share.has_passcode && !share.single_use && (
                                  <span className="text-content-muted text-xs">—</span>
                                )}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right font-mono text-content-primary">{share.access_count}</td>
                            <td className="px-4 py-3">
                              <span className={isExpired ? 'text-clay-600' : 'text-content-tertiary'}>
                                {formatTimeRemaining(share.expires_at)}
                              </span>
                            </td>
                            <td className="px-4 py-3 text-right">
                              {!isExpired && (
                                <button
                                  onClick={() => handleRevoke(share.token)}
                                  disabled={revoking === share.token}
                                  className="px-3 py-1 border border-clay-200 text-clay-600 rounded-lg text-xs font-medium hover:bg-clay-50 transition-colors disabled:opacity-50"
                                >
                                  {revoking === share.token ? 'Revoking...' : 'Revoke'}
                                </button>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                )}
              </div>
            </Reveal>
          </FeatureGate>
        </div>
      </div>
    </main>
  )
}
