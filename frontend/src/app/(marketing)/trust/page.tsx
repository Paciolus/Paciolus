'use client'

import { useRef, useState, useEffect } from 'react'
import { motion, useInView } from 'framer-motion'
import Link from 'next/link'
import { BrandIcon, type BrandIconName } from '@/components/shared'

/* ─── Data ─────────────────────────────────────────────────── */

type AccentColor = 'sage' | 'oatmeal' | 'clay'

interface ArchitectureStage {
  number: string
  title: string
  subtitle: string
  icon: BrandIconName
  accent: AccentColor
  controls: { label: string; detail: string }[]
}

const architectureStages: ArchitectureStage[] = [
  {
    number: '01',
    title: 'Ingest',
    subtitle: 'Secure data entry',
    icon: 'cloud-upload',
    accent: 'oatmeal',
    controls: [
      { label: 'TLS 1.3 Encryption', detail: 'All data in transit is encrypted with TLS 1.3 end-to-end.' },
      { label: 'Rate Limiting', detail: 'Brute-force protection on all authentication and upload endpoints.' },
    ],
  },
  {
    number: '02',
    title: 'Authenticate',
    subtitle: 'Identity verification',
    icon: 'padlock',
    accent: 'sage',
    controls: [
      { label: 'bcrypt Password Hashing', detail: 'Passwords salted and hashed with 12 rounds of bcrypt.' },
      { label: 'CSRF Protection', detail: 'Cross-site request forgery tokens on all state-changing operations.' },
    ],
  },
  {
    number: '03',
    title: 'Analyze',
    subtitle: 'Ephemeral processing',
    icon: 'shield-check',
    accent: 'sage',
    controls: [
      { label: 'JWT Authentication', detail: 'Stateless, short-lived token-based session management.' },
      { label: 'Multi-Tenant Isolation', detail: 'User data segregated at the database level with row-level security.' },
    ],
  },
  {
    number: '04',
    title: 'Purge',
    subtitle: 'Zero-Storage guarantee',
    icon: 'archive',
    accent: 'oatmeal',
    controls: [
      { label: 'Zero-Storage Architecture', detail: 'No raw files or line-level financial rows are persisted. Only aggregate metadata is stored.' },
    ],
  },
]

type ComplianceStatus = 'Compliant' | 'In Progress' | 'Available'

interface ComplianceNode {
  label: string
  status: ComplianceStatus
  detail: string
  dotClass: string
  badgeClass: string
}

const complianceNodes: ComplianceNode[] = [
  {
    label: 'GDPR',
    status: 'Compliant',
    detail: 'EU General Data Protection Regulation',
    dotClass: 'bg-sage-400',
    badgeClass: 'bg-sage-500/15 text-sage-400 border-sage-500/30',
  },
  {
    label: 'CCPA',
    status: 'Compliant',
    detail: 'California Consumer Privacy Act',
    dotClass: 'bg-sage-400',
    badgeClass: 'bg-sage-500/15 text-sage-400 border-sage-500/30',
  },
  {
    label: 'DPA',
    status: 'Available',
    detail: 'Enterprise tier',
    dotClass: 'bg-oatmeal-300',
    badgeClass: 'bg-oatmeal-300/10 text-oatmeal-300 border-oatmeal-300/30',
  },
  {
    label: 'SOC 2 Type II',
    status: 'In Progress',
    detail: 'Expected Q3 2026',
    dotClass: 'bg-oatmeal-400 animate-sage-pulse',
    badgeClass: 'bg-oatmeal-400/10 text-oatmeal-400 border-oatmeal-400/30',
  },
]

const weStore = [
  'User account information (name, email)',
  'Client metadata (names, industries, fiscal year-ends)',
  'Aggregate diagnostic metadata (category totals, ratios, row counts)',
  'Engagement records (narratives only, no line-level financial data)',
  'Anonymized usage statistics',
]

const weNeverStore = [
  'Raw uploaded CSV/Excel files',
  'Line-level trial balance rows or individual account balances',
  'Individual journal entries, invoices, or payment records',
  'Anomaly details tied to specific accounts or amounts',
]

