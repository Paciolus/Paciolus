/**
 * Trust page content (Sprint 820): the data behind `/trust`, split out of
 * the page so copy edits do not touch the rendering code. The page and the
 * `components/trust/*` blocks import from here.
 *
 * Sprint 834/861: `weStore` / `weDontKeep` (from content/storage-statement.ts) must say exactly what the database
 * holds — keep them in step with the models.
 */

import type { BrandIconName } from '@/components/shared'
import { PREVIEW_CACHE, WE_DONT_KEEP, WE_KEEP } from '@/content/storage-statement'

/* ─── Types ──────────────────────────────────────────────── */

export type AccentColor = 'sage' | 'oatmeal' | 'clay'

export interface ArchitectureNode {
  id: string
  number: string
  title: string
  subtitle: string
  icon: BrandIconName
  accent: AccentColor
  boundary: 'ephemeral' | 'persistent'
  controls: { label: string; detail: string }[]
}

export type ControlCategory = 'authentication' | 'transport' | 'tenancy' | 'export' | 'data-handling'

export interface SecurityControl {
  name: string
  description: string
  category: ControlCategory
  standard: string
  active: boolean
}

export interface DownloadableArtifact {
  label: string
  description: string
  href: string
  icon: BrandIconName
  type: string
}

/* ─── Data ───────────────────────────────────────────────── */

export const architectureNodes: ArchitectureNode[] = [
  {
    id: 'ingest',
    number: '01',
    title: 'Ingest',
    subtitle: 'Secure data entry',
    icon: 'cloud-upload',
    accent: 'oatmeal',
    boundary: 'ephemeral',
    controls: [
      { label: 'HTTPS', detail: 'The site and the API are served over HTTPS (TLS) by our hosting providers, Vercel and Render.' },
      { label: 'Rate Limiting', detail: 'Brute-force protection on all authentication and upload endpoints.' },
      { label: 'Body Size Limits', detail: 'Global request body size middleware prevents oversized payload attacks.' },
    ],
  },
  {
    id: 'authenticate',
    number: '02',
    title: 'Authenticate',
    subtitle: 'Identity verification',
    icon: 'padlock',
    accent: 'sage',
    boundary: 'ephemeral',
    controls: [
      { label: 'bcrypt Password Hashing', detail: 'Passwords salted and hashed with 12 rounds of bcrypt.' },
      { label: 'CSRF Protection', detail: 'Stateless HMAC CSRF tokens on state-changing requests made while signed in.' },
      { label: 'Account Lockout', detail: 'Database-backed lockout: 5 failed attempts lock the account for 15 minutes.' },
    ],
  },
  {
    id: 'process',
    number: '03',
    title: 'Process',
    subtitle: 'Ephemeral analysis',
    icon: 'shield-check',
    accent: 'sage',
    boundary: 'ephemeral',
    controls: [
      { label: 'JWT Authentication', detail: 'Short-lived 15-minute access tokens with refresh rotation and reuse detection.' },
      { label: 'Account Isolation', detail: 'Customer-data queries are scoped to the signed-in account in application code.' },
      { label: 'Formula Injection Guard', detail: 'CSV/Excel exports sanitized against formula injection attacks.' },
    ],
  },
  {
    id: 'purge',
    number: '04',
    title: 'Purge',
    subtitle: 'Uploads not kept',
    icon: 'archive',
    accent: 'oatmeal',
    boundary: 'persistent',
    controls: [
      { label: 'Uploads Not Kept', detail: 'Uploaded files are not saved. Analysis summaries, flagged account names, engagement entries and reports you share by link are — see the lists below.' },
      { label: 'Preview Cache Limit', detail: PREVIEW_CACHE },
    ],
  },
]

export const controlCategories: { key: ControlCategory; label: string; icon: BrandIconName }[] = [
  { key: 'authentication', label: 'Authentication', icon: 'padlock' },
  { key: 'transport', label: 'Transport', icon: 'cloud-upload' },
  { key: 'tenancy', label: 'Tenancy', icon: 'users' },
  { key: 'export', label: 'Export', icon: 'file-download' },
  { key: 'data-handling', label: 'Data Handling', icon: 'shield-check' },
]

