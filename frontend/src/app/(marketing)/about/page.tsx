'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

/* ---------- Animation helpers ---------- */
const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: (i: number) => ({
    opacity: 1,
    y: 0,
    transition: { delay: i * 0.1, duration: 0.5, ease: 'easeOut' as const },
  }),
}

const staggerContainer = {
  hidden: {},
  visible: {
    transition: { staggerChildren: 0.12, delayChildren: 0.15 },
  },
}

const cardReveal = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.45, ease: 'easeOut' as const },
  },
}

/* ---------- Data ---------- */
const whatItIs = [
  'A data analytics platform for financial professionals',
  'A tool that identifies anomalies for auditor evaluation',
  'A workpaper-ready export system (PDF, Excel, CSV)',
  'Built on Zero-Storage architecture for maximum data privacy',
]

const whatItIsNot = [
  'Not an audit software that replaces professional judgment',
  'Not a system that provides assurance opinions',
  'Not a tool that generates audit evidence',
  'Not a platform that stores your financial data',
]

const zeroStorageCards = [
  {
    title: 'Security',
    description: 'No database to breach. Financial data is processed in-memory and never written to disk or persisted in any store.',
    icon: (
      <svg className="w-8 h-8 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
      </svg>
    ),
  },
  {
    title: 'Privacy',
    description: 'Zero retention by design. Once your session ends, all uploaded data is gone. There is nothing to subpoena, leak, or expose.',
    icon: (
      <svg className="w-8 h-8 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88" />
      </svg>
    ),
  },
  {
    title: 'Compliance',
    description: 'Simplified GDPR and CCPA posture. When you store nothing, data subject requests become trivial.',
    icon: (
      <svg className="w-8 h-8 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z" />
      </svg>
    ),
  },
]

const professionalsCards = [
  {
    title: 'Audit Background',
    description: 'Designed by professionals who understand ISA and PCAOB standards. Every workflow reflects how audit teams actually work.',
    icon: (
      <svg className="w-8 h-8 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5" />
      </svg>
    ),
  },
  {
    title: 'Professional Standards',
    description: 'Every test battery references applicable professional standards. Memos cite ISA 240, ISA 500, PCAOB AS 2401, and more.',
    icon: (
      <svg className="w-8 h-8 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 6.042A8.967 8.967 0 006 3.75c-1.052 0-2.062.18-3 .512v14.25A8.987 8.987 0 016 18c2.305 0 4.408.867 6 2.292m0-14.25a8.966 8.966 0 016-2.292c1.052 0 2.062.18 3 .512v14.25A8.987 8.987 0 0018 18a8.967 8.967 0 00-6 2.292m0-14.25v14.25" />
      </svg>
    ),
  },
  {
    title: 'Workpaper Ready',
    description: 'PDF memos with signoff lines, Excel exports with full underlying data, and CSV output for downstream analysis.',
    icon: (
      <svg className="w-8 h-8 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m2.25 0H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />
      </svg>
    ),
  },
]

