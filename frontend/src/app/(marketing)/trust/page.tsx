import Link from 'next/link'
import { BrandIcon } from '@/components/shared'
import { ArchitectureDiagram } from '@/components/trust/ArchitectureDiagram'
import { ControlMatrix } from '@/components/trust/ControlMatrix'
import { DataFlowDiagram } from '@/components/trust/DataFlowDiagram'
import { ModuleSection } from '@/components/trust/ModuleSection'
import { containerVariants, fadeUp, listItem } from '@/components/trust/variants'
import * as motion from '@/components/ui/motionClient'
import { PREVIEW_CACHE, RETENTION_STATEMENT, SHARE_RETENTION } from '@/content/storage-statement'
import { controlCategories, downloadableArtifacts, incidentStatements, policyDocuments, securityControls, trustFaq, vendorFacts, weDontKeep, weStore } from '@/content/trust'

const CONTROL_COUNT = securityControls.length
const DOMAIN_COUNT = controlCategories.length

/**
 * Trust Center — server component (Sprint 820). Data lives in
 * `content/trust.ts`; the interactive blocks (architecture diagram, control
 * matrix) are client components in
 * `components/trust/`. Mount animations use `components/ui/motionClient` elements.
 */
export default function TrustAndSecurity() {
  return (
    <main id="main-content" className="relative z-10 min-h-screen bg-gradient-obsidian">
      {/* ── Hero + Trust Metrics Bar ───────────────────────── */}
      <motion.section
        className="relative pt-32 pb-16 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2, ease: 'easeOut' as const }}
      >
        <div className="max-w-5xl mx-auto text-center">
          <h1 className="type-display-xl text-oatmeal-100 mb-6">
            Trust Center
          </h1>
          <p className="type-body-lg text-oatmeal-400 max-w-2xl mx-auto mb-10">
            How we protect your data, what we keep, and the documents you can check.
          </p>

          {/* Trust Metrics Bar */}
          <div className="inline-flex items-center gap-6 sm:gap-8 px-6 py-3 rounded-full bg-obsidian-800/60 border border-obsidian-600">
            <div className="text-center">
              <span className="type-proof text-oatmeal-100 tabular-nums">{CONTROL_COUNT}</span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Security Controls</p>
            </div>
            <div className="w-px h-8 bg-obsidian-600" aria-hidden="true" />
            <div className="text-center">
              <span className="type-proof text-oatmeal-100 tabular-nums">{DOMAIN_COUNT}</span>
              <p className="font-sans text-xs text-oatmeal-500 mt-0.5">Control Domains</p>
            </div>
          </div>

          {/* Quick Nav — updated to match new section order */}
          <nav className="mt-8 flex flex-wrap items-center justify-center gap-3" aria-label="Page sections">
            {[
              { label: 'Data Transparency', href: '#transparency' },
              { label: 'Architecture', href: '#architecture' },
              { label: 'Controls', href: '#controls' },
              { label: 'Certifications', href: '#certifications' },
              { label: 'Vendor Review', href: '#vendor-review' },
              { label: 'Questions', href: '#questions' },
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
              transition={{ duration: 0.2 }}
              className="inline-block type-meta text-sage-400 mb-3"
            >
              Data Handling
            </motion.span>
            <motion.h2
              id="transparency-heading"
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.2 }}
              className="type-headline text-oatmeal-100"
            >
              Data Transparency
            </motion.h2>
          </div>

          {/* Data Boundary Divider */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ duration: 0.2 }}
            className="relative flex items-center gap-4 mb-12"
            aria-hidden="true"
          >
            <div className="flex-1 flex items-center">
              <div className="w-2 h-2 rounded-full bg-sage-400/60" />
              <div className="flex-1 h-px bg-sage-400/30" />
            </div>
            <span className="font-sans text-xs font-medium text-oatmeal-400 tracking-wide uppercase px-3 py-1.5 rounded-full bg-obsidian-800/60 border border-obsidian-600 whitespace-nowrap">
              Your Data Boundary
            </span>
            <div className="flex-1 flex items-center">
              <div className="flex-1 h-px bg-clay-400/30" />
              <div className="w-2 h-2 rounded-full bg-clay-400/60" />
            </div>
          </motion.div>

          {/* Two-Column Store/Never Store */}
          <div className="grid md:grid-cols-2 gap-6">
            <motion.div
              className="bg-obsidian-800 border-l-4 border-sage-500 rounded-r-xl p-6 md:p-8"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.2, ease: 'easeOut' as const }}
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
              transition={{ duration: 0.2, ease: 'easeOut' as const }}
            >
              <div className="flex items-center gap-3 mb-6">
                <div className="w-8 h-8 rounded-lg bg-clay-500/15 flex items-center justify-center text-clay-400">
                  <BrandIcon name="shield-check" className="w-4.5 h-4.5" />
                </div>
                <h3 className="font-serif text-xl text-oatmeal-100">What We Don&apos;t Keep</h3>
              </div>
              <motion.ul
                className="space-y-3.5"
                variants={containerVariants}
                initial="hidden"
                animate="visible"
              >
                {weDontKeep.map(item => (
                  <motion.li key={item} variants={listItem} className="flex items-start gap-3">
                    <BrandIcon name="x-mark" className="w-4 h-4 text-clay-400 flex-shrink-0 mt-0.5" />
                    <span className="type-body-sm text-oatmeal-300">{item}</span>
                  </motion.li>
                ))}
              </motion.ul>
            </motion.div>
          </div>

          <div className="mt-8 space-y-2 max-w-3xl mx-auto">
            <p className="type-body-sm text-oatmeal-400">{PREVIEW_CACHE}</p>
            <p className="type-body-sm text-oatmeal-400">
              A report you share by link is the complete file, stored with our storage provider for {SHARE_RETENTION}.
            </p>
            <p className="type-body-sm text-oatmeal-400">{RETENTION_STATEMENT}</p>
          </div>
        </div>
      </section>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 2: Architecture Diagram ───────────────────── */}
      <ModuleSection
        id="architecture"
        meta="Security Architecture"
        title="How We Protect Your Data"
        subtitle="Four stages, and what each one keeps."
        surface="lobby-surface-accent overflow-hidden"
      >
        <div className="mb-16">
          <DataFlowDiagram />
        </div>
        <ArchitectureDiagram />
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 3: Control Matrix ────────────────────────── */}
      <ModuleSection
        id="controls"
        meta="Implemented Controls"
        title="Security Control Inventory"
        subtitle={`${CONTROL_COUNT} controls across ${DOMAIN_COUNT} domains. Expand any domain to read each one.`}
        surface="lobby-surface-recessed"
      >
        <ControlMatrix />
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 4: Certifications (Sprint 861) ───────────── */}
      <ModuleSection
        id="certifications"
        meta="Certifications"
        title="What We Do and Don&apos;t Claim"
        surface=""
      >
        <div className="max-w-3xl mx-auto space-y-6 type-body text-oatmeal-300">
          <p>
            Paciolus holds no SOC 1, SOC 2, ISO 27001 or other third-party certification, and does not claim one.
            What is in place is described in our{' '}
            <Link href="/security" className="text-sage-400 hover:text-sage-300 underline">Security Policy</Link>,
            our{' '}
            <Link href="/data-handling" className="text-sage-400 hover:text-sage-300 underline">Data Handling Architecture</Link>{' '}
            and our{' '}
            <Link href="/subprocessors" className="text-sage-400 hover:text-sage-300 underline">Subprocessor List</Link>.
          </p>
          <p>
            Our Privacy Policy explains how we handle requests under GDPR and the CCPA/CPRA, including access,
            deletion and breach notification.{' '}
            <Link href="/privacy" className="text-sage-400 hover:text-sage-300 underline">Privacy Policy</Link>
          </p>
          <p>
            A Data Processing Addendum is available on request while counsel finalizes it.{' '}
            <Link href="/contact?inquiry_type=organization" className="text-sage-400 hover:text-sage-300 underline">Request the DPA</Link>
          </p>
        </div>
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Vendor review facts (Sprint 862) ─────────────────── */}
      <ModuleSection
        id="vendor-review"
        meta="Vendor Review"
        title="Facts for Your Vendor Review"
        surface="lobby-surface-recessed"
      >
        <dl className="max-w-3xl mx-auto divide-y divide-obsidian-600 border-y border-obsidian-600">
          {vendorFacts.map(fact => (
            <div key={fact.term} className="grid sm:grid-cols-[14rem_minmax(0,1fr)] gap-x-6 gap-y-1 py-3">
              <dt className="font-serif text-oatmeal-100">{fact.term}</dt>
              <dd className="font-sans text-sm text-oatmeal-300">{fact.detail}</dd>
            </div>
          ))}
        </dl>
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Questions (Sprint 862) ───────────────────────────── */}
      <ModuleSection
        id="questions"
        meta="Questions"
        title="Direct Answers"
        surface=""
      >
        <dl className="max-w-3xl mx-auto space-y-8">
          {trustFaq.map(item => (
            <div key={item.question}>
              <dt className="font-serif text-lg text-oatmeal-100 mb-2">{item.question}</dt>
              <dd className="type-body text-oatmeal-300">{item.answer}</dd>
            </div>
          ))}
        </dl>
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Section 5: Incident response (Sprint 861) ────────── */}
      <ModuleSection
        id="playbook"
        meta="Incident Response"
        title="If Something Goes Wrong"
        surface="lobby-surface-accent"
      >
        <ul className="max-w-3xl mx-auto space-y-3">
          {incidentStatements.map(line => (
            <li key={line} className="type-body text-oatmeal-300">{line}</li>
          ))}
        </ul>
      </ModuleSection>

      <div className="lobby-divider max-w-4xl mx-auto" />

      {/* ── Downloadable Artifacts ─────────────────────────── */}
      <section id="artifacts" className="lobby-surface-raised py-16 px-6" aria-labelledby="artifacts-heading">
        <div className="max-w-4xl mx-auto">
          <motion.div
            className="text-center mb-10"
            initial={{ opacity: 0, y: 15 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2 }}
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
            {[...policyDocuments.map(doc => ({ ...doc, icon: 'shield-check' as const, type: 'Policy' })), ...downloadableArtifacts].map(artifact => (
              <motion.div key={artifact.href} variants={fadeUp}>
                <Link
                  href={artifact.href}
                  className="flex items-start gap-4 bg-obsidian-800/60 border border-obsidian-600 rounded-lg px-5 py-4 hover:border-sage-500/30 transition-colors group"
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
    </main>
  )
}
