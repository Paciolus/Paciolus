'use client'

import Link from 'next/link'

/**
 * QuickActionsBar - Workspace Navigation
 * 
 * Horizontal action toolbar for primary workspace navigation.
 * Provides quick access to key features.
 * 
 * Design: Minimal, professional with Sage/Oatmeal accents.
 */

interface ActionButton {
    id: string
    label: string
    href: string
    icon: React.ReactNode
    variant: 'primary' | 'secondary'
}

const actions: ActionButton[] = [
    {
        id: 'history',
        label: 'View History',
        href: '/history',
        variant: 'secondary',
        icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
        ),
    },
    {
        id: 'portfolio',
        label: 'Portfolio',
        href: '/portfolio',
        variant: 'secondary',
        icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
        ),
    },
    {
        id: 'settings',
        label: 'Settings',
        href: '/settings',
        variant: 'secondary',
        icon: (
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
        ),
    },
]

export function QuickActionsBar() {
    return (
        <section className="py-6 px-6 border-b border-obsidian-600/30">
            <div className="max-w-5xl mx-auto">
                <div className="flex flex-wrap items-center gap-3">
                    <span className="text-oatmeal-400 text-sm font-sans font-medium mr-2 hidden sm:block">
                        Quick Actions:
                    </span>

                    {actions.map((action) => (
                        <Link
                            key={action.id}
                            href={action.href}
                            className={`
                inline-flex items-center gap-2 px-4 py-2 rounded-lg font-sans text-sm font-medium
                transition-all
                ${action.variant === 'primary'
                                    ? 'bg-sage-500/20 border border-sage-500/40 text-sage-300 hover:bg-sage-500/30 hover:border-sage-500/60'
                                    : 'bg-obsidian-800/50 border border-obsidian-600/50 text-oatmeal-300 hover:bg-obsidian-700/50 hover:border-obsidian-500/50'
                                }
              `}
                        >
                            {action.icon}
                            <span>{action.label}</span>
                        </Link>
                    ))}
                </div>
            </div>
        </section>
    )
}

export default QuickActionsBar
