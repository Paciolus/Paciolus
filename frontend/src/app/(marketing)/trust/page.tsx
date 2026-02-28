'use client'

import { useRef, useState, useEffect, useCallback } from 'react'
import Link from 'next/link'
import { motion, useInView, AnimatePresence } from 'framer-motion'
import { BrandIcon, type BrandIconName } from '@/components/shared'

/* ─── Types ──────────────────────────────────────────────── */

type AccentColor = 'sage' | 'oatmeal' | 'clay'

interface ArchitectureNode {
  id: string
  number: string
  title: string
  subtitle: string
  icon: BrandIconName
  accent: AccentColor
  boundary: 'ephemeral' | 'persistent'
}

type ControlCategory = 'authentication' | 'transport' | 'tenancy' | 'export' | 'data-handling'

interface SecurityControl {
  name: string
  description: string
  category: ControlCategory
  standard: string
  active: boolean
}

type ComplianceStatus = 'compliant' | 'in-progress' | 'planned'

interface ComplianceMilestone {
  label: string
  status: ComplianceStatus
  detail: string
  year: string
  artifact?: { label: string; href: string }
}

interface PlaybookPhase {
  title: string
  icon: BrandIconName
  accent: AccentColor
  description: string
  measures: string[]
}

interface DownloadableArtifact {
  label: string
  description: string
  href: string
  icon: BrandIconName
  type: string
}

/* ─── Data ───────────────────────────────────────────────── */

const architectureNodes: ArchitectureNode[] = [
  {
    id: 'ingest',
    number: '01',
    title: 'Ingest',
    subtitle: 'Secure data entry',
    icon: 'cloud-upload',
    accent: 'oatmeal',
    boundary: 'ephemeral',
  },
  {
    id: 'authenticate',
    number: '02',
    title: 'Authenticate',
    subtitle: 'Identity verification',
    icon: 'padlock',
    accent: 'sage',
    boundary: 'ephemeral',
  },
  {
    id: 'process',
    number: '03',
    title: 'Process',
    subtitle: 'Ephemeral analysis',
    icon: 'shield-check',
    accent: 'sage',
    boundary: 'ephemeral',
  },
  {
    id: 'purge',
    number: '04',
    title: 'Purge',
    subtitle: 'Zero-Storage guarantee',
    icon: 'archive',
    accent: 'oatmeal',
    boundary: 'persistent',
  },
]

const controlCategories: { key: ControlCategory; label: string; icon: BrandIconName }[] = [
  { key: 'authentication', label: 'Authentication', icon: 'padlock' },
  { key: 'transport', label: 'Transport', icon: 'cloud-upload' },
  { key: 'tenancy', label: 'Tenancy', icon: 'users' },
  { key: 'export', label: 'Export', icon: 'file-download' },
  { key: 'data-handling', label: 'Data Handling', icon: 'shield-check' },
]

const securityControls: SecurityControl[] = [
  { name: 'bcrypt Password Hashing', description: '12-round salted bcrypt hashing for all stored credentials.', category: 'authentication', standard: 'OWASP ASVS 2.4', active: true },
  { name: 'JWT Access Tokens', description: '30-minute stateless tokens with jti claim and refresh rotation.', category: 'authentication', standard: 'RFC 7519', active: true },
  { name: 'Refresh Token Rotation', description: '7-day refresh tokens with single-use enforcement and reuse detection.', category: 'authentication', standard: 'OAuth 2.0 BCP', active: true },
  { name: 'CSRF Protection', description: 'Stateless HMAC-based CSRF tokens on all state-changing endpoints.', category: 'authentication', standard: 'OWASP ASVS 4.2', active: true },
  { name: 'Account Lockout', description: 'Progressive lockout stored in database, surviving server restarts.', category: 'authentication', standard: 'NIST 800-63B', active: true },
  { name: 'Email Verification', description: 'Token-based email verification with disposable domain blocking.', category: 'authentication', standard: 'OWASP ASVS 2.1', active: true },
  { name: 'TLS 1.3 Transport', description: 'End-to-end TLS 1.3 encryption for all client-server communication.', category: 'transport', standard: 'RFC 8446', active: true },
  { name: 'Rate Limiting', description: 'Per-endpoint and global 60/min rate limits on all routes.', category: 'transport', standard: 'OWASP API4', active: true },
  { name: 'Body Size Middleware', description: 'Global request body size limits preventing oversized payload attacks.', category: 'transport', standard: 'OWASP API4', active: true },
  { name: 'CORS Hardening', description: 'Strict origin allowlist with credentialed request support.', category: 'transport', standard: 'OWASP ASVS 14.5', active: true },
  { name: 'Row-Level Isolation', description: 'Every database query scoped to authenticated user_id. No cross-tenant data leakage.', category: 'tenancy', standard: 'SOC 2 CC6.1', active: true },
  { name: 'Diagnostic Zone Protection', description: 'Tool pages require verified authentication before any data access.', category: 'tenancy', standard: 'OWASP ASVS 4.1', active: true },
  { name: 'Soft-Delete Immutability', description: 'Audit trail records use soft-delete with ORM-level deletion guards.', category: 'tenancy', standard: 'SOC 2 CC8.1', active: true },
  { name: 'Formula Injection Guard', description: 'All CSV/Excel exports sanitized against =, +, -, @ formula injection.', category: 'export', standard: 'CWE-1236', active: true },
  { name: 'Export Signing', description: 'Workpaper signoff metadata embedded in every PDF and Excel export.', category: 'export', standard: 'PCAOB AS 1215', active: true },
  { name: 'Column & Cell Limits', description: 'Upload validation enforces column count and cell count boundaries.', category: 'export', standard: 'OWASP Input Val.', active: true },
  { name: 'Zero-Storage Architecture', description: 'No raw uploaded files or line-level financial data persisted. Only aggregate metadata stored.', category: 'data-handling', standard: 'GDPR Art. 25', active: true },
  { name: 'Memory Cleanup', description: 'Context-managed memory purge after every analysis operation.', category: 'data-handling', standard: 'CWE-401', active: true },
  { name: 'Structured Logging', description: 'Request-ID correlated logs with sanitized error output. No PII in logs.', category: 'data-handling', standard: 'SOC 2 CC7.2', active: true },
]

