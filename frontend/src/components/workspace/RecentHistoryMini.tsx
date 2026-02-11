'use client'

import { useEffect, useState } from 'react'
import Link from 'next/link'
import { apiGet } from '@/utils'

/**
 * RecentHistoryMini - Compact Activity Widget
 * Sprint 147: Migrated to apiGet for caching (5-min TTL) and retry.
 *
 * Displays recent assessment activity in workspace view.
 * Shows last 3-5 assessments with quick navigation to full history.
 *
 * Design: Compact card list with Surgical aesthetic.
 */

interface HistoryItem {
    id: number
    filename: string
    created_at: string
    was_balanced: boolean
    record_count: number
    anomaly_count: number
}

interface RecentHistoryMiniProps {
    token?: string
}

export function RecentHistoryMini({ token }: RecentHistoryMiniProps) {
    const [history, setHistory] = useState<HistoryItem[]>([])
    const [isLoading, setIsLoading] = useState(true)

    useEffect(() => {
        let cancelled = false

        async function fetchHistory() {
            if (!token) {
                setIsLoading(false)
                return
            }

            try {
                const { data, ok } = await apiGet<HistoryItem[]>(
                    '/activity/recent?limit=5',
                    token,
                )

                if (!cancelled && ok && data) {
                    setHistory(data)
                }
            } catch (error) {
                console.error('Failed to fetch recent history:', error)
            } finally {
                if (!cancelled) {
                    setIsLoading(false)
                }
            }
        }

        fetchHistory()

        return () => { cancelled = true }
    }, [token])

    return (
        <section className="py-12 px-6">
            <div className="max-w-5xl mx-auto">
                {/* Section Header */}
                <div className="flex items-center justify-between mb-6">
                    <div>
                        <h2 className="text-2xl font-serif font-bold text-oatmeal-200 mb-1">
                            Recent Activity
                        </h2>
                        <p className="text-oatmeal-400 text-sm font-sans">
                            Your latest diagnostic assessments
                        </p>
                    </div>
                    <Link
                        href="/history"
                        className="inline-flex items-center gap-2 px-4 py-2 bg-obsidian-800/50 border border-obsidian-600/50 rounded-lg text-oatmeal-300 text-sm font-sans font-medium hover:bg-obsidian-700/50 hover:border-obsidian-500/50 transition-all"
                    >
                        <span>View All</span>
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                    </Link>
                </div>

                {/* History List */}
                {isLoading ? (
                    <div className="space-y-3">
                        {[1, 2, 3].map((i) => (
                            <div key={i} className="bg-obsidian-800/30 border border-obsidian-600/30 rounded-lg p-4">
                                <div className="flex items-center justify-between">
                                    <div className="flex-1 space-y-2">
                                        <div className="w-48 h-4 bg-obsidian-700 animate-pulse rounded"></div>
                                        <div className="w-32 h-3 bg-obsidian-700 animate-pulse rounded"></div>
                                    </div>
                                    <div className="w-16 h-6 bg-obsidian-700 animate-pulse rounded"></div>
                                </div>
                            </div>
                        ))}
                    </div>
                ) : history.length === 0 ? (
                    <div className="bg-obsidian-800/30 border border-obsidian-600/30 rounded-xl p-12 text-center">
                        <svg className="w-12 h-12 text-oatmeal-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                        </svg>
                        <p className="text-oatmeal-400 font-sans mb-2">No assessments yet</p>
                        <p className="text-oatmeal-500 text-sm font-sans">
                            Upload your first trial balance to get started
                        </p>
                    </div>
                ) : (
                    <div className="space-y-3">
                        {history.map((item) => (
                            <div
                                key={item.id}
                                className="bg-obsidian-800/30 border border-obsidian-600/30 rounded-lg p-4 hover:bg-obsidian-800/50 hover:border-obsidian-600/50 transition-all cursor-pointer"
                            >
                                <div className="flex items-center justify-between">
                                    <div className="flex-1 min-w-0">
                                        <div className="flex items-center gap-3 mb-2">
                                            <h3 className="text-oatmeal-200 font-sans font-medium truncate">
                                                {item.filename}
                                            </h3>
                                            {item.was_balanced ? (
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-sage-500/10 border border-sage-500/20 rounded text-sage-400 text-xs font-sans font-medium">
                                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                                                    </svg>
                                                    Balanced
                                                </span>
                                            ) : (
                                                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-clay-500/10 border border-clay-500/20 rounded text-clay-400 text-xs font-sans font-medium">
                                                    <svg className="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                                                    </svg>
                                                    Out of Balance
                                                </span>
                                            )}
                                        </div>
                                        <div className="flex items-center gap-4 text-xs font-sans text-oatmeal-500">
                                            <span>
                                                {new Date(item.created_at).toLocaleDateString('en-US', {
                                                    month: 'short',
                                                    day: 'numeric',
                                                    hour: 'numeric',
                                                    minute: '2-digit'
                                                })}
                                            </span>
                                            <span>{item.record_count.toLocaleString()} rows</span>
                                            {item.anomaly_count > 0 && (
                                                <span className="text-clay-400">{item.anomaly_count} anomalies</span>
                                            )}
                                        </div>
                                    </div>
                                    <svg className="w-5 h-5 text-oatmeal-500 flex-shrink-0 ml-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                                    </svg>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </section>
    )
}

export default RecentHistoryMini
