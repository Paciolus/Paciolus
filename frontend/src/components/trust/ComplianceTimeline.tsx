import Link from 'next/link'
import { BrandIcon } from '@/components/shared'
import * as motion from '@/components/ui/motionClient'
import { complianceMilestones, type ComplianceStatus } from '@/content/trust'
import { containerVariants, lineGrow, scaleIn, vertLineGrow } from './variants'

export function ComplianceTimeline() {

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
    <div>
      {/* Desktop Timeline */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="hidden md:block relative"
      >
        {/* Connecting Line */}
        <div className="absolute top-[0.5rem] left-0 right-0 flex justify-center pointer-events-none" aria-hidden="true">
          <div className="w-full max-w-4xl flex">
            {[0, 1, 2].map(i => (
              <div key={i} className="flex-1 flex justify-center px-10">
                <motion.div
                  variants={lineGrow}
                  className="w-full h-0.5 bg-gradient-to-r from-oatmeal-400/30 to-sage-500/20"
                />
              </div>
            ))}
          </div>
        </div>

        {/* Milestone Nodes */}
        <div className="grid grid-cols-4 gap-6">
          {complianceMilestones.map(m => {
            const s = statusConfig[m.status]
            return (
              <motion.div key={m.label} variants={scaleIn} className="flex flex-col items-center">
                {/* Status Dot */}
                <div className={`w-4 h-4 rounded-full ${s.dot} mb-6 ring-4 ring-obsidian-900/80`} aria-hidden="true" />

                {/* Card */}
                <div className="bg-obsidian-800/60 border border-obsidian-600 rounded-xl p-5 w-full text-center">
                  <div className="font-mono text-[10px] text-oatmeal-600 tracking-wider mb-2">{m.year}</div>
                  <h3 className="font-serif text-lg text-oatmeal-100 mb-2">{m.label}</h3>
                  <span className={`inline-block font-sans text-xs font-medium px-2.5 py-1 rounded-full border ${s.badge}`}>
                    {s.label}
                  </span>
                  {m.selfAssessed && (
                    <div className="font-sans text-[10px] text-oatmeal-500 mt-2 italic">
                      Self-assessed — no third-party audit
                    </div>
                  )}
                  <p className="font-sans text-xs text-oatmeal-500 mt-3">{m.detail}</p>

                  {/* Artifact Link */}
                  {m.artifact && (
                    <Link
                      href={m.artifact.href}
                      className="inline-flex items-center gap-1.5 mt-3 font-sans text-xs text-sage-400 hover:text-sage-300 transition-colors group"
                    >
                      <BrandIcon name="document" className="w-3 h-3" />
                      {m.artifact.label}
                      <BrandIcon name="chevron-right" className="w-2.5 h-2.5 group-hover:translate-x-0.5 transition-transform" />
                    </Link>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      </motion.div>

      {/* Mobile Timeline */}
      <motion.div
        variants={containerVariants}
        initial="hidden"
        animate="visible"
        className="md:hidden relative"
      >
        <motion.div
          variants={vertLineGrow}
          className="absolute left-[0.45rem] top-2 bottom-2 w-0.5 bg-gradient-to-b from-sage-400/40 to-oatmeal-400/20"
          aria-hidden="true"
        />

        <div className="space-y-8">
          {complianceMilestones.map(m => {
            const s = statusConfig[m.status]
            return (
              <motion.div key={m.label} variants={scaleIn} className="relative flex items-start gap-5 pl-1">
                <div className={`flex-shrink-0 w-3.5 h-3.5 rounded-full ${s.dot} mt-1.5 ring-4 ring-obsidian-900/80`} aria-hidden="true" />
                <div className="flex-1 bg-obsidian-800/60 border border-obsidian-600 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-1">
                    <h3 className="font-serif text-base text-oatmeal-100">{m.label}</h3>
                    <span className={`font-sans text-[11px] font-medium px-2 py-0.5 rounded-full border ${s.badge}`}>
                      {s.label}
                    </span>
                  </div>
                  {m.selfAssessed && (
                    <div className="font-sans text-[10px] text-oatmeal-500 mb-1 italic">
                      Self-assessed — no third-party audit
                    </div>
                  )}
                  <div className="font-mono text-[10px] text-oatmeal-600 tracking-wider mb-1">{m.year}</div>
                  <p className="font-sans text-xs text-oatmeal-500">{m.detail}</p>
                  {m.artifact && (
                    <Link
                      href={m.artifact.href}
                      className="inline-flex items-center gap-1.5 mt-2 font-sans text-xs text-sage-400 hover:text-sage-300 transition-colors group"
                    >
                      <BrandIcon name="document" className="w-3 h-3" />
                      {m.artifact.label}
                      <BrandIcon name="chevron-right" className="w-2.5 h-2.5 group-hover:translate-x-0.5 transition-transform" />
                    </Link>
                  )}
                </div>
              </motion.div>
            )
          })}
        </div>
      </motion.div>

      {/* Attestation disclaimer */}
      <p className="font-sans text-xs text-oatmeal-600 text-center mt-8 max-w-2xl mx-auto leading-relaxed">
        GDPR and CCPA compliance reflects our self-assessed posture based on implemented controls and privacy architecture.
        Security controls listed above are implemented and active.
      </p>
    </div>
  )
}