const complianceMilestones: ComplianceMilestone[] = [
  {
    label: 'GDPR',
    status: 'compliant',
    detail: 'EU General Data Protection Regulation',
    year: '2024',
    artifact: { label: 'Privacy Policy', href: '/privacy' },
  },
  {
    label: 'CCPA',
    status: 'compliant',
    detail: 'California Consumer Privacy Act',
    year: '2024',
    artifact: { label: 'Privacy Policy', href: '/privacy' },
  },
  {
    label: 'DPA',
    status: 'planned',
    detail: 'Data Processing Agreement — Enterprise tier',
    year: '2025',
    artifact: { label: 'Request DPA', href: '/contact?inquiry_type=enterprise' },
  },
  {
    label: 'SOC 2 Type II',
    status: 'in-progress',
    detail: 'Service Organization Control — Expected Q3 2026',
    year: '2026',
  },
]

const playbookPhases: PlaybookPhase[] = [
  {
    title: 'Detection',
    icon: 'warning-triangle',
    accent: 'oatmeal',
    description: 'Automated monitoring and anomaly detection across infrastructure and application layers.',
    measures: [
      'Structured logging with request-ID correlation',
      'Sentry APM with Zero-Storage compliant error tracking',
      'Rate limit breach alerting',
    ],
  },
  {
    title: 'Containment',
    icon: 'shield-check',
    accent: 'sage',
    description: 'Immediate isolation of affected systems to prevent lateral movement.',
    measures: [
      'JWT token revocation on password change',
      'Account lockout on suspicious activity',
      'CSRF token rotation',
    ],
  },
  {
    title: 'Recovery',
    icon: 'archive',
    accent: 'sage',
    description: 'Zero-Storage architecture minimizes exposure — no raw financial data to exfiltrate.',
    measures: [
      'No raw files stored means no file-level breach surface',
      'Aggregate-only metadata limits data exposure scope',
      'Soft-delete audit trail preserves forensic record',
    ],
  },
  {
    title: 'Communication',
    icon: 'document',
    accent: 'oatmeal',
    description: 'Transparent disclosure protocol aligned with GDPR Article 33 notification requirements.',
    measures: [
      '72-hour regulatory notification commitment',
      'Affected user communication via verified email',
      'Post-incident report published to Trust page',
    ],
  },
]

const downloadableArtifacts: DownloadableArtifact[] = [
  { label: 'Privacy Policy', description: 'Full GDPR/CCPA-compliant privacy disclosure.', href: '/privacy', icon: 'document', type: 'Policy' },
  { label: 'Terms of Service', description: 'Platform usage terms and liability framework.', href: '/terms', icon: 'clipboard-check', type: 'Legal' },
  { label: 'Zero-Storage Architecture', description: 'Technical deep-dive into our ephemeral processing model.', href: '/approach', icon: 'shield-check', type: 'Technical' },
  { label: 'Request DPA', description: 'Data Processing Agreement available for Enterprise accounts.', href: '/contact?inquiry_type=enterprise', icon: 'file-download', type: 'Enterprise' },
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

/* ─── Accent Utilities ───────────────────────────────────── */

function accentClasses(accent: AccentColor) {
  const map = {
    sage: {
      bg: 'bg-sage-500/20',
      border: 'border-sage-500/40',
      text: 'text-sage-400',
      glow: 'shadow-sage-500/30',
      dot: 'bg-sage-400',
      badge: 'bg-sage-500/15 text-sage-400 border-sage-500/30',
      ring: 'ring-sage-500/20',
    },
    oatmeal: {
      bg: 'bg-oatmeal-500/15',
      border: 'border-oatmeal-400/40',
      text: 'text-oatmeal-300',
      glow: 'shadow-oatmeal-400/25',
      dot: 'bg-oatmeal-300',
      badge: 'bg-oatmeal-300/10 text-oatmeal-300 border-oatmeal-300/30',
      ring: 'ring-oatmeal-400/20',
    },
    clay: {
      bg: 'bg-clay-500/20',
      border: 'border-clay-500/40',
      text: 'text-clay-400',
      glow: 'shadow-clay-500/30',
      dot: 'bg-clay-400',
      badge: 'bg-clay-500/15 text-clay-400 border-clay-500/30',
      ring: 'ring-clay-500/20',
    },
  }
  return map[accent]
}

/* ─── Animation Variants ─────────────────────────────────── */

const containerVariants = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.08, delayChildren: 0.15 },
  },
}

