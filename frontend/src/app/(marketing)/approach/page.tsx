import Link from 'next/link'
import * as motion from '@/components/ui/motionClient'
import { PREVIEW_CACHE, RETENTION_STATEMENT, SHARE_RETENTION, STORAGE_STATEMENT, WE_DONT_KEEP, WE_KEEP } from '@/content/storage-statement'
import { marketingFadeUp } from '@/lib/motion'

const stagger = {
  visible: {
    transition: {
      staggerChildren: 0.12,
    },
  },
}

const flowSteps = [
  {
    label: 'Upload',
    description: 'You upload a file (CSV, Excel, TSV, TXT, QBO, OFX, IIF, PDF, or ODS)',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M7 16a4 4 0 01-.88-7.903A5 5 0 1115.9 6L16 6a5 5 0 011 9.9M15 13l-3-3m0 0l-3 3m3-3v12" />
      </svg>
    ),
  },
  {
    label: 'Process',
    description: 'The uploaded file is parsed in memory',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
      </svg>
    ),
  },
  {
    label: 'Display',
    description: 'Results stream to your browser',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 17L9 20l-1 1h8l-1-1-.75-3M3 13h18M5 17h14a2 2 0 002-2V5a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
      </svg>
    ),
  },
  {
    label: 'Released',
    description: 'The uploaded file is released from memory; a summary is saved',
    icon: (
      <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
  },
]

const howItWorksSteps = [
  'You upload a trial balance, journal entries, or financial document',
  'Our server reads the file into memory',
  'Analytics run: anomaly detection, ratio analysis, test batteries',
  'Results are returned to your browser',
  'The uploaded file is released from memory and not kept. A summary (category totals, ratios, row counts, flagged account names) is saved to your history',
]

// Sprint 861: the "Traditional SaaS vs Paciolus" comparison was unsourced.
// This table says only what happens to each kind of data.
const dataRows = [
  { what: 'Uploaded file', where: 'Server memory', howLong: 'For the request. A previewed PDF or workbook: up to 10 minutes' },
  { what: 'Account and client list', where: 'Our database', howLong: 'While your account is open' },
  { what: 'Analysis summary (totals, ratios, row counts, flagged account names)', where: 'Our database', howLong: 'While your account is open' },
  { what: 'What you enter in an engagement', where: 'Our database', howLong: 'While your account is open' },
  { what: 'Report you share by link (the complete file)', where: 'Our storage provider', howLong: 'Up to 24 hours (Professional) or 48 hours (Enterprise), then deleted' },
]

// Sprint 861: one source with the Trust page (content/storage-statement.ts).
const weStore = WE_KEEP
const weDontKeep = WE_DONT_KEEP

const securityAdvantages = [
  'Uploaded files are not kept, so a breach of our database would not expose them',
  'The database does hold what you enter in an engagement, including misstatement amounts and analytical expectations',
  `A report you share by link is held by our storage provider for ${SHARE_RETENTION}`,
]

const tradeOffs = [
  'History keeps summaries only — to re-run a test you upload the file again',
  'Line-level detail (individual flagged entries) lives in the exports you download, not in your Paciolus history',
  'Trend views use saved summary totals, not your original files',
]

