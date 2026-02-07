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
              Five integrated tools. One platform.
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
            <h2 className="font-serif text-2xl text-oatmeal-200 mb-3">Five Tools. One Platform.</h2>
            <p className="font-sans text-oatmeal-500 text-sm max-w-lg mx-auto">
              Each tool is purpose-built for a specific audit workflow. Use them independently or together.
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