const fadeUp = {
  hidden: { opacity: 0, y: 24 },
  visible: {
    opacity: 1,
    y: 0,
    transition: { duration: 0.5, ease: 'easeOut' as const },
  },
}

const fadeIn = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { duration: 0.4, ease: 'easeOut' as const },
  },
}

const scaleIn = {
  hidden: { opacity: 0, scale: 0.92 },
  visible: {
    opacity: 1,
    scale: 1,
    transition: { type: 'spring' as const, stiffness: 260, damping: 22 },
  },
}

const lineGrow = {
  hidden: { scaleX: 0, originX: 0 },
  visible: {
    scaleX: 1,
    transition: { duration: 1.0, ease: 'easeOut' as const, delay: 0.4 },
  },
}

const vertLineGrow = {
  hidden: { scaleY: 0, originY: 0 },
  visible: {
    scaleY: 1,
    transition: { duration: 1.2, ease: 'easeOut' as const, delay: 0.3 },
  },
}

const listItem = {
  hidden: { opacity: 0, x: -8 },
  visible: {
    opacity: 1,
    x: 0,
    transition: { type: 'spring' as const, stiffness: 200, damping: 20 },
  },
}

/* ─── Local Components ───────────────────────────────────── */

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

/** Section wrapper with consistent heading pattern */
function ModuleSection({
  id,
  meta,
  title,
  subtitle,
  surface = '',
  children,
}: {
  id: string
  meta: string
  title: string
  subtitle?: string
  surface?: string
  children: React.ReactNode
}) {
  return (
    <section id={id} className={`py-24 px-6 ${surface}`} aria-labelledby={`${id}-heading`}>
      <div className="max-w-6xl mx-auto">
        <div className="max-w-3xl mx-auto text-center mb-16">
          <motion.span
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4 }}
            className="inline-block type-meta text-sage-400 mb-3"
          >
            {meta}
          </motion.span>
          <motion.h2
            id={`${id}-heading`}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="type-headline text-oatmeal-100 mb-4"
          >
            {title}
          </motion.h2>
          {subtitle && (
            <motion.p
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.2 }}
              className="font-sans text-oatmeal-400"
            >
              {subtitle}
            </motion.p>
          )}
        </div>
        {children}
      </div>
    </section>
  )
}

/* ─── Simplified Architecture Diagram (no expandable controls) */

