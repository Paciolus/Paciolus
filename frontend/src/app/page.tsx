'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'
import { useAuth } from '@/context/AuthContext'
import { ProfileDropdown } from '@/components/auth'
import { FeaturePillars, ProcessTimeline, DemoZone } from '@/components/marketing'

const toolCards = [
  {
    title: 'Trial Balance Diagnostics',
    description: 'Upload a trial balance for instant anomaly detection, ratio analysis, lead sheet mapping, and financial statement generation.',
    href: '/tools/trial-balance',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z" />
      </svg>
    ),
    badge: 'Headliner',
    badgeColor: 'bg-sage-500/15 text-sage-400 border-sage-500/30',
  },
  {
    title: 'Multi-Period Comparison',
    description: 'Compare up to three trial balance periods side-by-side with variance analysis and budget tracking.',
    href: '/tools/multi-period',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
      </svg>
    ),
    badge: 'Tool 2',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'Journal Entry Testing',
    description: 'Automated GL analysis with Benford\'s Law, structural validation, and statistical anomaly detection.',
    href: '/tools/journal-entry-testing',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    badge: 'Tool 3',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'AP Payment Testing',
    description: 'Duplicate payment detection, vendor analysis, and fraud indicators across your accounts payable register.',
    href: '/tools/ap-testing',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7v8a2 2 0 002 2h6M8 7V5a2 2 0 012-2h4.586a1 1 0 01.707.293l4.414 4.414a1 1 0 01.293.707V15a2 2 0 01-2 2h-2M8 7H6a2 2 0 00-2 2v10a2 2 0 002 2h8a2 2 0 002-2v-2" />
      </svg>
    ),
    badge: 'Tool 4',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'Bank Reconciliation',
    description: 'Match bank statement transactions against your general ledger with automated reconciliation and difference analysis.',
    href: '/tools/bank-rec',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16V4m0 0L3 8m4-4l4 4m6 0v12m0 0l4-4m-4 4l-4-4" />
      </svg>
    ),
    badge: 'Tool 5',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'Payroll & Employee Testing',
    description: 'Ghost employee detection, duplicate payments, and payroll anomaly analysis across your payroll register.',
    href: '/tools/payroll-testing',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
      </svg>
    ),
    badge: 'Tool 6',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'Three-Way Match Validator',
    description: 'Match purchase orders, invoices, and receipts to validate AP completeness and detect procurement variances.',
    href: '/tools/three-way-match',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    badge: 'Tool 7',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'Revenue Testing',
    description: 'ISA 240 revenue recognition analysis — 12-test battery for structural, statistical, and advanced anomaly indicators.',
    href: '/tools/revenue-testing',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    badge: 'Tool 8',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'AR Aging Analysis',
    description: 'Receivables aging analysis with dual-input TB + sub-ledger support — concentration risk, stale balances, and allowance adequacy indicators.',
    href: '/tools/ar-aging',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
    badge: 'Tool 9',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
  {
    title: 'Fixed Asset Testing',
    description: 'PP&E register analysis with depreciation, useful life, and residual value anomaly detection per IAS 16 and ISA 540.',
    href: '/tools/fixed-assets',
    icon: (
      <svg className="w-7 h-7" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
      </svg>
    ),
    badge: 'Tool 10',
    badgeColor: 'bg-oatmeal-500/10 text-oatmeal-400 border-oatmeal-500/20',
  },
] as const

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.12 },
  },
}

const itemVariants = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0, transition: { type: 'spring' as const, stiffness: 200, damping: 20 } },
}

/**
 * Platform Homepage (Sprint 66)
 *
 * Marketing landing page showcasing the Paciolus suite of audit tools.
 */