interface TransparencyLink {
  label: string
  href: string
  icon: BrandIconName
}

const transparencyLinks: TransparencyLink[] = [
  { label: 'Privacy Policy', href: '/privacy', icon: 'document' },
  { label: 'Terms of Service', href: '/terms', icon: 'clipboard-check' },
  { label: 'Zero-Storage Architecture', href: '/approach', icon: 'shield-check' },
]

/* ─── Accent Classes ──────────────────────────────────────── */

function getAccentClasses(accent: AccentColor) {
  const classes = {
    sage: {
      bg: 'bg-sage-500/20',
      border: 'border-sage-500/40',
      text: 'text-sage-400',
      glow: 'shadow-sage-500/30',
    },
    oatmeal: {
      bg: 'bg-oatmeal-500/15',
      border: 'border-oatmeal-400/40',
      text: 'text-oatmeal-300',
      glow: 'shadow-oatmeal-400/25',
    },
    clay: {
      bg: 'bg-clay-500/20',
      border: 'border-clay-500/40',
      text: 'text-clay-400',
      glow: 'shadow-clay-500/30',
    },
  }
  return classes[accent]
}

/* ─── Animation Variants ──────────────────────────────────── */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: {
      staggerChildren: 0.1,
      delayChildren: 0.2,
    },
  },
}

const stageVariants = {
  hidden: { opacity: 0, y: 32, scale: 0.93 },
  visible: {
    opacity: 1,
    y: 0,
    scale: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 260,
      damping: 22,
    },
  },
}

const lineVariants1 = {
  hidden: { scaleX: 0, originX: 0 },
  visible: {
    scaleX: 1,
    transition: { duration: 0.8, ease: 'easeOut' as const, delay: 0.5 },
  },
}

const lineVariants2 = {
  hidden: { scaleX: 0, originX: 0 },
  visible: {
    scaleX: 1,
    transition: { duration: 0.8, ease: 'easeOut' as const, delay: 0.75 },
  },
}

const lineVariants3 = {
  hidden: { scaleX: 0, originX: 0 },
  visible: {
    scaleX: 1,
    transition: { duration: 0.8, ease: 'easeOut' as const, delay: 1.0 },
  },
}

const verticalLineVariants = {
  hidden: { scaleY: 0, originY: 0 },
  visible: {
    scaleY: 1,
    transition: { duration: 1.2, ease: 'easeOut' as const, delay: 0.4 },
  },
}

const iconVariants = {
  hidden: { scale: 0.8, opacity: 0 },
  visible: {
    scale: 1,
    opacity: 1,
    transition: {
      type: 'spring' as const,
      stiffness: 400,
      damping: 15,
    },
  },
}

const fadeUp = {
  hidden: { opacity: 0, y: 20 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' as const },
  },
}

const listItemVariants = {
  hidden: { opacity: 0, x: -10 },
  visible: {
    opacity: 1,
    x: 0,
    transition: {
      type: 'spring' as const,
      stiffness: 200,
      damping: 20,
    },
  },
}

/* ─── Local Components ────────────────────────────────────── */