function ArchitectureDiagram() {
  return (
    <div>
      {/* Desktop Architecture */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="hidden md:block"
      >
        {/* Zero-Storage Boundary Indicator */}
        <div className="flex items-center gap-3 mb-8">
          <div className="flex items-center gap-2">
            <div className="w-2.5 h-2.5 rounded-full bg-sage-400/60" />
            <span className="font-sans text-xs text-oatmeal-500">Ephemeral Zone</span>
          </div>
          <div className="flex-1 h-px bg-gradient-to-r from-sage-500/20 via-oatmeal-300/10 to-clay-400/20" />
          <div className="flex items-center gap-2">
            <span className="font-sans text-xs text-oatmeal-500">Persistent Boundary</span>
            <div className="w-2.5 h-2.5 rounded-full bg-oatmeal-400/60" />
          </div>
        </div>

        {/* Main Architecture Grid */}
        <div className="relative">
          {/* Connecting Flow Lines */}
          <div className="absolute top-[4.5rem] left-0 right-0 flex justify-center pointer-events-none" aria-hidden="true">
            <div className="w-full max-w-5xl flex">
              {[0, 1, 2].map(i => (
                <div key={i} className="flex-1 flex justify-center px-8">
                  <motion.div
                    variants={lineGrow}
                    className="w-full h-0.5 bg-gradient-to-r from-oatmeal-400/40 via-sage-500/30 to-sage-500/20"
                  />
                </div>
              ))}
            </div>
          </div>

          {/* Zero-Storage Boundary Line — dashed vertical between node 3 and 4 */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 1.2, duration: 0.6 }}
            className="absolute top-0 bottom-0 pointer-events-none"
            style={{ left: 'calc(75% - 0.5px)' }}
            aria-hidden="true"
          >
            <div className="h-full border-l-2 border-dashed border-oatmeal-400/20" />
            <div className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 px-2 py-1 bg-obsidian-800 rounded-md">
              <span className="font-mono text-[10px] text-oatmeal-500 whitespace-nowrap tracking-wider uppercase">
                Zero-Storage Boundary
              </span>
            </div>
          </motion.div>

          {/* Stage Cards */}
          <div className="grid grid-cols-4 gap-6">
            {architectureNodes.map(node => {
              const a = accentClasses(node.accent)
              return (
                <motion.div key={node.id} variants={scaleIn} className="relative flex flex-col items-center text-center">
                  {/* Number Badge */}
                  <span
                    className={`absolute -top-3 left-1/2 -translate-x-1/2 z-10 inline-flex items-center justify-center w-7 h-7 rounded-full ${a.bg} border ${a.border} font-mono text-xs font-bold ${a.text}`}
                    aria-hidden="true"
                  >
                    {node.number}
                  </span>

                  {/* Icon */}
                  <div
                    className={`relative w-20 h-20 rounded-2xl ${a.bg} border ${a.border} flex items-center justify-center mb-5 ${a.text} shadow-lg ${a.glow}`}
                  >
                    <div className="absolute inset-0 rounded-2xl bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
                    <BrandIcon name={node.icon} className="w-8 h-8" />
                  </div>

                  <h3 className="font-serif text-lg text-oatmeal-100 mb-1">{node.title}</h3>
                  <p className={`font-sans text-xs ${a.text} mb-3`}>{node.subtitle}</p>

                  {/* Boundary Tag */}
                  <span className={`inline-flex items-center gap-1.5 font-mono text-[10px] tracking-wider uppercase px-2 py-0.5 rounded-full ${
                    node.boundary === 'ephemeral'
                      ? 'bg-sage-500/10 text-sage-400 border border-sage-500/20'
                      : 'bg-oatmeal-300/10 text-oatmeal-400 border border-oatmeal-300/20'
                  }`}>
                    <div className={`w-1.5 h-1.5 rounded-full ${
                      node.boundary === 'ephemeral' ? 'bg-sage-400' : 'bg-oatmeal-400'
                    }`} />
                    {node.boundary}
                  </span>
                </motion.div>
              )
            })}
          </div>
        </div>
      </motion.div>

      {/* Mobile Architecture — Vertical Timeline */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="md:hidden relative"
      >
        {/* Vertical Line */}
        <motion.div
          variants={vertLineGrow}
          className="absolute left-[2.25rem] top-12 bottom-12 w-0.5 bg-gradient-to-b from-oatmeal-400/50 via-sage-500/40 to-sage-500/20"
          aria-hidden="true"
        />

        {/* Zero-Storage Boundary (mobile) */}
        <div className="flex items-center gap-3 mb-8 ml-[4.5rem]">
          <div className="w-1.5 h-1.5 rounded-full bg-sage-400" />
          <span className="font-mono text-[10px] text-oatmeal-500 tracking-wider uppercase">Ephemeral Zone</span>
        </div>

        <div className="space-y-8">
          {architectureNodes.map((node, idx) => {
            const a = accentClasses(node.accent)
            const ephemeralCount = architectureNodes.filter(n => n.boundary === 'ephemeral').length
            const showBoundary = idx === ephemeralCount - 1

            return (
              <div key={node.id}>
                <motion.div variants={scaleIn} className="relative flex items-start gap-5">
                  <div
                    className={`relative flex-shrink-0 w-[4.5rem] h-[4.5rem] rounded-xl ${a.bg} border ${a.border} flex items-center justify-center ${a.text} shadow-lg ${a.glow}`}
                  >
                    <span
                      className={`absolute -top-2 -right-2 z-10 inline-flex items-center justify-center w-6 h-6 rounded-full bg-obsidian-800 border ${a.border} font-mono text-[10px] font-bold ${a.text}`}
                      aria-hidden="true"
                    >
                      {node.number}
                    </span>
                    <div className="absolute inset-0 rounded-xl bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
                    <BrandIcon name={node.icon} className="w-7 h-7" />
                  </div>

                  <div className="flex-1 pt-1">
                    <h3 className="font-serif text-lg text-oatmeal-100 mb-1">{node.title}</h3>
                    <p className={`font-sans text-xs ${a.text} mb-2`}>{node.subtitle}</p>

                    <span className={`inline-flex items-center gap-1.5 font-mono text-[10px] tracking-wider uppercase px-2 py-0.5 rounded-full ${
                      node.boundary === 'ephemeral'
                        ? 'bg-sage-500/10 text-sage-400 border border-sage-500/20'
                        : 'bg-oatmeal-300/10 text-oatmeal-400 border border-oatmeal-300/20'
                    }`}>
                      <div className={`w-1.5 h-1.5 rounded-full ${node.boundary === 'ephemeral' ? 'bg-sage-400' : 'bg-oatmeal-400'}`} />
                      {node.boundary}
                    </span>
                  </div>
                </motion.div>

                {/* Zero-Storage Boundary divider on mobile */}
                {showBoundary && (
                  <div className="flex items-center gap-3 my-6 ml-[4.5rem]">
                    <div className="flex-1 border-t border-dashed border-oatmeal-400/20" />
                    <span className="font-mono text-[10px] text-oatmeal-500 tracking-wider uppercase whitespace-nowrap px-2 py-1 bg-obsidian-800 rounded-md">
                      Zero-Storage Boundary
                    </span>
                    <div className="flex-1 border-t border-dashed border-oatmeal-400/20" />
                  </div>
                )}
              </div>
            )
          })}
        </div>
      </motion.div>

      {/* Zero-Storage Summary Pill */}
      <motion.div
        initial={{ opacity: 0, y: 15 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.6 }}
        className="max-w-lg mx-auto text-center mt-14"
      >
        <Link
          href="/approach"
          className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-obsidian-800/70 border border-obsidian-500/40 hover:border-sage-500/30 transition-colors group"
        >
          <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse" aria-hidden="true" />
          <span className="font-sans text-sm text-oatmeal-400">
            Zero-Storage: all raw data purged after analysis
          </span>
          <BrandIcon name="chevron-right" className="w-3.5 h-3.5 text-sage-400 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </motion.div>
    </div>
  )
}

/* ─── Module 2: Control Matrix ───────────────────────────── */

function ControlMatrix() {
  const [activeFilters, setActiveFilters] = useState<Set<ControlCategory>>(new Set())

  const toggleFilter = useCallback((cat: ControlCategory) => {
    setActiveFilters(prev => {
      const next = new Set(prev)
      if (next.has(cat)) {
        next.delete(cat)
      } else {
        next.add(cat)
      }
      return next
    })
  }, [])

  const filteredControls = activeFilters.size === 0
    ? securityControls
    : securityControls.filter(c => activeFilters.has(c.category))

  const getCategoryLabel = (cat: ControlCategory) =>
    controlCategories.find(c => c.key === cat)?.label ?? cat

  return (
    <div>
      {/* Filter Chips */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.2 }}
        className="flex flex-wrap items-center justify-center gap-2 mb-10"
        role="group"
        aria-label="Filter security controls by category"
      >
        {controlCategories.map(cat => {
          const isActive = activeFilters.has(cat.key)
          return (
            <button
              key={cat.key}
              onClick={() => toggleFilter(cat.key)}
              aria-pressed={isActive}
              className={`inline-flex items-center gap-2 px-4 py-2 rounded-full font-sans text-sm transition-all duration-200 border focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-400 ${
                isActive
                  ? 'bg-sage-500/20 border-sage-500/40 text-sage-300'
                  : 'bg-obsidian-800/60 border-obsidian-600 text-oatmeal-400 hover:border-oatmeal-400/30'
              }`}
            >
              <BrandIcon name={cat.icon} className="w-3.5 h-3.5" />
              {cat.label}
              {isActive && (
                <span className="ml-1 w-4 h-4 rounded-full bg-sage-400/30 flex items-center justify-center">
                  <BrandIcon name="checkmark" className="w-2.5 h-2.5 text-sage-300" />
                </span>
              )}
            </button>
          )
        })}

        {activeFilters.size > 0 && (
          <button
            onClick={() => setActiveFilters(new Set())}
            className="inline-flex items-center gap-1.5 px-3 py-2 rounded-full font-sans text-xs text-oatmeal-500 hover:text-oatmeal-300 transition-colors focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-400"
          >
            <BrandIcon name="x-mark" className="w-3 h-3" />
            Clear
          </button>
        )}
      </motion.div>

      {/* Control Count */}
      <motion.p
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.3 }}
        className="text-center font-sans text-xs text-oatmeal-500 mb-6"
      >
        Showing <span className="type-num-xs text-oatmeal-300">{filteredControls.length}</span> of{' '}
        <span className="type-num-xs text-oatmeal-300">{securityControls.length}</span> controls
      </motion.p>

      {/* Controls Grid */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="grid md:grid-cols-2 lg:grid-cols-3 gap-3"
        role="list"
        aria-label="Security controls"
      >
        <AnimatePresence mode="popLayout">
          {filteredControls.map(ctrl => (
            <motion.div
              key={ctrl.name}
              variants={fadeUp}
              layout
              initial={{ opacity: 0, scale: 0.95 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.95 }}
              transition={{ duration: 0.25, ease: 'easeOut' as const }}
              role="listitem"
              className="bg-obsidian-800/60 border border-obsidian-600 rounded-xl p-4 hover:border-obsidian-500/60 transition-colors"
            >
              {/* Header */}
              <div className="flex items-start justify-between gap-3 mb-2">
                <h4 className="font-sans text-sm font-medium text-oatmeal-200 leading-snug">{ctrl.name}</h4>
                <div className="flex-shrink-0 w-2 h-2 mt-1.5 rounded-full bg-sage-400" aria-label="Active control" />
              </div>

              <p className="font-sans text-[11px] text-oatmeal-500 leading-relaxed mb-3">{ctrl.description}</p>

              {/* Footer: category + standard */}
              <div className="flex items-center justify-between">
                <span className="inline-flex items-center gap-1 font-mono text-[10px] text-oatmeal-500 tracking-wider uppercase px-2 py-0.5 rounded-full bg-obsidian-700/50 border border-obsidian-600/50">
                  {getCategoryLabel(ctrl.category)}
                </span>
                <span className="font-mono text-[10px] text-sage-400/80">{ctrl.standard}</span>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </motion.div>
    </div>
  )
}

/* ─── Module 3: Compliance Status Row ────────────────────── */

function ComplianceStatusRow() {
  const statusConfig: Record<ComplianceStatus, { dot: string; badge: string; label: string }> = {
    compliant: {
      dot: 'bg-sage-400',
      badge: 'bg-sage-500/15 text-sage-400 border-sage-500/30',
      label: 'Compliant',
    },
    'in-progress': {
      dot: 'bg-oatmeal-400 animate-sage-pulse',
      badge: 'bg-oatmeal-400/10 text-oatmeal-400 border-oatmeal-400/30',
      label: 'In Progress',
    },
    planned: {
      dot: 'bg-oatmeal-300/50',
      badge: 'bg-oatmeal-300/10 text-oatmeal-400 border-oatmeal-300/30',
      label: 'Available',
    },
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, delay: 0.1 }}
      className="bg-obsidian-800/60 border border-obsidian-600 rounded-xl p-6"
    >
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {complianceMilestones.map(m => {
          const s = statusConfig[m.status]
          return (
            <div key={m.label} className="flex items-center gap-3">
              <div className={`w-3 h-3 rounded-full flex-shrink-0 ${s.dot}`} aria-hidden="true" />
              <div className="min-w-0">
                <div className="flex items-center gap-2">
                  <span className="font-serif text-sm text-oatmeal-100 font-medium">{m.label}</span>
                  <span className={`font-sans text-[10px] font-medium px-1.5 py-0.5 rounded-full border ${s.badge}`}>
                    {s.label}
                  </span>
                </div>
                <p className="font-sans text-[11px] text-oatmeal-500 truncate">{m.detail}</p>
                {m.artifact && (
                  <Link
                    href={m.artifact.href}
                    className="inline-flex items-center gap-1 font-sans text-[11px] text-sage-400 hover:text-sage-300 transition-colors mt-0.5"
                  >
                    {m.artifact.label}
                    <BrandIcon name="chevron-right" className="w-2.5 h-2.5" />
                  </Link>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}

/* ─── Module 4: Incident Preparedness Accordion ──────────── */

function PlaybookAccordion() {
  const [expandedPhase, setExpandedPhase] = useState<number | null>(null)

  const togglePhase = useCallback((idx: number) => {
    setExpandedPhase(prev => prev === idx ? null : idx)
  }, [])

  return (
    <div>
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="space-y-2 max-w-3xl mx-auto"
      >
        {playbookPhases.map((phase, i) => {
          const a = accentClasses(phase.accent)
          const isOpen = expandedPhase === i
          return (
            <motion.div key={phase.title} variants={fadeUp}>
              <button
                onClick={() => togglePhase(i)}
                aria-expanded={isOpen}
                aria-controls={`playbook-panel-${i}`}
                className={`w-full flex items-center gap-3 px-5 py-4 rounded-xl border transition-all duration-200 focus-visible:outline-hidden focus-visible:ring-2 focus-visible:ring-sage-400 ${
                  isOpen
                    ? `${a.bg} ${a.border}`
                    : 'bg-obsidian-800/60 border-obsidian-600 hover:border-obsidian-500/60'
                }`}
              >
                <div className={`w-8 h-8 rounded-lg ${a.bg} border ${a.border} flex items-center justify-center ${a.text} flex-shrink-0`}>
                  <BrandIcon name={phase.icon} className="w-4 h-4" />
                </div>
                <div className="flex-1 text-left">
                  <span className="font-serif text-sm text-oatmeal-100">{phase.title}</span>
                  <span className="font-sans text-[11px] text-oatmeal-500 ml-2">Phase {String(i + 1).padStart(2, '0')}</span>
                </div>
                <BrandIcon
                  name="chevron-right"
                  className={`w-4 h-4 text-oatmeal-500 transition-transform duration-200 ${isOpen ? 'rotate-90' : ''}`}
                />
              </button>

              <AnimatePresence>
                {isOpen && (
                  <motion.div
                    id={`playbook-panel-${i}`}
                    role="region"
                    aria-label={`${phase.title} phase details`}
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    transition={{ duration: 0.3, ease: 'easeOut' as const }}
                    className="overflow-hidden"
                  >
                    <div className="px-5 pt-3 pb-5">
                      <p className="font-sans text-sm text-oatmeal-300 leading-relaxed mb-4">{phase.description}</p>
                      <ul className="space-y-2">
                        {phase.measures.map(measure => (
                          <li key={measure} className="flex items-start gap-2.5">
                            <BrandIcon name="checkmark" className="w-3.5 h-3.5 text-sage-400 flex-shrink-0 mt-0.5" />
                            <span className="font-sans text-xs text-oatmeal-400 leading-relaxed">{measure}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  </motion.div>
                )}
              </AnimatePresence>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Enterprise CTA */}
      <motion.div
        initial={{ opacity: 0, y: 12 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5, delay: 0.3 }}
        className="text-center mt-8"
      >
        <Link
          href="/contact?inquiry_type=enterprise"
          className="inline-flex items-center gap-2.5 px-5 py-2.5 rounded-full bg-obsidian-800/70 border border-obsidian-500/40 hover:border-sage-500/30 transition-colors group font-sans text-sm text-oatmeal-400"
        >
          <BrandIcon name="shield-check" className="w-4 h-4 text-sage-400" />
          Full playbook available on request for Enterprise accounts
          <BrandIcon name="chevron-right" className="w-3.5 h-3.5 text-sage-400 group-hover:translate-x-0.5 transition-transform" />
        </Link>
      </motion.div>
    </div>
  )
}

/* ─── Page ───────────────────────────────────────────────── */

export default function TrustAndSecurity() {
  return (
    <div className="relative z-10 min-h-screen bg-gradient-obsidian">
      {/* ── Hero + Trust Metrics Bar ───────────────────────── */}
      <motion.section
        className="relative pt-32 pb-16 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="type-display-xl text-oatmeal-100 mb-6">
            Assurance Center
          </h1>
          <p className="type-body-lg text-oatmeal-400 max-w-2xl mx-auto mb-10">
            How we protect your data — and the evidence to prove it.
          </p>

          {/* Trust Metrics Bar */}
          <div className="inline-flex items-center gap-6 sm:gap-8 px-6 py-3 rounded-full bg-obsidian-800/60 border border-obsidian-600">
            <div className="text-center">
              <span className="type-proof text-oatmeal-100">
                <CountUp target={19} />
              </span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Security Controls</p>
            </div>
            <div className="w-px h-8 bg-obsidian-600" aria-hidden="true" />
            <div className="text-center">
              <span className="type-proof text-oatmeal-100">
                <CountUp target={5} />
              </span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Control Domains</p>
            </div>
            <div className="w-px h-8 bg-obsidian-600" aria-hidden="true" />
            <div className="text-center">
              <span className="type-num-lg text-sage-400">Zero</span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Raw Data Stored</p>
            </div>
          </div>

          {/* Quick Nav — updated to match new section order */}
          <nav className="mt-8 flex flex-wrap items-center justify-center gap-3" aria-label="Page sections">
            {[
              { label: 'Data Transparency', href: '#transparency' },
              { label: 'Architecture', href: '#architecture' },
              { label: 'Controls', href: '#controls' },
              { label: 'Compliance', href: '#compliance' },
              { label: 'Incident Response', href: '#playbook' },
              { label: 'Artifacts', href: '#artifacts' },
            ].map(link => (
              <a
                key={link.href}
                href={link.href}
                className="font-sans text-xs text-oatmeal-500 hover:text-sage-400 transition-colors px-3 py-1.5 rounded-full border border-obsidian-700 hover:border-sage-500/30"
              >
                {link.label}
              </a>
            ))}
          </nav>
        </div>
      </motion.section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 1: Data Transparency (promoted to #1) ──── */}
      <section id="transparency" className="py-20 px-6 lobby-surface-recessed" aria-labelledby="transparency-heading">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-10">
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="inline-block type-meta text-sage-400 mb-3"
            >
              Data Handling
            </motion.span>
            <motion.h2
              id="transparency-heading"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="type-headline text-oatmeal-100"
            >
              Data Transparency
            </motion.h2>
          </div>

          {/* Data Boundary Divider */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="relative flex items-center gap-4 mb-12"
            aria-hidden="true"
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
            <motion.div
              className="bg-obsidian-800 border-l-4 border-sage-500 rounded-r-xl p-6 md:p-8"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
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
                animate="visible"
              >
                {weStore.map(item => (
                  <motion.li key={item} variants={listItem} className="flex items-start gap-3">
                    <BrandIcon name="checkmark" className="w-4 h-4 text-sage-400 flex-shrink-0 mt-0.5" />
                    <span className="type-body-sm text-oatmeal-300">{item}</span>
                  </motion.li>
                ))}
              </motion.ul>
            </motion.div>

            <motion.div
              className="bg-obsidian-800 border-l-4 border-clay-500 rounded-r-xl p-6 md:p-8"
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
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
                animate="visible"
              >
                {weNeverStore.map(item => (
                  <motion.li key={item} variants={listItem} className="flex items-start gap-3">
                    <BrandIcon name="x-mark" className="w-4 h-4 text-clay-400 flex-shrink-0 mt-0.5" />
                    <span className="type-body-sm text-oatmeal-300">{item}</span>
                  </motion.li>
                ))}
              </motion.ul>
            </motion.div>
          </div>
        </div>
      </section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 2: Architecture Diagram (simplified) ───── */}
      <ModuleSection
        id="architecture"
        meta="Security Architecture"
        title="How We Protect Your Data"
        subtitle="Four stages. Every control documented. Zero raw data persisted."
        surface="lobby-surface-accent lobby-glow-sage overflow-hidden"
      >
        <ArchitectureDiagram />
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 3: Control Matrix (unchanged) ──────────── */}
      <ModuleSection
        id="controls"
        meta="Control Matrix"
        title="Security Control Inventory"
        subtitle="Every security control mapped to its standard reference. Filter by domain to inspect specific areas."
        surface="lobby-surface-recessed"
      >
        <ControlMatrix />
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 4: Compliance Status (condensed row) ──── */}
      <section id="compliance" className="py-16 px-6" aria-labelledby="compliance-heading">
        <div className="max-w-5xl mx-auto">
          <div className="max-w-3xl mx-auto text-center mb-10">
            <motion.span
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="inline-block type-meta text-sage-400 mb-3"
            >
              Compliance
            </motion.span>
            <motion.h2
              id="compliance-heading"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5, delay: 0.1 }}
              className="type-headline text-oatmeal-100"
            >
              Standards &amp; Certifications
            </motion.h2>
          </div>
          <ComplianceStatusRow />
        </div>
      </section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 5: Incident Preparedness (accordion) ──── */}
      <ModuleSection
        id="playbook"
        meta="Incident Response"
        title="Preparedness Playbook"
        subtitle="Our four-phase incident response posture. Zero-Storage architecture minimizes breach impact by design."
        surface="lobby-surface-accent lobby-glow-sage overflow-hidden"
      >
        <PlaybookAccordion />
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 6: Downloadable Artifacts ─────────────── */}
      <section id="artifacts" className="lobby-surface-raised py-16 px-6" aria-labelledby="artifacts-heading">
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5 }}
          >
            <span className="inline-block type-meta text-sage-400 mb-3">Documents</span>
            <h2 id="artifacts-heading" className="type-headline-sm text-oatmeal-100 mb-2">Downloadable Artifacts</h2>
            <p className="font-sans text-oatmeal-400 text-sm">
              Review our policies and request compliance documents for your due diligence.
            </p>
          </motion.div>

          <motion.div
            className="grid sm:grid-cols-2 gap-4"
            variants={containerVariants}
            initial="hidden"
            animate="visible"
          >
            {downloadableArtifacts.map(artifact => (
              <motion.div key={artifact.href} variants={fadeUp}>
                <Link
                  href={artifact.href}
                  className="flex items-start gap-4 bg-obsidian-800/60 border border-obsidian-600 rounded-xl px-5 py-4 hover:border-sage-500/30 transition-colors group"
                >
                  <div className="w-9 h-9 rounded-lg bg-sage-500/15 flex items-center justify-center text-sage-400 flex-shrink-0 mt-0.5">
                    <BrandIcon name={artifact.icon} className="w-4.5 h-4.5" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-sans text-sm font-medium text-oatmeal-200">{artifact.label}</span>
                      <span className="font-mono text-[10px] text-oatmeal-600 tracking-wider uppercase px-1.5 py-0.5 rounded-sm bg-obsidian-700/50">
                        {artifact.type}
                      </span>
                    </div>
                    <p className="font-sans text-xs text-oatmeal-500">{artifact.description}</p>
                  </div>
                  <BrandIcon name="chevron-right" className="w-4 h-4 text-oatmeal-500 group-hover:text-sage-400 group-hover:translate-x-0.5 transition-all flex-shrink-0 mt-1" />
                </Link>
              </motion.div>
            ))}
          </motion.div>
        </div>
      </section>
    </div>
  )
}