export default function HomePage() {
  const { user, isAuthenticated, isLoading: authLoading, logout } = useAuth()

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-obsidian-900/90 backdrop-blur-lg border-b border-obsidian-600/30 z-50">
        <div className="max-w-6xl mx-auto px-6 py-4 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3 group">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
            />
          </Link>
          <div className="flex items-center gap-4">
            <Link
              href="/tools/trial-balance"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              TB Diagnostics
            </Link>
            <Link
              href="/tools/multi-period"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Multi-Period
            </Link>
            <Link
              href="/tools/journal-entry-testing"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              JE Testing
            </Link>
            <Link
              href="/tools/ap-testing"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              AP Testing
            </Link>
            <Link
              href="/tools/bank-rec"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Bank Rec
            </Link>
            <Link
              href="/tools/payroll-testing"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Payroll
            </Link>
            <Link
              href="/tools/three-way-match"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Three-Way Match
            </Link>
            <Link
              href="/tools/revenue-testing"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Revenue
            </Link>
            <Link
              href="/tools/ar-aging"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              AR Aging
            </Link>
            <Link
              href="/tools/fixed-assets"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Fixed Assets
            </Link>
            <Link
              href="/engagements"
              className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
            >
              Workspaces
            </Link>
            <div className="ml-4 pl-4 border-l border-obsidian-600/30">
              {authLoading ? null : isAuthenticated && user ? (
                <ProfileDropdown user={user} onLogout={logout} />
              ) : (
                <Link
                  href="/login"
                  className="text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
                >
                  Sign In
                </Link>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Hero Section */}
      <section className="pt-32 pb-20 px-6">
        <div className="max-w-4xl mx-auto text-center">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
          >
            <div className="inline-flex items-center gap-2 px-4 py-2 rounded-full bg-sage-500/10 border border-sage-500/20 mb-8">
              <div className="w-2 h-2 bg-sage-400 rounded-full" />
              <span className="text-sage-300 text-sm font-sans font-medium">Professional Audit Intelligence</span>
            </div>

            <h1 className="font-serif text-5xl md:text-6xl text-oatmeal-100 mb-6 leading-tight">
              The Complete Audit
              <br />
              <span className="text-sage-400">Intelligence Suite</span>
            </h1>

            <p className="font-sans text-lg text-oatmeal-400 max-w-2xl mx-auto mb-10 leading-relaxed">
              Professional-grade diagnostic tools for financial professionals.
              Zero-Storage architecture ensures your client data is never saved.
              Ten integrated tools. One diagnostic workspace. One platform.
            </p>

            <div className="flex items-center justify-center gap-4">
              <Link
                href="/tools/trial-balance"
                className="px-8 py-3.5 bg-sage-500/20 border border-sage-500/40 rounded-xl text-sage-300 font-sans font-medium hover:bg-sage-500/30 transition-colors"
              >
                Explore Our Tools
              </Link>
              {!isAuthenticated && (
                <Link
                  href="/register"
                  className="px-8 py-3.5 bg-obsidian-700 border border-obsidian-500/40 rounded-xl text-oatmeal-300 font-sans font-medium hover:bg-obsidian-600 transition-colors"
                >
                  Get Started Free
                </Link>
              )}
            </div>
          </motion.div>
        </div>
      </section>

      {/* Tool Showcase */}
      <section className="py-16 px-6">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-serif text-2xl text-oatmeal-200 mb-3">Ten Tools. One Workspace.</h2>
            <p className="font-sans text-oatmeal-500 text-sm max-w-lg mx-auto">
              Each tool is purpose-built for a specific diagnostic workflow. Use them independently or tie them together in a Diagnostic Workspace.
            </p>
          </div>

          <motion.div
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true, margin: '-80px' }}
            className="grid grid-cols-1 md:grid-cols-3 gap-6"
          >
            {toolCards.map((tool) => (
              <motion.div key={tool.href} variants={itemVariants}>
                <Link
                  href={tool.href}
                  className="group block bg-obsidian-800/50 border border-obsidian-600/30 rounded-2xl p-7 hover:border-obsidian-500/50 hover:bg-obsidian-800/70 transition-all duration-200"
                >
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-12 h-12 rounded-xl bg-obsidian-700/50 flex items-center justify-center text-oatmeal-400 group-hover:text-sage-400 transition-colors">
                      {tool.icon}
                    </div>
                    <span className={`px-2.5 py-1 rounded-full text-[10px] font-sans font-medium border ${tool.badgeColor}`}>
                      {tool.badge}
                    </span>
                  </div>
                  <h3 className="font-serif text-lg text-oatmeal-200 mb-2 group-hover:text-oatmeal-100 transition-colors">
                    {tool.title}
                  </h3>
                  <p className="font-sans text-sm text-oatmeal-500 leading-relaxed">
                    {tool.description}
                  </p>
                  <div className="mt-4 flex items-center gap-1.5 text-sage-500 group-hover:text-sage-400 transition-colors">
                    <span className="font-sans text-sm">Try it</span>
                    <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                </Link>
              </motion.div>
            ))}
          </motion.div>

          {/* Diagnostic Workspace CTA */}
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ delay: 0.3 }}
            className="mt-10"
          >
            <Link
              href="/engagements"
              className="block bg-obsidian-800/50 border border-sage-500/20 rounded-2xl p-8 hover:border-sage-500/40 hover:bg-obsidian-800/70 transition-all duration-200 group"
            >
              <div className="flex flex-col md:flex-row items-start md:items-center gap-6">
                <div className="w-14 h-14 rounded-xl bg-sage-500/10 flex items-center justify-center text-sage-400 group-hover:bg-sage-500/20 transition-colors shrink-0">
                  <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                  </svg>
                </div>
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="font-serif text-xl text-oatmeal-200 group-hover:text-oatmeal-100 transition-colors">
                      Diagnostic Workspace
                    </h3>
                    <span className="px-2.5 py-1 rounded-full text-[10px] font-sans font-medium border bg-sage-500/15 text-sage-400 border-sage-500/30">
                      New
                    </span>
                  </div>
                  <p className="font-sans text-sm text-oatmeal-500 leading-relaxed max-w-2xl">
                    Tie all ten tools together in a single engagement workflow. Set materiality thresholds, track follow-up items, generate workpaper indices, and export diagnostic packages — all without storing financial data.
                  </p>
                </div>
                <div className="flex items-center gap-1.5 text-sage-500 group-hover:text-sage-400 transition-colors shrink-0">
                  <span className="font-sans text-sm">Open Workspace</span>
                  <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                </div>
              </div>
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Feature Pillars */}
      <FeaturePillars />

      {/* Process Timeline */}
      <ProcessTimeline />

      {/* Demo Zone */}
      <DemoZone />

      {/* Footer */}
      <footer className="border-t border-obsidian-600/30 py-8 px-6">
        <div className="max-w-5xl mx-auto flex flex-col md:flex-row items-center justify-between gap-4">
          <p className="font-sans text-xs text-oatmeal-600">
            Paciolus — Professional Audit Intelligence Suite
          </p>
          <p className="font-sans text-xs text-oatmeal-600 italic">
            &ldquo;Particularis de Computis et Scripturis&rdquo;
          </p>
        </div>
      </footer>
    </main>
  )
}
