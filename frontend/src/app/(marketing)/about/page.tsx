import Link from 'next/link'
import { Blockquote } from '@/components/marketing/Blockquote'
import * as motion from '@/components/ui/motionClient'
import { DOCUMENTATION_STATEMENT, RESPONSIBILITY_STATEMENT, SHARE_RETENTION, STORAGE_DETAIL_HREF, STORAGE_DETAIL_LABEL, STORAGE_STATEMENT } from '@/content/storage-statement'

/* ---------- Animation helpers ---------- */
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
    transition: { duration: 0.2, ease: 'easeOut' as const },
  },
}

/* ---------- Data ---------- */
const whatItIs = [
  'An analytical tool designed to support auditors’ analytical work',
  'A tool that surfaces analytical exceptions requiring professional evaluation',
  'PDF memos and Excel/CSV workpapers, for your review',
  'Built so uploaded files are processed in memory and not kept after analysis',
]

const whatItIsNot = [
  'Not an audit software that replaces professional judgment',
  'Not a system that provides assurance opinions',
  'Not a tool that generates audit evidence',
  'Not a workpaper archive — your firm keeps its own documentation',
]

const professionalsCards = [
  {
    title: 'Designed Around How Auditors Work',
    description: 'Designed to support auditors’ analytical work, with references to the standards each test draws on.',
  },
  {
    title: 'Cited Rules',
    description: 'Every test names the rule it applies, or says when a threshold is our own convention. Sources & Methodology lists each one.',
  },
  {
    title: 'Memos and Workpapers',
    description: 'PDF memos (sign-off lines are optional, completed by the firm), Excel and CSV exports, for your review.',
  },
]