export const securityControls: SecurityControl[] = [
  { name: 'bcrypt Password Hashing', description: '12-round salted bcrypt hashing for all stored credentials.', category: 'authentication', standard: 'OWASP ASVS 2.4', active: true },
  { name: 'JWT Access Tokens', description: '15-minute stateless tokens with jti claim and refresh rotation.', category: 'authentication', standard: 'RFC 7519', active: true },
  { name: 'Refresh Token Rotation', description: '7-day refresh tokens with single-use enforcement and reuse detection.', category: 'authentication', standard: 'OAuth 2.0 BCP', active: true },
  { name: 'CSRF Protection', description: 'Stateless HMAC-based CSRF tokens on state-changing requests made while signed in.', category: 'authentication', standard: 'OWASP ASVS 4.2', active: true },
  { name: 'Account Lockout', description: 'By default, 5 failed attempts lock the account for 15 minutes; the lockout is stored in the database.', category: 'authentication', standard: 'NIST 800-63B', active: true },
  { name: 'Email Verification', description: 'Token-based email verification with disposable domain blocking.', category: 'authentication', standard: 'OWASP ASVS 2.1', active: true },
  { name: 'HTTPS Transport', description: 'The site and the API are served over HTTPS (TLS) by our hosting providers, Vercel and Render.', category: 'transport', standard: '—', active: true },
  { name: 'Rate Limiting', description: 'Every route is rate-limited: 60/min by default, tighter on authentication, upload, export and write endpoints.', category: 'transport', standard: 'OWASP API4', active: true },
  { name: 'Body Size Middleware', description: 'Global request body size limits preventing oversized payload attacks.', category: 'transport', standard: 'OWASP API4', active: true },
  { name: 'CORS Hardening', description: 'Strict origin allowlist with credentialed request support.', category: 'transport', standard: 'OWASP ASVS 14.5', active: true },
  { name: 'Account-Scoped Queries', description: 'Customer-data queries are scoped to the signed-in account in application code, to prevent one customer reading another’s data.', category: 'tenancy', standard: 'OWASP ASVS 4.1', active: true },
  { name: 'Verified-Account Gate', description: 'Tool endpoints require a signed-in account with a verified email address.', category: 'tenancy', standard: 'OWASP ASVS 4.1', active: true },
  { name: 'Soft-Delete Immutability', description: 'Audit trail records use soft-delete with ORM-level deletion guards.', category: 'tenancy', standard: 'OWASP ASVS 8.3', active: true },
  { name: 'Formula Injection Guard', description: 'All CSV/Excel exports sanitized against =, +, -, @ formula injection.', category: 'export', standard: 'CWE-1236', active: true },
  { name: 'Upload Size Limits', description: 'Uploads are checked against column-count, row-count and cell-length limits.', category: 'export', standard: 'OWASP Input Val.', active: true },
  { name: 'Uploads Not Kept', description: 'Uploaded files are not saved. Analysis summaries, flagged account names, engagement entries and reports you share by link are.', category: 'data-handling', standard: '—', active: true },
  { name: 'Preview Cache Limit', description: 'A previewed PDF or workbook is held in memory for up to 10 minutes so the tool can reuse it, with at most 100 held at once.', category: 'data-handling', standard: '—', active: true },
  { name: 'Structured Logging', description: 'Request-ID correlated logs with sanitized error output.', category: 'data-handling', standard: 'OWASP ASVS 7.1', active: true },
]

/**
 * Sprint 861 (CEO decision 2026-11-14): three plain sentences replace the
 * four-phase playbook, which published commitments ("immediate isolation")
 * a one-person operation could fail to meet. Say only what is true.
 */
export const incidentStatements = [
  'Errors are reported to Sentry and the site is checked for uptime every 15 minutes.',
  'Incidents are handled by the founder as soon as they are seen; there is no 24/7 on-call.',
  'If personal data is affected, we notify affected users and regulators as the law requires.',
]