/* ---------- Page Component ---------- */
export default function AboutPage() {
  return (
    <div className="relative z-10 min-h-screen bg-gradient-obsidian">
      {/* ===== Hero Section ===== */}
      <motion.section
        className="relative pt-32 pb-16 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="type-display text-oatmeal-100 mb-6">
            Why We Built Paciolus
          </h1>
          <p className="type-body-lg text-oatmeal-400 max-w-2xl mx-auto">
            Most analytics platforms are adapted for financial professionals. Paciolus was designed for them from the first line of code.
          </p>
        </div>
      </motion.section>

      {/* ===== Founding Motivation Blockquote ===== */}
      <motion.section
        className="px-6 pb-16"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3, ease: 'easeOut' as const }}
      >
        <div className="max-w-3xl mx-auto">
          <blockquote className="border-l-4 border-sage-500 bg-obsidian-800/50 rounded-r-lg pl-6 pr-8 py-6">
            <p className="font-serif text-xl md:text-2xl text-oatmeal-200 italic leading-relaxed">
              &ldquo;The moment when you need a defensible answer shouldn&rsquo;t depend on the size of your firm. We built Paciolus so it doesn&rsquo;t.&rdquo;
            </p>
          </blockquote>
        </div>
      </motion.section>

      {/* ===== What Paciolus Is vs Is NOT ===== */}
      <motion.section
        className="px-6 pb-20"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <div className="max-w-5xl mx-auto">
          <motion.h2
            className="type-headline text-oatmeal-100 text-center mb-12"
            variants={cardReveal}
          >
            What Paciolus Is &mdash; and What It Is Not
          </motion.h2>

          <div className="grid md:grid-cols-2 gap-8">
            {/* Left card — What It IS */}
            <motion.div
              className="bg-obsidian-800 border border-sage-500/30 rounded-lg p-8"
              variants={cardReveal}
            >
              <h3 className="font-serif text-xl text-sage-400 mb-6 flex items-center gap-3">
                <svg className="w-6 h-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                What Paciolus Is
              </h3>
              <ul className="space-y-4">
                {whatItIs.map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-sage-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="font-sans text-oatmeal-300 leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* Right card — What It Is NOT */}
            <motion.div
              className="bg-obsidian-800 border border-clay-500/30 rounded-lg p-8"
              variants={cardReveal}
            >
              <h3 className="font-serif text-xl text-clay-400 mb-6 flex items-center gap-3">
                <svg className="w-6 h-6 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                What Paciolus Is NOT
              </h3>
              <ul className="space-y-4">
                {whatItIsNot.map((item, i) => (
                  <li key={i} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-clay-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="font-sans text-oatmeal-300 leading-relaxed">{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* ===== Zero-Storage Commitment ===== */}
      <motion.section
        className="px-6 pb-20"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <div className="max-w-5xl mx-auto">
          <motion.div className="text-center mb-12" variants={cardReveal}>
            <h2 className="type-headline text-oatmeal-100 mb-4">
              Zero-Storage Commitment
            </h2>
            <p className="type-body text-oatmeal-400 max-w-2xl mx-auto">
              Paciolus processes financial data entirely in-memory. Nothing is written to disk,
              stored in a database, or retained after your session ends.{' '}
              <Link href="/approach" className="text-sage-400 hover:text-sage-300 underline transition-colors">
                Learn more about our technical approach
              </Link>.
            </p>
          </motion.div>

          <div className="grid md:grid-cols-3 gap-6">
            {zeroStorageCards.map((card, i) => (
              <motion.div
                key={card.title}
                className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 text-center"
                custom={i}
                variants={fadeUp}
              >
                <div className="flex justify-center mb-4">
                  {card.icon}
                </div>
                <h3 className="font-serif text-lg text-oatmeal-100 mb-3">{card.title}</h3>
                <p className="type-body-sm text-oatmeal-400">
                  {card.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ===== Built for Financial Professionals ===== */}
      <motion.section
        className="px-6 pb-20"
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
      >
        <div className="max-w-5xl mx-auto">
          <motion.h2
            className="type-headline text-oatmeal-100 text-center mb-12"
            variants={cardReveal}
          >
            Built for Financial Professionals
          </motion.h2>

          <div className="grid md:grid-cols-3 gap-6">
            {professionalsCards.map((card, i) => (
              <motion.div
                key={card.title}
                className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6"
                custom={i}
                variants={fadeUp}
              >
                <div className="mb-4">
                  {card.icon}
                </div>
                <h3 className="font-serif text-lg text-oatmeal-100 mb-3">{card.title}</h3>
                <p className="type-body-sm text-oatmeal-400">
                  {card.description}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ===== CTA Section ===== */}
      <motion.section
        className="px-6 pb-24"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="type-headline text-oatmeal-100 mb-4">
            Start your first analysis.
          </h2>
          <p className="type-body text-oatmeal-400 mb-8">
            Seven-day trial. All twelve tools. Your client&apos;s data is never stored.
          </p>
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="inline-block bg-sage-600 hover:bg-sage-500 text-oatmeal-100 font-sans font-medium py-3 px-8 rounded-lg transition-colors"
            >
              Start Free Trial
            </Link>
            <Link
              href="/approach"
              className="inline-block font-sans text-sage-400 hover:text-sage-300 transition-colors underline"
            >
              Learn Our Approach
            </Link>
          </div>
        </div>
      </motion.section>

    </div>
  )
}
