'use client'

/**
 * Team Management Page — Phase LXIX: Pricing v3.
 *
 * Organization member management, invites, and seat usage.
 * Gated to Professional/Enterprise users with owner/admin role.
 */

import { useCallback, useEffect, useState } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { useAuthSession } from '@/contexts/AuthSessionContext'
import { FeatureGate } from '@/components/shared/FeatureGate'
import { apiGet, apiPost, apiPut, apiDelete } from '@/utils/apiClient'

interface OrgMember {
  id: number
  user_id: number
  user_name: string
  user_email: string
  role: 'owner' | 'admin' | 'member'
  joined_at: string
}

interface OrgInvite {
  id: number
  invitee_email: string
  role: string
  status: string
  created_at: string
  expires_at: string
}

interface OrgInfo {
  id: number
  name: string
  slug: string
  member_count: number
}

export default function TeamPage() {
  const router = useRouter()
  const { user, isAuthenticated, isLoading: authLoading, token } = useAuthSession()
  const [org, setOrg] = useState<OrgInfo | null>(null)
  const [members, setMembers] = useState<OrgMember[]>([])
  const [invites, setInvites] = useState<OrgInvite[]>([])
  const [inviteEmail, setInviteEmail] = useState('')
  const [inviteRole, setInviteRole] = useState('member')
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [actionLoading, setActionLoading] = useState(false)

  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login')
    }
  }, [authLoading, isAuthenticated, router])

  const fetchData = useCallback(async () => {
    if (!token) return
    setIsLoading(true)
    setError(null)
    try {
      const [orgRes, membersRes, invitesRes] = await Promise.all([
        apiGet<OrgInfo>('/organization', token),
        apiGet<OrgMember[]>('/organization/members', token),
        apiGet<OrgInvite[]>('/organization/invites', token),
      ])
      if (orgRes.ok && orgRes.data) {
        setOrg(orgRes.data)
      } else {
        setOrg(null)
      }
      if (membersRes.ok && membersRes.data) {
        setMembers(membersRes.data)
      }
      if (invitesRes.ok && invitesRes.data) {
        setInvites(invitesRes.data)
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load organization data.'
      setError(msg)
    } finally {
      setIsLoading(false)
    }
  }, [token])

  useEffect(() => {
    if (isAuthenticated) {
      fetchData()
    }
  }, [isAuthenticated, fetchData])

  async function handleInvite() {
    if (!inviteEmail.trim() || !token) return
    setActionLoading(true)
    setError(null)
    try {
      const res = await apiPost('/organization/invite', token, { email: inviteEmail.trim(), role: inviteRole })
      if (!res.ok) {
        setError(res.error ?? 'Failed to send invite.')
        return
      }
      setInviteEmail('')
      await fetchData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to send invite.')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleRevokeInvite(inviteId: number) {
    if (!token) return
    setActionLoading(true)
    try {
      const res = await apiDelete(`/organization/invites/${inviteId}`, token)
      if (!res.ok) setError(res.error ?? 'Failed to revoke invite.')
      else await fetchData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to revoke invite.')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleRemoveMember(memberId: number) {
    if (!token) return
    setActionLoading(true)
    try {
      const res = await apiDelete(`/organization/members/${memberId}`, token)
      if (!res.ok) setError(res.error ?? 'Failed to remove member.')
      else await fetchData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to remove member.')
    } finally {
      setActionLoading(false)
    }
  }

  async function handleChangeRole(memberId: number, newRole: string) {
    if (!token) return
    setActionLoading(true)
    try {
      const res = await apiPut(`/organization/members/${memberId}/role`, token, { role: newRole })
      if (!res.ok) setError(res.error ?? 'Failed to update role.')
      else await fetchData()
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Failed to update role.')
    } finally {
      setActionLoading(false)
    }
  }

  if (authLoading) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
      </div>
    )
  }

  const currentMember = members.find(m => m.user_id === user?.id)
  const isAdminOrOwner = currentMember?.role === 'owner' || currentMember?.role === 'admin'

  return (
    <FeatureGate feature="admin_dashboard">
      <main id="main-content" className="min-h-screen bg-surface-page pt-24 pb-16 px-6">
        <div className="max-w-3xl mx-auto">
          {/* Breadcrumb */}
          <div className="flex items-center gap-2 text-content-tertiary text-sm font-sans mb-4">
            <Link href="/" className="hover:text-content-secondary transition-colors">Home</Link>
            <span>/</span>
            <Link href="/settings" className="hover:text-content-secondary transition-colors">Settings</Link>
            <span>/</span>
            <span className="text-content-secondary">Team</span>
          </div>

          <h1 className="text-3xl font-serif font-bold text-content-primary mb-2">
            Team Management
          </h1>
          <p className="text-content-secondary font-sans mb-8">
            Manage your organization members and invites.
          </p>

          {error && (
            <div className="bg-clay-50 border border-clay-200 text-clay-700 rounded-lg p-3 mb-6 text-sm font-sans" role="alert">
              {error}
            </div>
          )}

          {isLoading ? (
            <div className="bg-surface-card border border-theme rounded-lg p-6">
              <div className="animate-pulse space-y-3">
                <div className="h-6 bg-oatmeal-200 rounded-sm w-1/3" />
                <div className="h-4 bg-oatmeal-200 rounded-sm w-1/2" />
              </div>
            </div>
          ) : !org ? (
            <div className="bg-surface-card border border-theme rounded-lg p-8 text-center">
              <h2 className="font-serif text-xl text-content-primary mb-3">No Organization</h2>
              <p className="text-content-secondary mb-4">
                You are not part of an organization. Organizations are automatically created when you subscribe to a Professional or Enterprise plan.
              </p>
              <Link
                href="/pricing"
                className="inline-block px-6 py-3 bg-sage-600 text-oatmeal-50 rounded-lg font-sans font-medium hover:bg-sage-700 transition-colors"
              >
                View Plans
              </Link>
            </div>
          ) : (
            <>
              {/* Org Info */}
              <div className="bg-surface-card border border-theme rounded-lg p-6 mb-6">
                <h2 className="font-serif text-lg text-content-primary mb-2">{org.name}</h2>
                <p className="text-sm text-content-muted font-sans">
                  {org.member_count} member{org.member_count !== 1 ? 's' : ''}
                </p>
              </div>

              {/* Members */}
              <div className="bg-surface-card border border-theme rounded-lg p-6 mb-6">
                <h2 className="font-serif text-lg text-content-primary mb-4">Members</h2>
                <div className="space-y-3">
                  {members.map((member) => (
                    <div key={member.id} className="flex items-center justify-between py-2 border-b border-theme last:border-b-0">
                      <div>
                        <p className="font-sans text-sm text-content-primary font-medium">
                          {member.user_name}
                          {member.user_id === user?.id && (
                            <span className="ml-2 text-xs text-content-muted">(you)</span>
                          )}
                        </p>
                        <p className="font-sans text-xs text-content-muted">{member.user_email}</p>
                      </div>
                      <div className="flex items-center gap-3">
                        <span className={`text-xs font-sans font-medium px-2 py-0.5 rounded-full border ${
                          member.role === 'owner'
                            ? 'bg-sage-50 text-sage-700 border-sage-200'
                            : member.role === 'admin'
                              ? 'bg-oatmeal-200 text-content-secondary border-theme'
                              : 'bg-surface-input text-content-muted border-theme'
                        }`}>
                          {member.role}
                        </span>
                        {isAdminOrOwner && member.role !== 'owner' && member.user_id !== user?.id && (
                          <div className="flex gap-2">
                            {currentMember?.role === 'owner' && (
                              <select
                                value={member.role}
                                onChange={(e) => handleChangeRole(member.id, e.target.value)}
                                disabled={actionLoading}
                                className="text-xs font-sans border border-theme rounded-sm px-2 py-1 bg-surface-page text-content-primary"
                              >
                                <option value="admin">Admin</option>
                                <option value="member">Member</option>
                              </select>
                            )}
                            <button
                              onClick={() => handleRemoveMember(member.id)}
                              disabled={actionLoading}
                              className="text-xs font-sans text-clay-600 hover:text-clay-700 disabled:opacity-50"
                            >
                              Remove
                            </button>
                          </div>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Invite Form */}
              {isAdminOrOwner && (
                <div className="bg-surface-card border border-theme rounded-lg p-6 mb-6">
                  <h2 className="font-serif text-lg text-content-primary mb-4">Invite Member</h2>
                  <div className="flex gap-3">
                    <input
                      type="email"
                      value={inviteEmail}
                      onChange={(e) => setInviteEmail(e.target.value)}
                      placeholder="Email address"
                      className="flex-1 px-3 py-2 border border-theme rounded-sm bg-surface-page text-content-primary font-sans text-sm placeholder:text-content-muted focus:outline-hidden focus:ring-1 focus:ring-sage-500"
                    />
                    <select
                      value={inviteRole}
                      onChange={(e) => setInviteRole(e.target.value)}
                      className="px-3 py-2 border border-theme rounded-sm bg-surface-page text-content-primary font-sans text-sm"
                    >
                      <option value="member">Member</option>
                      <option value="admin">Admin</option>
                    </select>
                    <button
                      onClick={handleInvite}
                      disabled={actionLoading || !inviteEmail.trim()}
                      className="px-4 py-2 bg-sage-600 text-oatmeal-50 rounded-lg font-sans text-sm font-medium hover:bg-sage-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                      {actionLoading ? 'Sending...' : 'Send Invite'}
                    </button>
                  </div>
                </div>
              )}

              {/* Pending Invites */}
              {isAdminOrOwner && invites.length > 0 && (
                <div className="bg-surface-card border border-theme rounded-lg p-6">
                  <h2 className="font-serif text-lg text-content-primary mb-4">Pending Invites</h2>
                  <div className="space-y-3">
                    {invites.map((invite) => (
                      <div key={invite.id} className="flex items-center justify-between py-2 border-b border-theme last:border-b-0">
                        <div>
                          <p className="font-sans text-sm text-content-primary">{invite.invitee_email}</p>
                          <p className="font-sans text-xs text-content-muted">
                            Expires {new Date(invite.expires_at).toLocaleDateString()}
                          </p>
                        </div>
                        <button
                          onClick={() => handleRevokeInvite(invite.id)}
                          disabled={actionLoading}
                          className="text-xs font-sans text-clay-600 hover:text-clay-700 disabled:opacity-50"
                        >
                          Revoke
                        </button>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </main>
    </FeatureGate>
  )
}
