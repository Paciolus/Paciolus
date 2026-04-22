'use client'

/**
 * Public share-receive page (Sprint 699).
 *
 * Wired to the Sprint 696+698 passcode contract:
 *   GET  /export-sharing/{token}               → 200 bytes for non-passcode shares,
 *                                                 403 with instructional message
 *                                                 when a passcode is required.
 *   POST /export-sharing/{token}/download      → accepts {"passcode": "..."}; returns
 *                                                 bytes on success, 403 on invalid
 *                                                 passcode, 429 with Retry-After on
 *                                                 per-token or per-IP lockout.
 *
 * Zero-Storage: nothing persisted. The blob is streamed to an anchor click and
 * revoked immediately after the browser initiates the download.
 */

import { useCallback, useEffect, useRef, useState } from 'react'
import Link from 'next/link'
import { useParams } from 'next/navigation'

type PageState =
  | { kind: 'checking' }
  | { kind: 'passcode_required'; errorMessage?: string }
  | { kind: 'locked'; retryAfter: number }
  | { kind: 'expired' }
  | { kind: 'not_found' }
  | { kind: 'downloaded' }
  | { kind: 'network_error'; detail: string }

const API_BASE = process.env.NEXT_PUBLIC_API_URL || ''

function filenameFromDisposition(header: string | null): string | null {
  if (!header) return null
  // RFC 5987 filename* wins over plain filename= when both present.
  const starMatch = /filename\*=UTF-8''([^;\n]+)/i.exec(header)
  if (starMatch && starMatch[1]) {
    try {
      return decodeURIComponent(starMatch[1].trim().replace(/^"|"$/g, ''))
    } catch {
      // fall through to plain filename
    }
  }
  const plain = /filename="?([^";\n]+)"?/i.exec(header)
  return plain && plain[1] ? plain[1].trim() : null
}

async function triggerDownload(response: Response, fallbackName: string) {
  const blob = await response.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = filenameFromDisposition(response.headers.get('Content-Disposition')) ?? fallbackName
  document.body.appendChild(a)
  a.click()
  document.body.removeChild(a)
  URL.revokeObjectURL(url)
}

export default function SharedDownloadPage() {
  const params = useParams()
  const rawToken = params?.token
  const token = Array.isArray(rawToken) ? rawToken[0] ?? '' : rawToken ?? ''
  const [state, setState] = useState<PageState>({ kind: 'checking' })
  const [passcode, setPasscode] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const probed = useRef(false)

  const probeShare = useCallback(async () => {
    try {
      const resp = await fetch(`${API_BASE}/export-sharing/${encodeURIComponent(token)}`, {
        method: 'GET',
        credentials: 'omit',
      })
      if (resp.ok) {
        await triggerDownload(resp, `paciolus_export_${token.slice(0, 8)}`)
        setState({ kind: 'downloaded' })
        return
      }
      if (resp.status === 403) {
        setState({ kind: 'passcode_required' })
        return
      }
      if (resp.status === 410) {
        setState({ kind: 'expired' })
        return
      }
      if (resp.status === 404) {
        setState({ kind: 'not_found' })
        return
      }
      const body = await resp.json().catch(() => ({}))
      setState({ kind: 'network_error', detail: body.detail ?? `Server returned ${resp.status}` })
    } catch (e) {
      setState({ kind: 'network_error', detail: e instanceof Error ? e.message : 'Network error' })
    }
  }, [token])

  useEffect(() => {
    if (probed.current) return
    probed.current = true
    probeShare()
  }, [probeShare])

  const submitPasscode = useCallback(async () => {
    if (passcode.length === 0) return
    setSubmitting(true)
    try {
      const resp = await fetch(
        `${API_BASE}/export-sharing/${encodeURIComponent(token)}/download`,
        {
          method: 'POST',
          credentials: 'omit',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ passcode }),
        },
      )
      if (resp.ok) {
        await triggerDownload(resp, `paciolus_export_${token.slice(0, 8)}`)
        setState({ kind: 'downloaded' })
        return
      }
      if (resp.status === 429) {
        const retryAfter = Number(resp.headers.get('Retry-After') ?? '60')
        setState({ kind: 'locked', retryAfter: Math.max(1, retryAfter) })
        return
      }
      if (resp.status === 410) {
        setState({ kind: 'expired' })
        return
      }
      if (resp.status === 404) {
        setState({ kind: 'not_found' })
        return
      }
      const body = await resp.json().catch(() => ({}))
      setState({
        kind: 'passcode_required',
        errorMessage: body.detail ?? 'Invalid passcode. Please try again.',
      })
      setPasscode('')
    } catch (e) {
      setState({
        kind: 'passcode_required',
        errorMessage: e instanceof Error ? e.message : 'Network error',
      })
    } finally {
      setSubmitting(false)
    }
  }, [passcode, token])

  return (
    <main id="main-content" className="min-h-screen bg-surface-page flex flex-col">
      <header className="border-b border-theme">
        <div className="max-w-3xl mx-auto px-6 py-4 flex items-center justify-between">
          <Link href="/" className="font-serif text-lg font-bold text-content-primary">
            Paciolus
          </Link>
          <span className="text-xs font-sans text-content-tertiary uppercase tracking-wider">
            Shared Export
          </span>
        </div>
      </header>
      <section className="flex-1 flex items-center justify-center px-6 py-12">
        <div className="theme-card p-8 max-w-md w-full">
          <ShareStateView
            state={state}
            passcode={passcode}
            submitting={submitting}
            onPasscodeChange={setPasscode}
            onSubmit={submitPasscode}
            onRetry={() => {
              probed.current = false
              setState({ kind: 'checking' })
              probeShare()
            }}
          />
        </div>
      </section>
    </main>
  )
}

