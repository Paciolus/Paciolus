/**
 * Trust page content (Sprint 820): the data behind `/trust`, split out of
 * the page so copy edits do not touch the rendering code. The page and the
 * `components/trust/*` blocks import from here.
 *
 * Sprint 834: `weStore` / `weNeverStore` must say exactly what the database
 * holds — keep them in step with the models.
 */

import type { BrandIconName } from '@/components/shared'

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

export type ComplianceStatus = 'compliant' | 'in-progress' | 'planned'

export interface ComplianceMilestone {
  label: string
  status: ComplianceStatus
  detail: string
  /** Sprint 844: optional — the "2024 / 2025" years were dates nothing happened on. */
  year?: string
  artifact?: { label: string; href: string }
  /** Sprint 654: flag this milestone as a self-assessment (not a third-party audit). */
  selfAssessed?: boolean
}

export interface PlaybookPhase {
  title: string
  icon: BrandIconName
  accent: AccentColor
  description: string
  measures: string[]
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
      { label: 'TLS Encryption', detail: 'Data in transit uses TLS 1.2 or higher (1.3 where supported), terminated at Vercel and Render.' },
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
      { label: 'CSRF Protection', detail: 'Stateless HMAC CSRF tokens on all state-changing operations.' },
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
      { label: 'Account Isolation', detail: 'Every database query is scoped to the signed-in account in application code.' },
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
      { label: 'Uploads Not Kept', detail: 'Uploaded files and the ledger rows in them are not saved. Analysis summaries and engagement entries are — see the lists below.' },
      { label: 'Memory Cleanup', detail: 'Uploaded data is released from memory after every analysis operation completes.' },
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
  { name: 'CSRF Protection', description: 'Stateless HMAC-based CSRF tokens on all state-changing endpoints.', category: 'authentication', standard: 'OWASP ASVS 4.2', active: true },
  { name: 'Account Lockout', description: '5 failed attempts lock the account for 15 minutes; stored in the database, surviving restarts.', category: 'authentication', standard: 'NIST 800-63B', active: true },
  { name: 'Email Verification', description: 'Token-based email verification with disposable domain blocking.', category: 'authentication', standard: 'OWASP ASVS 2.1', active: true },
  { name: 'TLS Transport', description: 'TLS 1.2+ (1.3 where supported) for all client-server communication, terminated at Vercel and Render.', category: 'transport', standard: 'RFC 8446', active: true },
  { name: 'Rate Limiting', description: 'Every route is rate-limited: 60/min by default, tighter on authentication, upload, export and write endpoints.', category: 'transport', standard: 'OWASP API4', active: true },
  { name: 'Body Size Middleware', description: 'Global request body size limits preventing oversized payload attacks.', category: 'transport', standard: 'OWASP API4', active: true },
  { name: 'CORS Hardening', description: 'Strict origin allowlist with credentialed request support.', category: 'transport', standard: 'OWASP ASVS 14.5', active: true },
  { name: 'Account-Scoped Queries', description: 'Every database query is scoped to the authenticated account in application code, designed to prevent cross-account access.', category: 'tenancy', standard: 'OWASP ASVS 4.1', active: true },
  { name: 'Diagnostic Zone Protection', description: 'Tool pages require verified authentication before any data access.', category: 'tenancy', standard: 'OWASP ASVS 4.1', active: true },
  { name: 'Soft-Delete Immutability', description: 'Audit trail records use soft-delete with ORM-level deletion guards.', category: 'tenancy', standard: 'OWASP ASVS 8.3', active: true },
  { name: 'Formula Injection Guard', description: 'All CSV/Excel exports sanitized against =, +, -, @ formula injection.', category: 'export', standard: 'CWE-1236', active: true },
  { name: 'Optional Sign-Off Block', description: 'PDF memos can include prepared-by / reviewed-by lines you complete; off by default.', category: 'export', standard: 'PCAOB AS 1215', active: true },
  { name: 'Column & Cell Limits', description: 'Upload validation enforces column count and cell count boundaries.', category: 'export', standard: 'OWASP Input Val.', active: true },
  { name: 'Uploads Not Kept', description: 'Uploaded files and line-level rows are not saved. Analysis summaries, flagged account names and engagement entries are stored.', category: 'data-handling', standard: 'GDPR Art. 25', active: true },
  { name: 'Memory Cleanup', description: 'Uploaded data released from memory after every analysis operation.', category: 'data-handling', standard: 'CWE-401', active: true },
  { name: 'Structured Logging', description: 'Request-ID correlated logs with sanitized error output. No PII in logs.', category: 'data-handling', standard: 'OWASP ASVS 7.1', active: true },
]