/* ---------- Page Component ---------- */
export default function AboutPage() {
  return (
    <main id="main-content" className="relative z-10 min-h-screen bg-gradient-obsidian">
      {/* ===== Pacioli Connection ===== */}
      <motion.section
        className="relative pt-32 pb-10 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' as const }}
      >
        <div className="max-w-3xl mx-auto text-center">
          <p className="type-body-lg text-oatmeal-300 leading-relaxed">
            In 1494, Luca Pacioli published <span className="italic">Summa de arithmetica</span>, the first printed
            description of double-entry bookkeeping.
            Paciolus is built on the same foundation Pacioli laid &mdash; rigor, precision, and
            respect for professional judgment.
          </p>
        </div>
      </motion.section>

      {/* ===== Why We Built Paciolus ===== */}
      <motion.section
        className="relative pb-16 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' as const }}
      >
        <div className="max-w-4xl mx-auto text-center">
          <h1 className="type-display text-oatmeal-100 mb-6">
            Why We Built Paciolus
          </h1>
          <p className="type-body-lg text-oatmeal-400 max-w-2xl mx-auto">
            Audit work demands precision, professional skepticism, and thorough documentation.
            The tools that support this work should reflect the same rigor. Paciolus was designed
            to meet that standard &mdash; built for the analytical work in an audit, not adapted from
            general-purpose analytics tools.
          </p>
        </div>
      </motion.section>

      {/* ===== Founding Motivation Blockquote — Sprint 703 editorial treatment ===== */}
      <motion.section
        className="px-6 pb-16"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' as const }}
      >
        <Blockquote attribution="Paciolus — founding motivation">
          &ldquo;The moment when you need a well-documented answer shouldn&rsquo;t depend on the size of your firm. We built Paciolus so it doesn&rsquo;t.&rdquo;
        </Blockquote>
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
              className="bg-obsidian-700/60 border border-sage-500/30 rounded-lg p-8"
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
              className="bg-obsidian-700/60 border border-clay-500/30 rounded-lg p-8"
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

      {/* ===== What we keep (Sprint 861) ===== */}
      <motion.section
        className="px-6 pb-20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' as const }}
      >
        <div className="max-w-3xl mx-auto">
          <h2 className="type-headline text-oatmeal-100 text-center mb-8">
            What We Keep, and What We Don&apos;t
          </h2>
          <div className="bg-obsidian-700/60 border border-obsidian-500/30 rounded-lg p-8">
            <p className="type-body text-oatmeal-400 leading-relaxed">
              {STORAGE_STATEMENT} A summary of an analysis includes totals, ratios and the names of accounts a
              tool flagged. A report you share by link is stored with our storage provider for {SHARE_RETENTION}.{' '}
              <Link href={STORAGE_DETAIL_HREF} className="text-sage-400 hover:text-sage-300 underline transition-colors">
                {STORAGE_DETAIL_LABEL}
              </Link>.
            </p>
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

          <ol className="border-t border-obsidian-500/60">
            {professionalsCards.map((card, i) => (
              <li
                key={card.title}
                className="grid grid-cols-[2.5rem_minmax(0,1fr)] md:grid-cols-[2.5rem_minmax(0,16rem)_minmax(0,1fr)] gap-x-6 gap-y-2 py-5 border-b border-obsidian-500/60"
              >
                <span className="font-mono text-sm text-sage-400 tabular-nums">{i + 1}.</span>
                <h3 className="font-serif text-lg text-oatmeal-100">{card.title}</h3>
                <p className="col-start-2 md:col-start-3 type-body-sm text-oatmeal-400">{card.description}</p>
              </li>
            ))}
          </ol>
        </div>
      </motion.section>

      {/* ===== How We're Different ===== */}
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
            How Paciolus Is Different
          </motion.h2>

          <div className="grid md:grid-cols-2 gap-6">
            {[
              {
                title: 'No Installation Required',
                description: 'Access from any device without desktop software or plugins. Open a browser, upload a file, get documented results.',
              },
              {
                title: 'Uploads Processed in Memory',
                description: 'Uploaded files are parsed in memory and not kept after analysis. What we do save — summaries and your engagement entries — is listed on the Trust page.',
              },
              {
                title: 'Cited Memos',
                description: 'Every PDF memo cites the rule behind each test and marks thresholds that are Paciolus conventions. For your review.',
              },
            ].map((item) => (
              <motion.div
                key={item.title}
                className="bg-obsidian-700/60 border border-obsidian-500/30 rounded-lg p-6"
                variants={cardReveal}
              >
                <h3 className="font-serif text-lg text-sage-400 mb-3">{item.title}</h3>
                <p className="type-body-sm text-oatmeal-400">{item.description}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* ===== Workflow & Integrations ===== */}
      <motion.section
        className="px-6 pb-20"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' as const }}
      >
        <div className="max-w-3xl mx-auto">
          <h2 className="type-headline text-oatmeal-100 text-center mb-8">
            Where Paciolus Fits in Your Workflow
          </h2>
          <div className="bg-obsidian-700/60 border border-obsidian-500/30 rounded-lg p-8">
            <p className="type-body text-oatmeal-400 mb-6">
              Paciolus is a standalone analytics platform that complements your existing tools. It accepts 10 file formats: QuickBooks exports (QBO, IIF), bank feeds (OFX), Excel (.xlsx and .xls), CSV, TSV, TXT, PDF tables and Word (.docx) tables.
            </p>
            <p className="type-body text-oatmeal-400 mb-6">
              {RESPONSIBILITY_STATEMENT} Exports are standard PDF, XLSX and CSV files.
            </p>
            <p className="type-body text-oatmeal-400">
              Every tool run is logged in your activity history with a timestamp, visible in your workspace.
            </p>
            <p className="type-body text-oatmeal-400 mt-6">
              {DOCUMENTATION_STATEMENT}
            </p>
            <p className="type-body text-oatmeal-400 mt-6">
              Paciolus is developed and operated by Paciolus LLC, a US company.
            </p>
          </div>
        </div>
      </motion.section>

      {/* ===== CTA Section ===== */}
      <motion.section
        className="px-6 pb-24"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' as const }}
      >
        <div className="max-w-2xl mx-auto text-center">
          <h2 className="type-headline text-oatmeal-100 mb-4">
            Try the eighteen tools for seven days.
          </h2>
          <p className="type-body text-oatmeal-400 mb-8">
            Seven-day trial. All eighteen tools. Your uploaded files are not kept after analysis.
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

    </main>
  )
}