function CountUp({ target, suffix = '' }: { target: number; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const isVisible = useInView(ref, { once: true })
  const [count, setCount] = useState(0)

  useEffect(() => {
    if (!isVisible) return

    let frame = 0
    const totalFrames = 40
    const interval = setInterval(() => {
      frame++
      setCount(Math.round((frame / totalFrames) * target))
      if (frame >= totalFrames) {
        clearInterval(interval)
        setCount(target)
      }
    }, 30)

    return () => clearInterval(interval)
  }, [isVisible, target])

  return <span ref={ref}>{count}{suffix}</span>
}

/* ─── Page ────────────────────────────────────────────────── */

export default function TrustAndSecurity() {
  const archRef = useRef<HTMLDivElement>(null)
  const archInView = useInView(archRef, { once: true, margin: '-100px' })
  const complianceRef = useRef<HTMLDivElement>(null)
  const complianceInView = useInView(complianceRef, { once: true, margin: '-100px' })

  const archLineVariants = [lineVariants1, lineVariants2, lineVariants3]

  return (
    <div className="min-h-screen bg-gradient-obsidian">
      {/* ── 1. Hero + Trust Metrics Bar ───────────────────── */}
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
          <p className="font-sans text-lg md:text-xl text-oatmeal-400 max-w-2xl mx-auto leading-relaxed mb-10">
            How we protect your data — and why we built it this way.
          </p>

          {/* Trust Metrics Bar */}
          <div className="inline-flex items-center gap-6 sm:gap-8 px-6 py-3 rounded-full bg-obsidian-800/60 border border-obsidian-600">
            <div className="text-center">
              <span className="font-mono text-2xl font-bold text-oatmeal-100">
                <CountUp target={6} />
              </span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Security Layers</p>
            </div>
            <div className="w-px h-8 bg-obsidian-600" />
            <div className="text-center">
              <span className="font-mono text-2xl font-bold text-oatmeal-100">
                <CountUp target={3} />
              </span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Compliance Standards</p>
            </div>
            <div className="w-px h-8 bg-obsidian-600" />
            <div className="text-center">
              <span className="font-mono text-2xl font-bold text-sage-400">Zero</span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Raw Data Stored</p>
            </div>
          </div>
        </div>
      </motion.section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── 2. Security Architecture Diagram ──────────────── */}
      <section className="lobby-surface-accent lobby-glow-sage overflow-hidden py-24 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Header */}
          <div className="max-w-3xl mx-auto text-center mb-16">
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4 }}
              className="inline-block font-sans text-xs font-medium text-sage-400 tracking-widest uppercase mb-3"
            >
              Security Architecture
            </motion.span>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="font-serif text-3xl sm:text-4xl text-oatmeal-100 mb-4"
            >
              How We Protect Your Data
            </motion.h2>
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="font-sans text-oatmeal-400"
            >
              Four stages. Every control documented. Zero raw data persisted.
            </motion.p>
          </div>

          {/* Desktop Architecture */}
          <motion.div
            ref={archRef}
            variants={containerVariants}
            initial="hidden"
            animate={archInView ? 'visible' : 'hidden'}
            className="hidden md:block relative"
          >
            {/* Connecting Lines */}
            <div className="absolute top-[4.5rem] left-0 right-0 flex justify-center pointer-events-none">
              <div className="w-full max-w-5xl flex">
                {archLineVariants.map((variant, i) => (
                  <div key={i} className="flex-1 flex justify-center px-8">
                    <motion.div
                      variants={variant}
                      className="w-full h-0.5 bg-gradient-to-r from-oatmeal-400/40 via-sage-500/30 to-sage-500/20"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Stages Grid */}
            <div className="grid grid-cols-4 gap-6">
              {architectureStages.map((stage) => {
                const accent = getAccentClasses(stage.accent)
                return (
                  <motion.div
                    key={stage.number}
                    variants={stageVariants}
                    className="relative flex flex-col items-center text-center"
                  >
                    {/* Number Badge */}
                    <span
                      className={`absolute -top-3 left-1/2 -translate-x-1/2 z-10 inline-flex items-center justify-center w-7 h-7 rounded-full ${accent.bg} border ${accent.border} font-mono text-xs font-bold ${accent.text}`}
                    >
                      {stage.number}
                    </span>

                    {/* Icon Container */}
                    <motion.div
                      variants={iconVariants}
                      className={`relative w-20 h-20 rounded-2xl ${accent.bg} border ${accent.border} flex items-center justify-center mb-5 ${accent.text} shadow-lg ${accent.glow}`}
                    >
                      <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
                      <BrandIcon name={stage.icon} className="w-8 h-8" />
                    </motion.div>

                    {/* Title + Subtitle */}
                    <h3 className="font-serif text-lg text-oatmeal-100 mb-1">{stage.title}</h3>
                    <p className={`font-sans text-xs ${accent.text} mb-4`}>{stage.subtitle}</p>

                    {/* Control Pills */}
                    <div className="space-y-2 w-full">
                      {stage.controls.map((ctrl) => (
                        <div
                          key={ctrl.label}
                          className="bg-obsidian-800/60 border border-obsidian-600 rounded-lg px-3 py-2 text-left"
                        >
                          <p className="font-sans text-xs font-medium text-oatmeal-200">{ctrl.label}</p>
                          <p className="font-sans text-[11px] text-oatmeal-500 leading-relaxed mt-0.5">
                            {ctrl.detail}
                          </p>
                        </div>
                      ))}
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>

          {/* Mobile Architecture — Vertical Timeline */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate={archInView ? 'visible' : 'hidden'}
            className="md:hidden relative"
          >
            {/* Vertical Connecting Line */}
            <motion.div
              variants={verticalLineVariants}
              className="absolute left-[2.25rem] top-12 bottom-12 w-0.5 bg-gradient-to-b from-oatmeal-400/50 via-sage-500/40 to-sage-500/20"
            />

            <div className="space-y-10">
              {architectureStages.map((stage) => {
                const accent = getAccentClasses(stage.accent)
                return (
                  <motion.div
                    key={stage.number}
                    variants={stageVariants}
                    className="relative flex items-start gap-5"
                  >
                    {/* Icon Box */}
                    <motion.div
                      variants={iconVariants}
                      className={`relative flex-shrink-0 w-[4.5rem] h-[4.5rem] rounded-xl ${accent.bg} border ${accent.border} flex items-center justify-center ${accent.text} shadow-lg ${accent.glow}`}
                    >
                      <span
                        className={`absolute -top-2 -right-2 z-10 inline-flex items-center justify-center w-6 h-6 rounded-full bg-obsidian-800 border ${accent.border} font-mono text-[10px] font-bold ${accent.text}`}
                      >
                        {stage.number}
                      </span>
                      <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
                      <BrandIcon name={stage.icon} className="w-7 h-7" />
                    </motion.div>

                    {/* Content */}
                    <div className="flex-1 pt-1">
                      <h3 className="font-serif text-lg text-oatmeal-100 mb-1">{stage.title}</h3>
                      <p className={`font-sans text-xs ${accent.text} mb-3`}>{stage.subtitle}</p>
                      <div className="space-y-2">
                        {stage.controls.map((ctrl) => (
                          <div
                            key={ctrl.label}
                            className="bg-obsidian-800/60 border border-obsidian-600 rounded-lg px-3 py-2"
                          >
                            <p className="font-sans text-xs font-medium text-oatmeal-200">{ctrl.label}</p>
                            <p className="font-sans text-[11px] text-oatmeal-500 leading-relaxed mt-0.5">
                              {ctrl.detail}
                            </p>
                          </div>
                        ))}
                      </div>
                    </div>
                  </motion.div>
                )
              })}
            </div>
          </motion.div>

          {/* Zero-Storage Summary Pill */}
          <motion.div
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5, delay: 0.6 }}
            className="max-w-lg mx-auto text-center mt-14"
          >
            <Link
              href="/approach"
              className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-obsidian-800/70 border border-obsidian-500/40 hover:border-sage-500/30 transition-colors group"
            >
              <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" />
              <span className="font-sans text-sm text-oatmeal-400">
                Zero-Storage: all raw data purged after analysis
              </span>
              <BrandIcon name="chevron-right" className="w-3.5 h-3.5 text-sage-400 group-hover:translate-x-0.5 transition-transform" />
            </Link>
          </motion.div>
        </div>
      </section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── 3. Compliance Timeline ────────────────────────── */}
      <section className="lobby-surface-recessed py-20 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-14">
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4 }}
              className="inline-block font-sans text-xs font-medium text-sage-400 tracking-widest uppercase mb-3"
            >
              Compliance
            </motion.span>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="font-serif text-3xl sm:text-4xl text-oatmeal-100"
            >
              Standards &amp; Certifications
            </motion.h2>
          </div>

          {/* Desktop Timeline */}
          <motion.div
            ref={complianceRef}
            variants={containerVariants}
            initial="hidden"
            animate={complianceInView ? 'visible' : 'hidden'}
            className="hidden md:block relative"
          >
            {/* Connecting Lines between dots */}
            <div className="absolute top-[0.5rem] left-0 right-0 flex justify-center pointer-events-none">
              <div className="w-full max-w-4xl flex">
                {archLineVariants.map((variant, i) => (
                  <div key={i} className="flex-1 flex justify-center px-10">
                    <motion.div
                      variants={variant}
                      className="w-full h-0.5 bg-gradient-to-r from-oatmeal-400/30 to-sage-500/20"
                    />
                  </div>
                ))}
              </div>
            </div>

            {/* Nodes Grid */}
            <div className="grid grid-cols-4 gap-6">
              {complianceNodes.map((node) => (
                <motion.div
                  key={node.label}
                  variants={stageVariants}
                  className="flex flex-col items-center"
                >
                  {/* Status Dot */}
                  <div className={`w-4 h-4 rounded-full ${node.dotClass} mb-6 ring-4 ring-obsidian-900/80`} />

                  {/* Card */}
                  <div className="bg-obsidian-800/60 border border-obsidian-600 rounded-xl p-5 w-full text-center">
                    <h3 className="font-serif text-lg text-oatmeal-100 mb-2">{node.label}</h3>
                    <span
                      className={`inline-block font-sans text-xs font-medium px-2.5 py-1 rounded-full border ${node.badgeClass}`}
                    >
                      {node.status}
                    </span>
                    <p className="font-sans text-xs text-oatmeal-500 mt-3">{node.detail}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>

          {/* Mobile Timeline — Vertical */}
          <motion.div
            variants={containerVariants}
            initial="hidden"
            animate={complianceInView ? 'visible' : 'hidden'}
            className="md:hidden relative"
          >
            {/* Vertical Line */}
            <motion.div
              variants={verticalLineVariants}
              className="absolute left-[0.45rem] top-2 bottom-2 w-0.5 bg-gradient-to-b from-sage-400/40 to-oatmeal-400/20"
            />

            <div className="space-y-8">
              {complianceNodes.map((node) => (
                <motion.div
                  key={node.label}
                  variants={stageVariants}
                  className="relative flex items-start gap-5 pl-1"
                >
                  {/* Dot */}
                  <div className={`flex-shrink-0 w-3.5 h-3.5 rounded-full ${node.dotClass} mt-1.5 ring-4 ring-obsidian-900/80`} />

                  {/* Card */}
                  <div className="flex-1 bg-obsidian-800/60 border border-obsidian-600 rounded-xl p-4">
                    <div className="flex items-center justify-between mb-1">
                      <h3 className="font-serif text-base text-oatmeal-100">{node.label}</h3>
                      <span
                        className={`font-sans text-[11px] font-medium px-2 py-0.5 rounded-full border ${node.badgeClass}`}
                      >
                        {node.status}
                      </span>
                    </div>
                    <p className="font-sans text-xs text-oatmeal-500">{node.detail}</p>
                  </div>
                </motion.div>
              ))}
            </div>
          </motion.div>
        </div>
      </section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── 4. Data Transparency ──────────────────────────── */}
      <section className="relative py-20 px-6">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-10">
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.4 }}
              className="inline-block font-sans text-xs font-medium text-sage-400 tracking-widest uppercase mb-3"
            >
              Data Handling
            </motion.span>
            <motion.h2
              initial={{ opacity: 0, y: 20 }}
              whileInView={{ opacity: 1, y: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="font-serif text-3xl sm:text-4xl text-oatmeal-100"
            >
              Data Transparency
            </motion.h2>
          </div>

          {/* Data Boundary Divider */}
          <motion.div
            initial={{ opacity: 0 }}
            whileInView={{ opacity: 1 }}
            viewport={{ once: true }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative flex items-center gap-4 mb-12"
          >
            <div className="flex-1 flex items-center">
              <div className="w-2 h-2 rounded-full bg-sage-400/60" />
              <div className="flex-1 h-px bg-gradient-to-r from-sage-400/30 to-transparent" />
            </div>
            <span className="font-sans text-xs font-medium text-oatmeal-400 tracking-wide uppercase px-3 py-1.5 rounded-full bg-obsidian-800/60 border border-obsidian-600 whitespace-nowrap">
              Your Data Boundary
            </span>
            <div className="flex-1 flex items-center">
              <div className="flex-1 h-px bg-gradient-to-l from-clay-400/30 to-transparent" />
              <div className="w-2 h-2 rounded-full bg-clay-400/60" />
            </div>
          </motion.div>

          {/* Two-Column Store/Never Store */}
          <div className="grid md:grid-cols-2 gap-6">
            {/* What We Store */}
            <motion.div
              className="bg-obsidian-800 border-l-4 border-sage-500 rounded-r-xl p-6 md:p-8"
              initial={{ opacity: 0, x: -20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-sage-500/15 flex items-center justify-center text-sage-400">
                  <BrandIcon name="circle-check" className="w-4.5 h-4.5" />
                </div>
                <h3 className="font-serif text-xl text-oatmeal-100">What We Store</h3>
              </div>
              <motion.ul
                className="space-y-3.5"
                variants={containerVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
              >
                {weStore.map((item) => (
                  <motion.li key={item} variants={listItemVariants} className="flex items-start gap-3">
                    <svg className="w-4 h-4 text-sage-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    <span className="font-sans text-sm text-oatmeal-300 leading-relaxed">{item}</span>
                  </motion.li>
                ))}
              </motion.ul>
            </motion.div>

            {/* What We NEVER Store */}
            <motion.div
              className="bg-obsidian-800 border-l-4 border-clay-500 rounded-r-xl p-6 md:p-8"
              initial={{ opacity: 0, x: 20 }}
              whileInView={{ opacity: 1, x: 0 }}
              viewport={{ once: true }}
              transition={{ duration: 0.5, ease: 'easeOut' as const }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-clay-500/15 flex items-center justify-center text-clay-400">
                  <BrandIcon name="shield-check" className="w-4.5 h-4.5" />
                </div>
                <h3 className="font-serif text-xl text-oatmeal-100">What We NEVER Store</h3>
              </div>
              <motion.ul
                className="space-y-3.5"
                variants={containerVariants}
                initial="hidden"
                whileInView="visible"
                viewport={{ once: true }}
              >
                {weNeverStore.map((item) => (
                  <motion.li key={item} variants={listItemVariants} className="flex items-start gap-3">
                    <svg className="w-4 h-4 text-clay-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span className="font-sans text-sm text-oatmeal-300 leading-relaxed">{item}</span>
                  </motion.li>
                ))}
              </motion.ul>
            </motion.div>
          </div>
        </div>
      </section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── 5. Transparency Links — Icon Cards ────────────── */}
      <section className="lobby-surface-raised py-16 px-6">
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, y: 15 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
            transition={{ duration: 0.5 }}
          >
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-2">Transparency</h2>
            <p className="font-sans text-oatmeal-400 text-sm">
              We believe in transparency. Review our policies:
            </p>
          </motion.div>

          <motion.div
            className="grid sm:grid-cols-3 gap-4"
            variants={containerVariants}
            initial="hidden"
            whileInView="visible"
            viewport={{ once: true }}
          >
            {transparencyLinks.map((link) => (
              <motion.div key={link.href} variants={fadeUp}>
                <Link
                  href={link.href}
                  className="flex items-center gap-4 bg-obsidian-800/60 border border-obsidian-600 rounded-xl px-5 py-4 hover:border-sage-500/30 transition-colors group"
                >
                  <div className="w-9 h-9 rounded-lg bg-sage-500/15 flex items-center justify-center text-sage-400 flex-shrink-0">
                    <BrandIcon name={link.icon} className="w-4.5 h-4.5" />
                  </div>
                  <span className="font-sans text-sm text-oatmeal-200 flex-1">{link.label}</span>
                  <BrandIcon name="chevron-right" className="w-4 h-4 text-oatmeal-500 group-hover:text-sage-400 group-hover:translate-x-0.5 transition-all" />
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>
    </div>
  )
}
