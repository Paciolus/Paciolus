'use client'

/**
 * Internal Admin — Customer Detail Page
 * Sprint 590: Superadmin CRM
 *
 * Full customer profile with admin action modals.
 */

import { useEffect, useState } from 'react'
import { useParams, useRouter } from 'next/navigation'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { useToast } from '@/contexts/ToastContext'
import { Reveal } from '@/components/ui/Reveal'
import { useInternalAdmin } from '@/hooks/useInternalAdmin'

export default function CustomerDetailPage() {
  const params = useParams()
  const router = useRouter()
  const orgId = Number(params.orgId)
  const { isAuthenticated, isLoading: authLoading } = useAuthSession()
  const { success, error: toastError } = useToast()
  const {
    customerDetail,
    isLoading,
    error,
    fetchCustomerDetail,
    planOverride,
    extendTrial,
    issueCredit,
    issueRefund,
    forceCancel,
    impersonate,
    revokeSessions,
  } = useInternalAdmin()

  // Modal state
  const [activeModal, setActiveModal] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)
  const [formData, setFormData] = useState<Record<string, string>>({})

  useEffect(() => {
    if (!authLoading && !isAuthenticated) router.push('/login')
  }, [authLoading, isAuthenticated, router])

  useEffect(() => {
    if (isAuthenticated && orgId) fetchCustomerDetail(orgId)
  }, [isAuthenticated, orgId, fetchCustomerDetail])

  async function handleAction(action: () => Promise<unknown>) {
    setActionLoading(true)
    try {
      await action()
      success('Action completed')
      setActiveModal(null)
      setFormData({})
      fetchCustomerDetail(orgId) // Refresh
    } catch (e) {
      toastError('Action failed', e instanceof Error ? e.message : 'Unknown error')
    } finally {
      setActionLoading(false)
    }
  }

  if (authLoading || isLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  const d = customerDetail
  if (!d) {
    return (
      <main className="min-h-screen bg-surface-page">
        <div className="pt-8 pb-16 px-6 max-w-5xl mx-auto">
          <p className="text-content-tertiary font-sans">{error || 'Customer not found.'}</p>
          <button onClick={() => router.push('/internal/admin')} className="mt-4 text-sage-600 font-sans text-sm hover:underline">
            Back to customer list
          </button>
        </div>
      </main>
    )
  }

  return (
    <main id="main-content" className="min-h-screen bg-surface-page">
      <div className="pt-8 pb-16 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Breadcrumb */}
          <button onClick={() => router.push('/internal/admin')} className="text-sage-600 font-sans text-sm hover:underline mb-4 block">
            ← Back to customers
          </button>

          {/* Header */}
          <Reveal>
            <div className="flex items-start justify-between mb-6">
              <div>
                <h1 className="text-2xl font-serif font-bold text-content-primary">
                  {d.org_name || d.owner_name || d.owner_email}
                </h1>
                <p className="text-content-secondary font-sans text-sm mt-1">{d.owner_email}</p>
                <div className="flex items-center gap-2 mt-2">
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                    d.subscription?.tier === 'enterprise' ? 'bg-obsidian-100 text-obsidian-700' :
                    d.subscription?.tier === 'professional' ? 'bg-sage-100 text-sage-700' :
                    d.subscription?.tier === 'solo' ? 'bg-oatmeal-200 text-obsidian-600' :
                    'bg-surface-input text-content-tertiary'
                  }`}>
                    {d.subscription?.tier ?? 'free'}
                  </span>
                  <span className={`inline-block px-2 py-0.5 rounded text-xs font-medium ${
                    d.subscription?.status === 'active' ? 'bg-sage-100 text-sage-700' :
                    d.subscription?.status === 'trialing' ? 'bg-oatmeal-200 text-obsidian-600' :
                    'bg-clay-100 text-clay-700'
                  }`}>
                    {d.subscription?.status ?? 'no subscription'}
                  </span>
                  {d.is_verified && (
                    <span className="inline-block px-2 py-0.5 rounded text-xs font-medium bg-sage-50 text-sage-600">verified</span>
                  )}
                </div>
              </div>
            </div>
          </Reveal>

          {/* Action Buttons */}
          <Reveal delay={0.06}>
            <div className="flex flex-wrap gap-2 mb-6">
              <button onClick={() => setActiveModal('plan')} className="px-3 py-1.5 border border-theme rounded-lg text-sm font-sans hover:bg-surface-input transition-colors">Override Plan</button>
              <button onClick={() => setActiveModal('trial')} className="px-3 py-1.5 border border-theme rounded-lg text-sm font-sans hover:bg-surface-input transition-colors">Extend Trial</button>
              <button onClick={() => setActiveModal('credit')} className="px-3 py-1.5 border border-theme rounded-lg text-sm font-sans hover:bg-surface-input transition-colors">Issue Credit</button>
              <button onClick={() => setActiveModal('refund')} className="px-3 py-1.5 border border-theme rounded-lg text-sm font-sans hover:bg-surface-input transition-colors">Issue Refund</button>
              <button onClick={() => setActiveModal('cancel')} className="px-3 py-1.5 border border-clay-300 text-clay-600 rounded-lg text-sm font-sans hover:bg-clay-50 transition-colors">Cancel Subscription</button>
              <button onClick={() => setActiveModal('impersonate')} className="px-3 py-1.5 border border-theme rounded-lg text-sm font-sans hover:bg-surface-input transition-colors">View as Customer</button>
              <button onClick={() => handleAction(() => revokeSessions(orgId))} className="px-3 py-1.5 border border-clay-300 text-clay-600 rounded-lg text-sm font-sans hover:bg-clay-50 transition-colors">Revoke Sessions</button>
            </div>
          </Reveal>

          {/* Info Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Account Info */}
            <Reveal delay={0.12}>
              <div className="bg-surface-card border border-theme rounded-xl p-4">
                <h2 className="text-lg font-serif font-semibold text-content-primary mb-3">Account Info</h2>
                <dl className="space-y-2 text-sm font-sans">
                  <div className="flex justify-between"><dt className="text-content-tertiary">Signup</dt><dd className="text-content-primary">{d.signup_date ? new Date(d.signup_date).toLocaleDateString() : '—'}</dd></div>
                  <div className="flex justify-between"><dt className="text-content-tertiary">Last Login</dt><dd className="text-content-primary">{d.last_login ? new Date(d.last_login).toLocaleString() : 'Never'}</dd></div>
                  <div className="flex justify-between"><dt className="text-content-tertiary">Active Sessions</dt><dd className="font-mono text-content-primary">{d.active_session_count}</dd></div>
                  <div className="flex justify-between"><dt className="text-content-tertiary">Members</dt><dd className="font-mono text-content-primary">{d.members.length}</dd></div>
                </dl>
                {d.members.length > 0 && (
                  <div className="mt-3 border-t border-theme pt-3">
                    <h3 className="text-xs font-sans text-content-tertiary uppercase tracking-wide mb-2">Team Members</h3>
                    {d.members.map(m => (
                      <div key={m.user_id} className="flex items-center justify-between py-1 text-sm font-sans">
                        <span className="text-content-primary">{m.name || m.email}</span>
                        <span className="text-xs text-content-tertiary px-2 py-0.5 bg-surface-input rounded">{m.role}</span>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </Reveal>

            {/* Billing */}
            <Reveal delay={0.18}>
              <div className="bg-surface-card border border-theme rounded-xl p-4">
                <h2 className="text-lg font-serif font-semibold text-content-primary mb-3">Billing</h2>
                {d.subscription ? (
                  <dl className="space-y-2 text-sm font-sans">
                    <div className="flex justify-between"><dt className="text-content-tertiary">Plan</dt><dd className="text-content-primary font-medium">{d.subscription.tier} ({d.subscription.billing_interval ?? 'monthly'})</dd></div>
                    <div className="flex justify-between"><dt className="text-content-tertiary">Seats</dt><dd className="font-mono text-content-primary">{d.subscription.total_seats} ({d.subscription.seat_count} base + {d.subscription.additional_seats} add-on)</dd></div>
                    <div className="flex justify-between"><dt className="text-content-tertiary">Period End</dt><dd className="text-content-primary">{d.subscription.current_period_end ? new Date(d.subscription.current_period_end).toLocaleDateString() : '—'}</dd></div>
                    <div className="flex justify-between"><dt className="text-content-tertiary">Cancel at End</dt><dd className="text-content-primary">{d.subscription.cancel_at_period_end ? 'Yes' : 'No'}</dd></div>
                    {d.subscription.stripe_customer_id && (
                      <div className="flex justify-between"><dt className="text-content-tertiary">Stripe ID</dt><dd className="font-mono text-content-primary text-xs">{d.subscription.stripe_customer_id}</dd></div>
                    )}
                  </dl>
                ) : (
                  <p className="text-sm text-content-tertiary font-sans">No subscription.</p>
                )}
              </div>
            </Reveal>

            {/* Usage */}
            <Reveal delay={0.24}>
              <div className="bg-surface-card border border-theme rounded-xl p-4">
                <h2 className="text-lg font-serif font-semibold text-content-primary mb-3">Usage</h2>
                <dl className="space-y-2 text-sm font-sans">
                  <div className="flex justify-between"><dt className="text-content-tertiary">Uploads (this period)</dt><dd className="font-mono text-content-primary">{d.subscription?.uploads_used_current_period ?? 0}</dd></div>
                  <div className="flex justify-between"><dt className="text-content-tertiary">Uploads (30d)</dt><dd className="font-mono text-content-primary">{d.usage_stats?.uploads_30d ?? 0}</dd></div>
                  <div className="flex justify-between"><dt className="text-content-tertiary">Total Reports</dt><dd className="font-mono text-content-primary">{d.usage_stats?.total_reports ?? 0}</dd></div>
                </dl>
              </div>
            </Reveal>

            {/* Billing Events Timeline */}
            <Reveal delay={0.3}>
              <div className="bg-surface-card border border-theme rounded-xl p-4">
                <h2 className="text-lg font-serif font-semibold text-content-primary mb-3">Billing Timeline</h2>
                {d.billing_events.length > 0 ? (
                  <div className="space-y-2 max-h-64 overflow-y-auto">
                    {d.billing_events.slice(0, 20).map(e => (
                      <div key={e.id} className="flex items-start justify-between py-1.5 border-b border-theme last:border-0 text-sm font-sans">
                        <div>
                          <span className="text-content-primary font-medium">{e.event_type}</span>
                          {e.tier && <span className="ml-2 text-xs text-content-tertiary">{e.tier}</span>}
                        </div>
                        <span className="text-xs text-content-tertiary whitespace-nowrap ml-3">
                          {new Date(e.created_at).toLocaleDateString()}
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-content-tertiary font-sans">No billing events.</p>
                )}
              </div>
            </Reveal>
          </div>

          {/* Recent Activity */}
          <Reveal delay={0.36}>
            <div className="bg-surface-card border border-theme rounded-xl p-4 mt-6">
              <h2 className="text-lg font-serif font-semibold text-content-primary mb-3">Recent Activity</h2>
              {d.recent_activity.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full text-sm font-sans">
                    <thead>
                      <tr className="border-b border-theme">
                        <th className="text-left py-2 px-3 text-content-tertiary font-medium">File</th>
                        <th className="text-right py-2 px-3 text-content-tertiary font-medium">Records</th>
                        <th className="text-left py-2 px-3 text-content-tertiary font-medium">Date</th>
                      </tr>
                    </thead>
                    <tbody>
                      {d.recent_activity.slice(0, 20).map(a => (
                        <tr key={a.id} className="border-b border-theme last:border-0">
                          <td className="py-2 px-3 text-content-primary">{a.filename_display || '—'}</td>
                          <td className="py-2 px-3 text-right font-mono text-content-primary">{a.record_count}</td>
                          <td className="py-2 px-3 text-content-secondary text-xs">{new Date(a.timestamp).toLocaleString()}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-sm text-content-tertiary font-sans">No activity yet.</p>
              )}
            </div>
          </Reveal>

          {/* Action Modals */}
          {activeModal && (
            <div role="presentation" className="fixed inset-0 z-50 flex items-center justify-center bg-obsidian-900/50 backdrop-blur-sm" onClick={() => setActiveModal(null)} onKeyDown={e => { if (e.key === 'Escape') setActiveModal(null) }}>
              <div role="presentation" className="bg-surface-card border border-theme rounded-xl p-6 w-full max-w-md shadow-xl" onClick={e => e.stopPropagation()} onKeyDown={e => e.stopPropagation()}>
                {activeModal === 'plan' && (
                  <>
                    <h3 className="text-lg font-serif font-semibold text-content-primary mb-4">Override Plan</h3>
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="plan-new-plan" className="block text-sm font-sans text-content-tertiary mb-1">New Plan</label>
                        <select id="plan-new-plan" value={formData.new_plan || ''} onChange={e => setFormData(f => ({ ...f, new_plan: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans">
                          <option value="">Select plan...</option>
                          <option value="solo">Solo</option>
                          <option value="professional">Professional</option>
                          <option value="enterprise">Enterprise</option>
                        </select>
                      </div>
                      <div>
                        <label htmlFor="plan-reason" className="block text-sm font-sans text-content-tertiary mb-1">Reason</label>
                        <textarea id="plan-reason" value={formData.reason || ''} onChange={e => setFormData(f => ({ ...f, reason: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans" rows={2} />
                      </div>
                      <button disabled={!formData.new_plan || !formData.reason || actionLoading} onClick={() => handleAction(() => planOverride(orgId, { new_plan: formData.new_plan ?? '', reason: formData.reason ?? '', effective_immediately: true }))} className="w-full px-4 py-2 bg-sage-600 text-white rounded-lg font-sans font-medium text-sm hover:bg-sage-700 disabled:opacity-40 transition-colors">
                        {actionLoading ? 'Processing...' : 'Override Plan'}
                      </button>
                    </div>
                  </>
                )}
                {activeModal === 'trial' && (
                  <>
                    <h3 className="text-lg font-serif font-semibold text-content-primary mb-4">Extend Trial</h3>
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="trial-days" className="block text-sm font-sans text-content-tertiary mb-1">Days</label>
                        <input id="trial-days" type="number" min={1} max={90} value={formData.days || ''} onChange={e => setFormData(f => ({ ...f, days: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans" />
                      </div>
                      <div>
                        <label htmlFor="trial-reason" className="block text-sm font-sans text-content-tertiary mb-1">Reason</label>
                        <textarea id="trial-reason" value={formData.reason || ''} onChange={e => setFormData(f => ({ ...f, reason: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans" rows={2} />
                      </div>
                      <button disabled={!formData.days || !formData.reason || actionLoading} onClick={() => handleAction(() => extendTrial(orgId, { days: Number(formData.days), reason: formData.reason ?? '' }))} className="w-full px-4 py-2 bg-sage-600 text-white rounded-lg font-sans font-medium text-sm hover:bg-sage-700 disabled:opacity-40 transition-colors">
                        {actionLoading ? 'Processing...' : 'Extend Trial'}
                      </button>
                    </div>
                  </>
                )}
                {activeModal === 'credit' && (
                  <>
                    <h3 className="text-lg font-serif font-semibold text-content-primary mb-4">Issue Credit</h3>
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="credit-amount" className="block text-sm font-sans text-content-tertiary mb-1">Amount ($)</label>
                        <input id="credit-amount" type="number" min={0.01} step={0.01} value={formData.amount || ''} onChange={e => setFormData(f => ({ ...f, amount: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans font-mono" />
                      </div>
                      <div>
                        <label htmlFor="credit-reason" className="block text-sm font-sans text-content-tertiary mb-1">Reason</label>
                        <textarea id="credit-reason" value={formData.reason || ''} onChange={e => setFormData(f => ({ ...f, reason: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans" rows={2} />
                      </div>
                      <button disabled={!formData.amount || !formData.reason || actionLoading} onClick={() => handleAction(() => issueCredit(orgId, { amount_cents: Math.round(Number(formData.amount) * 100), reason: formData.reason ?? '' }))} className="w-full px-4 py-2 bg-sage-600 text-white rounded-lg font-sans font-medium text-sm hover:bg-sage-700 disabled:opacity-40 transition-colors">
                        {actionLoading ? 'Processing...' : 'Issue Credit'}
                      </button>
                    </div>
                  </>
                )}
                {activeModal === 'refund' && (
                  <>
                    <h3 className="text-lg font-serif font-semibold text-content-primary mb-4">Issue Refund</h3>
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="refund-payment-intent" className="block text-sm font-sans text-content-tertiary mb-1">Payment Intent ID</label>
                        <input id="refund-payment-intent" type="text" value={formData.payment_intent_id || ''} onChange={e => setFormData(f => ({ ...f, payment_intent_id: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans font-mono" placeholder="pi_..." />
                      </div>
                      <div>
                        <label htmlFor="refund-amount" className="block text-sm font-sans text-content-tertiary mb-1">Amount ($)</label>
                        <input id="refund-amount" type="number" min={0.01} step={0.01} value={formData.amount || ''} onChange={e => setFormData(f => ({ ...f, amount: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans font-mono" />
                      </div>
                      <div>
                        <label htmlFor="refund-reason" className="block text-sm font-sans text-content-tertiary mb-1">Reason</label>
                        <textarea id="refund-reason" value={formData.reason || ''} onChange={e => setFormData(f => ({ ...f, reason: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans" rows={2} />
                      </div>
                      <button disabled={!formData.payment_intent_id || !formData.amount || !formData.reason || actionLoading} onClick={() => handleAction(() => issueRefund(orgId, { payment_intent_id: formData.payment_intent_id ?? '', amount_cents: Math.round(Number(formData.amount) * 100), reason: formData.reason ?? '' }))} className="w-full px-4 py-2 bg-sage-600 text-white rounded-lg font-sans font-medium text-sm hover:bg-sage-700 disabled:opacity-40 transition-colors">
                        {actionLoading ? 'Processing...' : 'Issue Refund'}
                      </button>
                    </div>
                  </>
                )}
                {activeModal === 'cancel' && (
                  <>
                    <h3 className="text-lg font-serif font-semibold text-content-primary mb-4">Cancel Subscription</h3>
                    <div className="space-y-3">
                      <div>
                        <label htmlFor="cancel-reason" className="block text-sm font-sans text-content-tertiary mb-1">Reason</label>
                        <textarea id="cancel-reason" value={formData.reason || ''} onChange={e => setFormData(f => ({ ...f, reason: e.target.value }))} className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans" rows={2} />
                      </div>
                      <div className="flex items-center gap-2">
                        <input type="checkbox" id="immediate" checked={formData.immediate === 'true'} onChange={e => setFormData(f => ({ ...f, immediate: String(e.target.checked) }))} className="rounded" />
                        <label htmlFor="immediate" className="text-sm font-sans text-content-primary">Cancel immediately (instead of at period end)</label>
                      </div>
                      <button disabled={!formData.reason || actionLoading} onClick={() => handleAction(() => forceCancel(orgId, { reason: formData.reason ?? '', immediate: formData.immediate === 'true' }))} className="w-full px-4 py-2 bg-clay-600 text-white rounded-lg font-sans font-medium text-sm hover:bg-clay-700 disabled:opacity-40 transition-colors">
                        {actionLoading ? 'Processing...' : 'Cancel Subscription'}
                      </button>
                    </div>
                  </>
                )}
                {activeModal === 'impersonate' && (
                  <>
                    <h3 className="text-lg font-serif font-semibold text-content-primary mb-4">View as Customer</h3>
                    <div className="bg-clay-50 border border-clay-200 rounded-lg p-3 mb-4 text-sm font-sans text-clay-700">
                      This will generate a read-only session as this customer. All actions will be blocked. The session expires in 15 minutes. This action is fully audited.
                    </div>
                    <button disabled={actionLoading} onClick={async () => {
                      setActionLoading(true)
                      try {
                        const result = await impersonate(orgId)
                        success('Impersonation token generated')
                        setActiveModal(null)
                        // Store impersonation state
                        if (typeof window !== 'undefined') {
                          sessionStorage.setItem('impersonation_token', result.access_token)
                          sessionStorage.setItem('impersonation_email', result.target_email)
                          sessionStorage.setItem('impersonation_expires', result.expires_at)
                        }
                      } catch (e) {
                        toastError('Failed', e instanceof Error ? e.message : 'Unknown error')
                      } finally {
                        setActionLoading(false)
                      }
                    }} className="w-full px-4 py-2 bg-obsidian-600 text-white rounded-lg font-sans font-medium text-sm hover:bg-obsidian-700 disabled:opacity-40 transition-colors">
                      {actionLoading ? 'Generating...' : 'Start Impersonation'}
                    </button>
                  </>
                )}
                <button onClick={() => { setActiveModal(null); setFormData({}) }} className="mt-3 w-full px-4 py-2 border border-theme rounded-lg text-sm font-sans text-content-secondary hover:bg-surface-input transition-colors">
                  Cancel
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </main>
  )
}