export default function ApproachPage() {
  return (
    <main id="main-content" className="relative z-10 min-h-screen bg-gradient-obsidian">
      {/* 1. Hero Section */}
      <motion.section
        className="relative pt-32 pb-16 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="font-serif text-4xl md:text-5xl lg:text-6xl text-oatmeal-100 mb-6">
            How We Handle Your Data
          </h1>
          <p className="font-sans text-lg md:text-xl text-oatmeal-400 max-w-2xl mx-auto leading-relaxed">
            {STORAGE_STATEMENT} Here is exactly what, and for how long.
          </p>
        </div>
      </motion.section>

      {/* 2. Data Flow Diagram */}
      <motion.section
        className="relative pb-20 px-6"
        variants={stagger}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-80px' }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 md:gap-0 items-center">
            {flowSteps.map((step, idx) => (
              <motion.div key={step.label} variants={marketingFadeUp} transition={{ duration: 0.5, ease: 'easeOut' as const }} className="flex flex-col items-center relative">
                {/* Arrow between steps (desktop only) */}
                {idx > 0 && (
                  <div className="hidden md:block absolute -left-4 top-1/2 -translate-y-1/2 -translate-x-1/2 z-10">
                    <svg className="w-6 h-6 text-theme-success-text" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  </div>
                )}
                {/* Mobile arrow (between rows) */}
                {idx > 0 && (
                  <div className="md:hidden mb-3">
                    <svg className="w-6 h-6 text-theme-success-text mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
                    </svg>
                  </div>
                )}
                <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 w-full text-center hover:border-sage-500/40 transition-colors">
                  <div className="text-sage-400 mb-3 flex justify-center">{step.icon}</div>
                  <h3 className="font-serif text-lg text-oatmeal-100 mb-1">{step.label}</h3>
                  <p className="font-sans text-sm text-oatmeal-400">{step.description}</p>
                </div>
              </motion.div>
            ))}
          </div>

          <p className="mt-6 text-center font-sans text-sm text-oatmeal-400">{PREVIEW_CACHE}</p>
        </div>
      </motion.section>

      {/* 3. How It Works — Numbered Steps */}
      <motion.section
        className="relative pb-20 px-6"
        variants={stagger}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-80px' }}
      >
        <div className="max-w-4xl mx-auto">
          <motion.h2
            variants={marketingFadeUp}
            transition={{ duration: 0.5, ease: 'easeOut' as const }}
            className="font-serif text-3xl md:text-4xl text-oatmeal-100 mb-10 text-center"
          >
            How It Works
          </motion.h2>

          <div className="space-y-4">
            {howItWorksSteps.map((step, idx) => (
              <motion.div
                key={idx}
                variants={marketingFadeUp}
                transition={{ duration: 0.5, ease: 'easeOut' as const }}
                className={`bg-obsidian-800 border rounded-lg p-5 flex items-start gap-4 ${
                  idx === howItWorksSteps.length - 1
                    ? 'border-sage-500/40 bg-sage-500/10'
                    : 'border-obsidian-600'
                }`}
              >
                <span className="font-mono text-lg text-sage-400 flex-shrink-0 w-8 h-8 rounded-full bg-sage-500/20 flex items-center justify-center">
                  {idx + 1}
                </span>
                <p className={`font-sans leading-relaxed ${
                  idx === howItWorksSteps.length - 1
                    ? 'text-sage-300 font-medium'
                    : 'text-oatmeal-300'
                }`}>
                  {step}
                </p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* 4. Data table (Sprint 861) */}
      <motion.section
        className="relative pb-20 px-6"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-4xl mx-auto">
          <h2 className="font-serif text-3xl md:text-4xl text-oatmeal-100 mb-10 text-center">
            What Happens to Each Kind of Data
          </h2>

          <div className="overflow-x-auto">
            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">What</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Where</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">How long</th>
                </tr>
              </thead>
              <tbody>
                {dataRows.map((row, idx) => (
                  <tr key={row.what} className={`border-b border-obsidian-700 ${idx % 2 === 1 ? 'bg-obsidian-800/50' : ''}`}>
                    <td className="p-4 font-sans text-oatmeal-200 font-medium">{row.what}</td>
                    <td className="p-4 font-sans text-oatmeal-300">{row.where}</td>
                    <td className="p-4 font-sans text-oatmeal-300">{row.howLong}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <p className="mt-6 font-sans text-sm text-oatmeal-400">{RETENTION_STATEMENT}</p>
        </div>
      </motion.section>

      {/* 5. What We Store vs What We Don&apos;t Keep */}
      <motion.section
        className="relative pb-20 px-6"
        variants={stagger}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-80px' }}
      >
        <div className="max-w-4xl mx-auto">
          <motion.h2
            variants={marketingFadeUp}
            transition={{ duration: 0.5, ease: 'easeOut' as const }}
            className="font-serif text-3xl md:text-4xl text-oatmeal-100 mb-10 text-center"
          >
            What We Store and What We Don&apos;t Keep
          </motion.h2>

          <div className="grid md:grid-cols-2 gap-6">
            {/* What We Store */}
            <motion.div
              variants={marketingFadeUp}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
              className="bg-obsidian-800 border-l-4 border-sage-500 border-t border-r border-b border-t-obsidian-600 border-r-obsidian-600 border-b-obsidian-600 rounded-r-lg p-6"
            >
              <h3 className="font-serif text-xl text-oatmeal-100 mb-4 flex items-center gap-3">
                <svg className="w-6 h-6 text-sage-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                What We Store
              </h3>
              <ul className="space-y-3">
                {weStore.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-sage-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="font-sans text-oatmeal-300">{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            {/* What We Don&apos;t Keep */}
            <motion.div
              variants={marketingFadeUp}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
              className="bg-obsidian-800 border-l-4 border-clay-500 border-t border-r border-b border-t-obsidian-600 border-r-obsidian-600 border-b-obsidian-600 rounded-r-lg p-6"
            >
              <h3 className="font-serif text-xl text-oatmeal-100 mb-4 flex items-center gap-3">
                <svg className="w-6 h-6 text-clay-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
                What We Don&apos;t Keep
              </h3>
              <ul className="space-y-3">
                {weDontKeep.map((item) => (
                  <li key={item} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-clay-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="font-sans text-oatmeal-300">{item}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>
        </div>
      </motion.section>

      {/* 6. Security Advantages */}
      <motion.section
        className="relative pb-20 px-6"
        variants={stagger}
        initial="hidden"
        whileInView="visible"
        viewport={{ once: true, margin: '-80px' }}
      >
        <div className="max-w-4xl mx-auto">
          <motion.h2
            variants={marketingFadeUp}
            transition={{ duration: 0.5, ease: 'easeOut' as const }}
            className="font-serif text-3xl md:text-4xl text-oatmeal-100 mb-10 text-center"
          >
            What This Means if We Were Breached
          </motion.h2>

          <div className="grid md:grid-cols-2 gap-4">
            {securityAdvantages.map((advantage) => (
              <motion.div
                key={advantage}
                variants={marketingFadeUp}
                transition={{ duration: 0.5, ease: 'easeOut' as const }}
                className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-5 flex items-start gap-4 hover:border-sage-500/30 transition-colors"
              >
                <div className="flex-shrink-0 w-10 h-10 rounded-full bg-sage-500/20 flex items-center justify-center">
                  <svg className="w-5 h-5 text-sage-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                </div>
                <p className="font-sans text-oatmeal-300 leading-relaxed">{advantage}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* 7. Trade-Offs — Honest Disclosure */}
      <motion.section
        className="relative pb-20 px-6"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-4xl mx-auto">
          <div className="bg-obsidian-800 border border-oatmeal-500/20 rounded-lg p-8">
            <div className="flex items-start gap-4 mb-6">
              <div className="flex-shrink-0 w-10 h-10 rounded-full bg-clay-500/20 flex items-center justify-center">
                <svg className="w-5 h-5 text-clay-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
                </svg>
              </div>
              <div>
                <h2 className="font-serif text-2xl text-oatmeal-100 mb-2">
                  Trade-Offs
                </h2>
                <p className="font-sans text-oatmeal-400 leading-relaxed">
                  We believe in transparency. Not keeping your uploads has real trade-offs:
                </p>
              </div>
            </div>

            <ul className="space-y-4 ml-14">
              {tradeOffs.map((tradeOff) => (
                <li key={tradeOff} className="flex items-start gap-3">
                  <span className="w-1.5 h-1.5 rounded-full bg-oatmeal-500 flex-shrink-0 mt-2.5" />
                  <p className="font-sans text-oatmeal-300 leading-relaxed">{tradeOff}</p>
                </li>
              ))}
            </ul>

            <p className="font-sans text-sm text-oatmeal-500 mt-6 ml-14">
              We made this choice deliberately.
            </p>
          </div>
        </div>
      </motion.section>

      {/* 8. Further Reading */}
      <motion.section
        className="relative pb-24 px-6"
        initial={{ opacity: 0, y: 24 }}
        whileInView={{ opacity: 1, y: 0 }}
        viewport={{ once: true, margin: '-80px' }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-4xl mx-auto">
          <h2 className="font-serif text-3xl text-oatmeal-100 mb-8 text-center">
            Further Reading
          </h2>

          <div className="grid md:grid-cols-3 gap-4">
            <Link
              href="/privacy"
              className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 hover:border-sage-500/40 transition-colors group"
            >
              <div className="flex items-center gap-3 mb-2">
                <svg className="w-5 h-5 text-oatmeal-400 group-hover:text-sage-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                <h3 className="font-serif text-lg text-oatmeal-100 group-hover:text-sage-300 transition-colors">
                  Privacy Policy
                </h3>
              </div>
              <p className="font-sans text-sm text-oatmeal-500">
                Full details on data collection, usage, and your rights.
              </p>
            </Link>

            <Link
              href="/trust"
              className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 hover:border-sage-500/40 transition-colors group"
            >
              <div className="flex items-center gap-3 mb-2">
                <svg className="w-5 h-5 text-oatmeal-400 group-hover:text-sage-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <h3 className="font-serif text-lg text-oatmeal-100 group-hover:text-sage-300 transition-colors">
                  Trust &amp; Security
                </h3>
              </div>
              <p className="font-sans text-sm text-oatmeal-500">
                Security controls, what we keep, and what we do not claim.
              </p>
            </Link>

            <Link
              href="/terms"
              className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 hover:border-sage-500/40 transition-colors group"
            >
              <div className="flex items-center gap-3 mb-2">
                <svg className="w-5 h-5 text-oatmeal-400 group-hover:text-sage-400 transition-colors" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                </svg>
                <h3 className="font-serif text-lg text-oatmeal-100 group-hover:text-sage-300 transition-colors">
                  Terms of Service
                </h3>
              </div>
              <p className="font-sans text-sm text-oatmeal-500">
                Platform usage terms, limitations, and professional disclaimers.
              </p>
            </Link>
          </div>
        </div>
      </motion.section>

    </main>
  )
}
