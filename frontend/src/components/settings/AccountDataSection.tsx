'use client'

/**
 * AccountDataSection — download your data, delete your account (Sprint 844).
 *
 * The Privacy Policy promised both; until Sprint 844 neither existed. Backed by
 * `GET /auth/account/export` and `POST /auth/account/delete`
 * (backend/services/account_erasure.py).
 */

import { useState } from 'react'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { apiDownload, apiPost, downloadBlob } from '@/utils/apiClient'

export function AccountDataSection() {
  const { token, logout } = useAuthSession()
  const [exporting, setExporting] = useState(false)
  const [exportError, setExportError] = useState('')
  const [password, setPassword] = useState('')
  const [confirmWord, setConfirmWord] = useState('')
  const [deleting, setDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState('')

  async function handleExport() {
    setExporting(true)
    setExportError('')
    const { ok, blob, error } = await apiDownload('/auth/account/export', token)
    setExporting(false)
    if (ok && blob) {
      downloadBlob(blob, 'paciolus-account-export.json')
    } else {
      setExportError(error ?? 'Could not prepare your export. Please try again.')
    }
  }

  async function handleDelete() {
    setDeleting(true)
    setDeleteError('')
    const { ok, error } = await apiPost('/auth/account/delete', token, { password, confirm: confirmWord })
    setDeleting(false)
    if (!ok) {
      setDeleteError(error ?? 'Your account could not be deleted. Nothing was removed.')
      return
    }
    await logout()
    window.location.href = '/'
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="font-serif text-base text-content-primary mb-1">Download your data</h3>
        <p className="text-sm font-sans text-content-secondary mb-3">
          A JSON file with everything Paciolus stores about your account: profile, clients, engagements,
          analysis summaries, activity history and sessions. Uploaded files are not kept, so none are included.
        </p>
        <button
          onClick={() => { void handleExport() }}
          disabled={exporting}
          className="px-4 py-2 border border-theme rounded-lg font-sans text-sm text-content-primary hover:bg-surface-card-secondary disabled:opacity-50"
        >
          {exporting ? 'Preparing...' : 'Download my data'}
        </button>
        {exportError && <p role="alert" className="text-sm text-clay-600 mt-2">{exportError}</p>}
      </div>

      <div className="border-t border-theme pt-6">
        <h3 className="font-serif text-base text-clay-700 mb-1">Delete your account</h3>
        <p className="text-sm font-sans text-content-secondary mb-3">
          Permanently deletes your account, clients, engagements, analysis summaries, activity history and shared
          links, and cancels your subscription. This cannot be undone. Stripe keeps the invoice and payment records the
          law requires, and anonymized billing history is retained.
        </p>
        <div className="grid gap-3 sm:grid-cols-2 mb-3">
          <label className="text-xs font-sans text-content-secondary">
            Current password
            <input
              type="password"
              autoComplete="current-password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              className="mt-1 w-full px-3 py-2 bg-surface-card border border-theme rounded-lg text-sm"
            />
          </label>
          <label className="text-xs font-sans text-content-secondary">
            Type DELETE to confirm
            <input
              type="text"
              value={confirmWord}
              onChange={e => setConfirmWord(e.target.value)}
              className="mt-1 w-full px-3 py-2 bg-surface-card border border-theme rounded-lg text-sm font-mono"
            />
          </label>
        </div>
        <button
          onClick={() => { void handleDelete() }}
          disabled={deleting || !password || confirmWord !== 'DELETE'}
          className="px-4 py-2 bg-clay-600 text-oatmeal-50 rounded-lg font-sans text-sm font-medium hover:bg-clay-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {deleting ? 'Deleting...' : 'Delete my account'}
        </button>
        {deleteError && <p role="alert" className="text-sm text-clay-600 mt-2">{deleteError}</p>}
      </div>
    </div>
  )
}