export const downloadableArtifacts: DownloadableArtifact[] = [
  { label: 'Privacy Policy', description: 'What we collect, what we keep, and your rights.', href: '/privacy', icon: 'document', type: 'Policy' },
  { label: 'Terms of Service', description: 'Platform usage terms and liability framework.', href: '/terms', icon: 'clipboard-check', type: 'Legal' },
  { label: 'How We Handle Your Data', description: 'What happens to an upload, and exactly what we keep.', href: '/approach', icon: 'shield-check', type: 'Technical' },
  { label: 'Request DPA', description: 'Data Processing Addendum available on request while counsel finalizes it.', href: '/contact?inquiry_type=organization', icon: 'file-download', type: 'Organization' },
]

// Sprint 861: the lists live in `content/storage-statement.ts` so the Trust
// and Approach pages cannot drift apart.
export const weStore = WE_KEEP
export const weDontKeep = WE_DONT_KEEP

/** Plain-English stage labels for the flow diagram */
export const FLOW_STAGES = [
  {
    id: 'upload',
    label: 'Upload',
    description: 'Sent to us over TLS',
    icon: 'cloud-upload' as const,
    nodeRef: architectureNodes[0], // Ingest
  },
  {
    id: 'verify',
    label: 'Verify',
    description: 'Your identity is confirmed',
    icon: 'padlock' as const,
    nodeRef: architectureNodes[1], // Authenticate
  },
  {
    id: 'analyze',
    label: 'Analyze',
    description: 'Processed in memory',
    icon: 'shield-check' as const,
    nodeRef: architectureNodes[2], // Process
  },
]

/* ─── Published documents (Sprint 862) ───────────────────── */

/** The compliance documents published on the site from docs/04-compliance/. */
export const policyDocuments = [
  { label: 'Security Policy', href: '/security', description: 'What is in place: controls, certifications we do not hold, backups and incidents.' },
  { label: 'Data Handling Architecture', href: '/data-handling', description: 'Every table that stores your data, how long it is kept, and what deletion removes.' },
  { label: 'Subprocessor List', href: '/subprocessors', description: 'The third parties that process data for Paciolus, and where.' },
] as const

/** Facts for a vendor review — each one checkable in the documents above. */
export const vendorFacts: { term: string; detail: string }[] = [
  { term: 'Certifications', detail: 'None held or claimed (no SOC 1, SOC 2 or ISO 27001).' },
  { term: 'Where uploads are processed', detail: 'Render, United States (Virginia).' },
  { term: 'Where the database is', detail: 'Neon, United States (N. Virginia, us-east-1).' },
  { term: 'Shared reports and backups', detail: 'Cloudflare R2, Eastern North America.' },
  { term: 'Every other service', detail: 'Listed, with its region, in the Subprocessor List.' },
  { term: 'Backups', detail: 'Daily, kept as 30 daily and 12 monthly copies; a restore is tested monthly.' },
  { term: 'Data Processing Addendum', detail: 'Available on request while counsel finalizes it.' },
  { term: 'Security contact', detail: 'security@paciolus.com' },
  { term: 'Support', detail: 'Email, with a reply within 1–2 business days.' },
]

/**
 * Trust FAQ (Sprint 862). The CEO brief allows AU-C 230 and PCAOB AS 1215 to be
 * named only here, in answer to a direct question, AU-C 230 first;
 * `backend/tests/test_marketing_claims.py` allows exactly these lines.
 */
export const trustFaq: { question: string; answer: string }[] = [
  {
    question: 'Does Paciolus satisfy AU-C 230 or PCAOB AS 1215?',
    answer: 'No. AU-C 230 and PCAOB AS 1215 set documentation and retention duties for audit firms, not for software vendors, so Paciolus does not claim compliance with them. Paciolus produces PDF memos and Excel/CSV workpapers. Your firm keeps them in its own documentation system; Paciolus is not a workpaper archive.',
  },
  {
    question: 'Does Paciolus hold a SOC 2 report or any other certification?',
    answer: 'No. Paciolus holds no SOC 1, SOC 2, ISO 27001 or other third-party certification, and does not claim one. The Security Policy describes what is in place.',
  },
  {
    question: 'If I delete my account, is everything gone?',
    answer: 'Deleting your account deletes your data from our database and removes your shared reports. Copies in our database backups are deleted as those backups age out, within 12 months.',
  },
]

/* ─── Accent Utilities ───────────────────────────────────── */

export function accentClasses(accent: AccentColor) {
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
