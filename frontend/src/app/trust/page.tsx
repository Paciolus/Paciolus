'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'
import { MarketingNav, MarketingFooter } from '@/components/marketing'

const securityControls = [
  {
    title: 'TLS 1.3 Encryption',
    description: 'All data in transit is encrypted with TLS 1.3 end-to-end.',
    icon: (
      <svg className="w-7 h-7 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
  },
  {
    title: 'bcrypt Password Hashing',
    description: 'Passwords salted and hashed with 12 rounds of bcrypt.',
    icon: (
      <svg className="w-7 h-7 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
      </svg>
    ),
  },
  {
    title: 'JWT Authentication',
    description: 'Stateless, short-lived token-based session management.',
    icon: (
      <svg className="w-7 h-7 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
  {
    title: 'Multi-Tenant Isolation',
    description: 'User data segregated at the database level with row-level security.',
    icon: (
      <svg className="w-7 h-7 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4m0 5c0 2.21-3.582 4-8 4s-8-1.79-8-4" />
      </svg>
    ),
  },
  {
    title: 'Rate Limiting',
    description: 'Brute-force protection on all authentication and upload endpoints.',
    icon: (
      <svg className="w-7 h-7 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
      </svg>
    ),
  },
  {
    title: 'CSRF Protection',
    description: 'Cross-site request forgery tokens on all state-changing operations.',
    icon: (
      <svg className="w-7 h-7 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016zM12 9v2m0 4h.01" />
      </svg>
    ),
  },
]

const complianceItems = [
  {
    label: 'SOC 2 Type II',
    status: 'In Progress',
    detail: 'Expected Q3 2026',
    colorClass: 'text-oatmeal-400',
  },
  {
    label: 'GDPR',
    status: 'Compliant',
    detail: 'EU General Data Protection Regulation',
    colorClass: 'text-sage-400',
  },
  {
    label: 'CCPA',
    status: 'Compliant',
    detail: 'California Consumer Privacy Act',
    colorClass: 'text-sage-400',
  },
  {
    label: 'DPA',
    status: 'Available',
    detail: 'Enterprise tier',
    colorClass: 'text-oatmeal-300',
  },
]

const weStore = [
  'User account information (name, email)',
  'Client metadata (names, industries, fiscal year-ends)',
  'Engagement records (narratives only, no financial data)',
  'Anonymized usage statistics',
]

const weNeverStore = [
  'Trial balance data or account balances',
  'Journal entries, invoices, or payment records',
  'Uploaded CSV/Excel files',
  'Anomaly details with specific amounts',
]

const transparencyLinks = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
  { label: 'Zero-Storage Architecture', href: '/approach' },
]

const fadeUp = {
  initial: { opacity: 0, y: 24 },
  animate: { opacity: 1, y: 0 },
}

export default function TrustAndSecurity() {
  return (
    <div className="min-h-screen bg-gradient-obsidian">
      <MarketingNav />

      {/* 1. Hero Section */}
      <motion.section
        className="relative pt-32 pb-16 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="font-serif text-5xl md:text-6xl text-oatmeal-100 mb-6">
            Trust &amp; Security
          </h1>
          <p className="font-sans text-lg md:text-xl text-oatmeal-400 max-w-2xl mx-auto leading-relaxed">
            How we protect your data — and why we built it this way.
          </p>
        </div>
      </motion.section>

      {/* 2. Zero-Storage Hero Card */}
      <motion.section
        className="relative pb-16 px-6"
        {...fadeUp}
        transition={{ duration: 0.6, delay: 0.15, ease: 'easeOut' as const }}
        viewport={{ once: true }}
        whileInView={fadeUp.animate}
        initial={fadeUp.initial}
      >
        <div className="max-w-4xl mx-auto">
          <div className="bg-obsidian-800 border-2 border-sage-500/40 rounded-xl p-8 md:p-10 flex flex-col md:flex-row items-start gap-6">
            {/* Shield Icon */}
            <div className="flex-shrink-0 w-14 h-14 rounded-lg bg-sage-500/10 flex items-center justify-center">
              <svg className="w-8 h-8 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
              </svg>
            </div>
            <div className="flex-1">
              <h2 className="font-serif text-2xl md:text-3xl text-oatmeal-100 mb-3">
                Zero-Storage Architecture
              </h2>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-4">
                Your financial data never touches our database. Files are processed in ephemeral
                memory and destroyed within seconds.
              </p>
              <Link
                href="/approach"
                className="inline-flex items-center gap-2 font-sans text-sage-400 hover:text-sage-300 transition-colors group"
              >
                Learn how it works
                <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                </svg>
              </Link>
            </div>
          </div>
        </div>
      </motion.section>

      {/* 3. Security Controls Grid */}
      <section className="relative pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.h2
            className="font-serif text-3xl text-oatmeal-100 mb-10 text-center"
            {...fadeUp}
            transition={{ duration: 0.5, ease: 'easeOut' as const }}
            viewport={{ once: true }}
            whileInView={fadeUp.animate}
            initial={fadeUp.initial}
          >
            Security Controls
          </motion.h2>
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
            {securityControls.map((control, idx) => (
              <motion.div
                key={control.title}
                className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 hover:border-sage-500/30 transition-colors"
                initial={{ opacity: 0, y: 20 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ duration: 0.4, delay: idx * 0.08, ease: 'easeOut' as const }}
              >
                <div className="mb-4">{control.icon}</div>
                <h3 className="font-serif text-lg text-oatmeal-100 mb-2">{control.title}</h3>
                <p className="font-sans text-sm text-oatmeal-400 leading-relaxed">
                  {control.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* 4. Compliance Status */}
      <section className="relative pb-20 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.h2
            className="font-serif text-3xl text-oatmeal-100 mb-10 text-center"
            {...fadeUp}
            transition={{ duration: 0.5, ease: 'easeOut' as const }}
            viewport={{ once: true }}
            whileInView={fadeUp.animate}
            initial={fadeUp.initial}
          >
            Compliance Status
          </motion.h2>
          <motion.div
            className="bg-obsidian-800 border border-obsidian-600 rounded-xl overflow-hidden"
            {...fadeUp}
            transition={{ duration: 0.5, delay: 0.1, ease: 'easeOut' as const }}
            viewport={{ once: true }}
            whileInView={fadeUp.animate}
            initial={fadeUp.initial}
          >
            {complianceItems.map((item, idx) => (
              <div
                key={item.label}
                className={`flex items-center justify-between p-5 md:p-6 ${
                  idx < complianceItems.length - 1 ? 'border-b border-obsidian-700' : ''
                } ${idx % 2 === 1 ? 'bg-obsidian-800/50' : ''}`}
              >
                <div className="flex items-center gap-4">
                  <div className={`w-2.5 h-2.5 rounded-full flex-shrink-0 ${
                    item.colorClass === 'text-sage-400' ? 'bg-sage-400' :
                    item.colorClass === 'text-oatmeal-400' ? 'bg-oatmeal-400' :
                    'bg-oatmeal-300'
                  }`} />
                  <div>
                    <h3 className="font-serif text-oatmeal-100">{item.label}</h3>
                    <p className="font-sans text-sm text-oatmeal-500 mt-0.5">{item.detail}</p>
                  </div>
                </div>
                <span className={`font-sans text-sm font-medium ${item.colorClass}`}>
                  {item.status}
                </span>
              </div>
            ))}
          </motion.div>
        </div>
      </section>

      {/* 5. What We Store vs What We NEVER Store */}
      <section className="relative pb-20 px-6">
        <div className="max-w-5xl mx-auto">
          <motion.h2
            className="font-serif text-3xl text-oatmeal-100 mb-10 text-center"
            {...fadeUp}
            transition={{ duration: 0.5, ease: 'easeOut' as const }}
            viewport={{ once: true }}
            whileInView={fadeUp.animate}
            initial={fadeUp.initial}
          >
            Data Transparency
          </motion.h2>
          <div className="grid md:grid-cols-2 gap-6">
            {/* What We Store */}
            <motion.div
              className="bg-obsidian-800 border-l-4 border-sage-500 rounded-r-xl p-6 md:p-8"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
            >
              <h3 className="font-serif text-xl text-oatmeal-100 mb-6">What We Store</h3>
              <ul className="space-y-4">
                {weStore.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-sage-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="font-sans text-oatmeal-300 text-sm leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* What We NEVER Store */}
            <motion.div
              className="bg-obsidian-800 border-l-4 border-clay-500 rounded-r-xl p-6 md:p-8"
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
            >
              <h3 className="font-serif text-xl text-oatmeal-100 mb-6">What We NEVER Store</h3>
              <ul className="space-y-4">
                {weNeverStore.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-clay-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="font-sans text-oatmeal-300 text-sm leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>
        </div>
      </section>

      {/* 6. Transparency Section */}
      <section className="relative pb-24 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="bg-obsidian-800 border border-obsidian-600 rounded-xl p-8 md:p-10 text-center"
            {...fadeUp}
            transition={{ duration: 0.5, ease: 'easeOut' as const }}
            viewport={{ once: true }}
            whileInView={fadeUp.animate}
            initial={fadeUp.initial}
          >
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-3">Transparency</h2>
            <p className="font-sans text-oatmeal-400 mb-8 leading-relaxed">
              We believe in transparency. Review our policies:
            </p>
            <div className="flex flex-col sm:flex-row items-center justify-center gap-4 sm:gap-6">
              {transparencyLinks.map((link) => (
                <Link
                  key={link.href}
                  href={link.href}
                  className="inline-flex items-center gap-2 font-sans text-sage-400 hover:text-sage-300 transition-colors group"
                >
                  {link.label}
                  <svg className="w-4 h-4 transform group-hover:translate-x-1 transition-transform" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8l4 4m0 0l-4 4m4-4H3" />
                  </svg>
                </Link>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <MarketingFooter />
    </div>
  )
}