function ShareStateView({
  state,
  passcode,
  submitting,
  onPasscodeChange,
  onSubmit,
  onRetry,
}: {
  state: PageState
  passcode: string
  submitting: boolean
  onPasscodeChange: (s: string) => void
  onSubmit: () => void
  onRetry: () => void
}) {
  if (state.kind === 'checking') {
    return (
      <div className="text-center py-6" aria-live="polite">
        <div className="w-6 h-6 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin mx-auto mb-3" />
        <p className="font-sans text-sm text-content-secondary">Checking share link…</p>
      </div>
    )
  }

  if (state.kind === 'downloaded') {
    return (
      <div className="text-center py-4">
        <h1 className="font-serif text-xl font-bold text-content-primary mb-2">
          Download started
        </h1>
        <p className="font-sans text-sm text-content-secondary mb-4">
          Your export should appear in your browser downloads. This link remains valid
          until it expires or is revoked by the sender.
        </p>
        <button
          type="button"
          onClick={onRetry}
          className="px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
        >
          Download again
        </button>
      </div>
    )
  }

  if (state.kind === 'not_found') {
    return (
      <div className="text-center py-4">
        <h1 className="font-serif text-xl font-bold text-content-primary mb-2">
          Share link unavailable
        </h1>
        <p className="font-sans text-sm text-content-secondary">
          This link doesn&apos;t exist or has been revoked by the sender.
        </p>
      </div>
    )
  }

  if (state.kind === 'expired') {
    return (
      <div className="text-center py-4">
        <h1 className="font-serif text-xl font-bold text-content-primary mb-2">
          This link has expired
        </h1>
        <p className="font-sans text-sm text-content-secondary">
          Ask the sender to generate a new share link.
        </p>
      </div>
    )
  }

  if (state.kind === 'locked') {
    return <LockoutCountdown seconds={state.retryAfter} onExpire={onRetry} />
  }

  if (state.kind === 'network_error') {
    return (
      <div className="text-center py-4" role="alert">
        <h1 className="font-serif text-xl font-bold text-content-primary mb-2">
          Something went wrong
        </h1>
        <p className="font-sans text-sm text-content-secondary mb-4">{state.detail}</p>
        <button
          type="button"
          onClick={onRetry}
          className="px-4 py-2 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm hover:bg-sage-700 transition-colors"
        >
          Try again
        </button>
      </div>
    )
  }

  // passcode_required
  return (
    <form
      onSubmit={e => {
        e.preventDefault()
        if (!submitting) onSubmit()
      }}
    >
      <h1 className="font-serif text-xl font-bold text-content-primary mb-2">
        Passcode required
      </h1>
      <p className="font-sans text-sm text-content-secondary mb-4">
        This share link is passcode-protected. Enter the passcode provided by the sender.
      </p>
      <label htmlFor="shared-passcode" className="block text-xs font-sans font-medium text-content-secondary mb-1">
        Passcode
      </label>
      <input
        id="shared-passcode"
        ref={el => el?.focus()}
        type="password"
        autoComplete="off"
        value={passcode}
        onChange={e => onPasscodeChange(e.target.value)}
        className="w-full px-3 py-2 rounded-lg bg-surface-input border border-theme text-content-primary font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500"
        disabled={submitting}
      />
      {state.errorMessage && (
        <p className="mt-2 text-xs font-sans text-clay-700" role="alert">
          {state.errorMessage}
        </p>
      )}
      <button
        type="submit"
        disabled={submitting || passcode.length === 0}
        className="mt-4 w-full px-5 py-2.5 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? 'Verifying…' : 'Download'}
      </button>
      <p className="mt-3 text-xs font-sans text-content-tertiary">
        Passcodes are never embedded in share links or emails — the sender should deliver
        yours over a separate channel.
      </p>
    </form>
  )
}

function LockoutCountdown({ seconds, onExpire }: { seconds: number; onExpire: () => void }) {
  const [remaining, setRemaining] = useState(seconds)
  useEffect(() => {
    setRemaining(seconds)
  }, [seconds])
  useEffect(() => {
    if (remaining <= 0) {
      onExpire()
      return
    }
    const id = setTimeout(() => setRemaining(r => r - 1), 1000)
    return () => clearTimeout(id)
  }, [remaining, onExpire])

  const minutes = Math.floor(remaining / 60)
  const secs = remaining % 60
  const formatted = minutes > 0 ? `${minutes}m ${secs}s` : `${secs}s`

  return (
    <div className="text-center py-4" role="alert">
      <h1 className="font-serif text-xl font-bold text-content-primary mb-2">
        Too many failed attempts
      </h1>
      <p className="font-sans text-sm text-content-secondary mb-3">
        For security, this share link is temporarily locked. Try again in{' '}
        <span className="font-mono text-content-primary">{formatted}</span>.
      </p>
      <p className="text-xs font-sans text-content-tertiary">
        The countdown resets once the lockout expires.
      </p>
    </div>
  )
}