export const complianceMilestones: ComplianceMilestone[] = [
  {
    label: 'GDPR',
    status: 'compliant',
    detail: 'EU General Data Protection Regulation. Self-assessed against our Privacy Policy; not certified.',
    artifact: { label: 'Privacy Policy', href: '/privacy' },
    selfAssessed: true,
  },
  {
    label: 'CCPA',
    status: 'compliant',
    detail: 'California Consumer Privacy Act / CPRA. Self-assessed; not certified.',
    artifact: { label: 'Privacy Policy', href: '/privacy' },
    selfAssessed: true,
  },
  {
    label: 'DPA',
    status: 'planned',
    detail: 'Data Processing Addendum — being finalized with counsel. Available on request in the meantime.',
    artifact: { label: 'Request DPA', href: '/contact?inquiry_type=organization' },
  },
  {
    // Sprint 654: explicit SOC 2 placeholder so the absence of a third-party
    // audit is addressed in the UI rather than left silent.
    label: 'SOC 2 Type II',
    status: 'planned',
    detail: 'No SOC 2 audit has been performed and none is currently scheduled.',
  },
]

export const playbookPhases: PlaybookPhase[] = [
  {
    title: 'Detection',
    icon: 'warning-triangle',
    accent: 'oatmeal',
    description: 'Errors go to Sentry and uptime is checked every 15 minutes. There is no 24/7 on-call; incidents are handled by the founder as soon as they are seen.',
    measures: [
      'Structured logging with request-ID correlation',
      'Sentry error tracking with local variables, error text and log breadcrumbs removed',
      'Uptime probe every 15 minutes',
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
    description: 'Not keeping uploads limits exposure — there are no uploaded files or ledger rows at rest to exfiltrate.',
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
      'Regulators notified as the law requires (72 hours to an EU authority under GDPR Art. 33)',
      'Affected users told by email without undue delay',
      'A summary of what happened, for affected customers',
    ],
  },
]

export const downloadableArtifacts: DownloadableArtifact[] = [
  { label: 'Privacy Policy', description: 'What we collect, what we keep, and your rights.', href: '/privacy', icon: 'document', type: 'Policy' },
  { label: 'Terms of Service', description: 'Platform usage terms and liability framework.', href: '/terms', icon: 'clipboard-check', type: 'Legal' },
  { label: 'How We Handle Your Data', description: 'What happens to an upload, and exactly what we keep.', href: '/approach', icon: 'shield-check', type: 'Technical' },
  { label: 'Request DPA', description: 'Data Processing Addendum available on request while counsel finalizes it.', href: '/contact?inquiry_type=organization', icon: 'file-download', type: 'Organization' },
]

// Sprint 834 (CEO decision 8, 2026-10-24): these lists must say exactly what
// the database holds. The earlier copy promised Paciolus kept no account
// balances or anomaly details tied to accounts or amounts, while
// uncorrected_misstatements, analytical_expectations, diagnostic_summaries and
// tool_runs.flagged_accounts do persist such figures and names. Keep this in
// step with the models; counsel reviews the wording (tasks/ceo-actions.md).
export const weStore = [
  'User account information (name, email)',
  'Client metadata (names, industries, fiscal year-ends)',
  'Aggregate totals from each analysis (category totals, ratios, row counts, total debits and credits)',
  'Names of accounts a tool flagged (no amounts or entry details)',
  'What you enter in an engagement: materiality, follow-up notes, intercompany account mappings, analytical expectations (expected and actual values) and uncorrected misstatements (account, debit or credit, amount)',
  'Report files you choose to share by link, held encrypted for up to 48 hours and then deleted',
  'Counts of which tools you run and how many uploads you make (for your upload allowance)',
]

export const weNeverStore = [
  'Uploaded files (CSV, Excel, PDF or any other format)',
  'Line-level trial balance rows from your uploads',
  'Individual journal entries, invoices, payments or payroll records',
  'Flagged-entry details from your uploads (only flagged account names are kept, without amounts)',
]

/** Plain-English stage labels for the flow diagram */
export const FLOW_STAGES = [
  {
    id: 'upload',
    label: 'Upload',
    description: 'Your file enters encrypted',
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
    description: 'Data processed in isolation',
    icon: 'shield-check' as const,
    nodeRef: architectureNodes[2], // Process
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
