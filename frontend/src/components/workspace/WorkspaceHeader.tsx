'use client'

import { useEffect, useState } from 'react'
import type { User } from '@/contexts/AuthContext'
import { apiGet } from '@/utils'

/**
 * WorkspaceHeader - Authenticated User Welcome
 * Sprint 147: Migrated to apiGet for caching (1-min TTL) and retry.
 *
 * Replaces the Hero section for authenticated users.
 * Displays welcome message, dashboard stats, and primary action.
 *
 * Design: Surgical/Advisory aesthetic with Oat & Obsidian palette.
 */

interface DashboardStats {
    total_clients: number
    assessments_today: number
    last_assessment_date: string | null
    total_assessments: number
}

interface WorkspaceHeaderProps {
    user: User
    token?: string
}

export function WorkspaceHeader({ user, token }: WorkspaceHeaderProps) {
    const [stats, setStats] = useState<DashboardStats | null>(null)
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        let cancelled = false

        async function fetchStats() {
            if (!token) {
                setIsLoading(false)
                return
            }

            try {
                const { data, ok } = await apiGet<DashboardStats>(
                    '/dashboard/stats',
                    token,
                )

                if (!cancelled && ok && data) {
                    setStats(data)
                }
            } catch (error) {
                console.error('Failed to fetch dashboard stats:', error)
            } finally {
                if (!cancelled) {
                    setIsLoading(false)
                }
            }
        }

        fetchStats()

        return () => { cancelled = true }
    }, [token])

    return (
        <section className="pt-32 pb-12 px-6">
            <div className="max-w-5xl mx-auto">
                {/* Welcome Message */}
                <div className="mb-8">
                    <div className="inline-flex items-center gap-2 bg-sage-500/10 border border-sage-500/20 rounded-full px-4 py-1.5 mb-4">
                        <span className="w-2 h-2 bg-sage-400 rounded-full animate-pulse"></span>
                        <span className="text-sage-300 text-sm font-sans font-medium">Workspace Active</span>
                    </div>

                    <h1 className="text-4xl md:text-5xl font-serif font-bold text-oatmeal-200 mb-3">
                        Welcome back, <span className="text-sage-400">{user.name || user.email.split('@')[0]}</span>
                    </h1>
                    <p className="text-xl text-oatmeal-400 font-sans">
                        Your diagnostic command center is ready.
                    </p>
                </div>

                {/* Quick Stats Dashboard */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    {/* Assessments Today */}
                    <div className="bg-obsidian-800/50 border border-obsidian-600/50 border-l-4 border-l-sage-600/60 rounded-xl p-6 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-oatmeal-400 text-sm font-sans font-medium">Today</span>
                            <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                            </svg>
                        </div>
                        {isLoading ? (
                            <div className="w-16 h-8 bg-obsidian-700 animate-pulse rounded"></div>
                        ) : (
                            <p className="text-3xl font-serif font-bold text-oatmeal-100">
                                {stats?.assessments_today ?? 0}
                            </p>
                        )}
                        <p className="text-oatmeal-500 text-xs font-sans mt-1">Assessments</p>
                    </div>

                    {/* Total Clients */}
                    <div className="bg-obsidian-800/50 border border-obsidian-600/50 border-l-4 border-l-sage-600/60 rounded-xl p-6 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-oatmeal-400 text-sm font-sans font-medium">Portfolio</span>
                            <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
                            </svg>
                        </div>
                        {isLoading ? (
                            <div className="w-16 h-8 bg-obsidian-700 animate-pulse rounded"></div>
                        ) : (
                            <p className="text-3xl font-serif font-bold text-oatmeal-100">
                                {stats?.total_clients ?? 0}
                            </p>
                        )}
                        <p className="text-oatmeal-500 text-xs font-sans mt-1">Clients</p>
                    </div>

                    {/* Last Assessment */}
                    <div className="bg-obsidian-800/50 border border-obsidian-600/50 border-l-4 border-l-sage-600/60 rounded-xl p-6 backdrop-blur-sm">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-oatmeal-400 text-sm font-sans font-medium">Activity</span>
                            <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                            </svg>
                        </div>
                        {isLoading ? (
                            <div className="w-24 h-8 bg-obsidian-700 animate-pulse rounded"></div>
                        ) : stats?.last_assessment_date ? (
                            <p className="text-lg font-sans font-semibold text-oatmeal-100">
                                {new Date(stats.last_assessment_date).toLocaleDateString('en-US', {
                                    month: 'short',
                                    day: 'numeric',
                                    hour: 'numeric',
                                    minute: '2-digit'
                                })}
                            </p>
                        ) : (
                            <p className="text-lg font-sans font-semibold text-oatmeal-500">
                                No activity
                            </p>
                        )}
                        <p className="text-oatmeal-500 text-xs font-sans mt-1">Last Assessment</p>
                    </div>
                </div>
            </div>
        </section>
    )
}

export default WorkspaceHeader
