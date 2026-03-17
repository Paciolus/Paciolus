'use client'

/**
 * Branding Settings Page — Sprint 545b
 *
 * PDF branding configuration: header text, footer text, logo upload.
 * Enterprise tier only (gated by FeatureGate).
 */

import { useEffect, useState, useRef } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/contexts/AuthContext'
import { FeatureGate } from '@/components/shared/FeatureGate'
import { Reveal } from '@/components/ui/Reveal'
import { useBranding } from '@/hooks/useBranding'

const MAX_LOGO_SIZE = 500 * 1024 // 500KB
const ACCEPTED_TYPES = ['image/png', 'image/jpeg']

export default function BrandingSettingsPage() {
  const router = useRouter()
  const { isAuthenticated, isLoading: authLoading } = useAuth()
  const {
    branding,
    isLoading,
    error,
    fetchBranding,
    updateBranding,
    uploadLogo,
    deleteLogo,
  } = useBranding()

  const [header, setHeader] = useState('')
  const [footer, setFooter] = useState('')
  const [saving, setSaving] = useState(false)
  const [uploadError, setUploadError] = useState<string | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated) {
      fetchBranding()
    }
  }, [isAuthenticated, fetchBranding])

  useEffect(() => {
    if (branding) {
      setHeader(branding.header_text)
      setFooter(branding.footer_text)
    }
  }, [branding])

  async function handleSave() {
    setSaving(true)
    await updateBranding(header, footer)
    setSaving(false)
  }

  async function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    setUploadError(null)
    const file = e.target.files?.[0]
    if (!file) return

    if (!ACCEPTED_TYPES.includes(file.type)) {
      setUploadError('Only PNG and JPEG files are accepted.')
      return
    }
    if (file.size > MAX_LOGO_SIZE) {
      setUploadError('Logo must be under 500KB.')
      return
    }

    await uploadLogo(file)
    // Reset input so same file can be re-selected
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  async function handleDeleteLogo() {
    await deleteLogo()
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
              <span className="text-content-secondary">PDF Branding</span>
            </div>
            <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
              PDF Branding
            </h1>
            <p className="text-content-secondary font-sans">
              Customize the header, footer, and logo on exported PDF memos.
            </p>
          </div>

          <FeatureGate feature="custom_branding">
            {/* Error Banner */}
            {(error || uploadError) && (
              <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-6 text-sm font-sans" role="alert">
                {error || uploadError}
              </div>
            )}

            {/* Text Settings */}
            <Reveal className="mb-6">
              <div className="bg-surface-card border border-theme rounded-xl p-6">
                <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
                  Header & Footer Text
                </h2>
                <div className="space-y-4">
                  <div>
                    <label htmlFor="header-text" className="block text-sm font-sans font-medium text-content-secondary mb-1">
                      Header Text
                    </label>
                    <input
                      id="header-text"
                      type="text"
                      maxLength={200}
                      value={header}
                      onChange={e => setHeader(e.target.value)}
                      placeholder="e.g., Smith & Associates CPA"
                      className="w-full bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder:text-content-muted"
                    />
                    <p className="text-xs text-content-tertiary font-sans mt-1">{header.length}/200</p>
                  </div>
                  <div>
                    <label htmlFor="footer-text" className="block text-sm font-sans font-medium text-content-secondary mb-1">
                      Footer Text
                    </label>
                    <textarea
                      id="footer-text"
                      maxLength={300}
                      value={footer}
                      onChange={e => setFooter(e.target.value)}
                      placeholder="e.g., Confidential — Prepared for client use only"
                      rows={3}
                      className="w-full bg-surface-input border border-theme rounded-lg px-3 py-2 text-sm font-sans text-content-primary placeholder:text-content-muted resize-none"
                    />
                    <p className="text-xs text-content-tertiary font-sans mt-1">{footer.length}/300</p>
                  </div>
                  <button
                    onClick={handleSave}
                    disabled={saving || isLoading}
                    className="px-5 py-2.5 bg-sage-600 text-white rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {saving ? 'Saving...' : 'Save Text'}
                  </button>
                </div>
              </div>
            </Reveal>

            {/* Logo Upload */}
            <Reveal delay={0.06}>
              <div className="bg-surface-card border border-theme rounded-xl p-6">
                <h2 className="text-xl font-serif font-semibold text-content-primary mb-4">
                  Logo
                </h2>

                {branding?.logo_url ? (
                  <div className="mb-4">
                    <div className="w-48 h-24 border border-theme rounded-lg overflow-hidden bg-surface-input flex items-center justify-center mb-3">
                      <img
                        src={branding.logo_url}
                        alt="Current logo"
                        className="max-w-full max-h-full object-contain"
                      />
                    </div>
                    <button
                      onClick={handleDeleteLogo}
                      className="px-4 py-2 border border-clay-200 text-clay-600 rounded-lg font-sans text-sm font-medium hover:bg-clay-50 transition-colors"
                    >
                      Remove Logo
                    </button>
                  </div>
                ) : (
                  <p className="text-sm text-content-muted font-sans mb-4">No logo uploaded.</p>
                )}

                <div>
                  <input
                    ref={fileInputRef}
                    type="file"
                    accept="image/png,image/jpeg"
                    onChange={handleFileSelect}
                    className="block w-full text-sm text-content-secondary font-sans
                      file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border file:border-theme
                      file:text-sm file:font-sans file:font-medium file:text-content-primary
                      file:bg-surface-input hover:file:bg-oatmeal-200 file:transition-colors file:cursor-pointer"
                  />
                  <p className="text-xs text-content-tertiary font-sans mt-2">
                    PNG or JPEG, max 500KB. Recommended: 400x100px.
                  </p>
                </div>
              </div>
            </Reveal>
          </FeatureGate>
        </div>
      </div>
    </main>
  )
}
