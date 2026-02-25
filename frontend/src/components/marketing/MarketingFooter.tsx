import Image from 'next/image'
import Link from 'next/link'
import { BrandIcon } from '@/components/shared'

/**
 * MarketingFooter — Sprint 338 Redesign
 *
 * 4-column strategic layout:
 * - Brand: logo, tagline, zero-storage badge
 * - Solutions: tool + workspace links
 * - Resources: about, approach, trust, contact
 * - Legal: privacy, terms, pricing, auth links
 *
 * Features:
 * - Underline-slide hover on all links (matches nav)
 * - BrandIcon accent on zero-storage badge
 * - Sage top-border accent on footer boundary
 * - Professional disclaimer bar preserved
 */

interface FooterLink {
  label: string
  href: string
}

const SOLUTIONS_LINKS: FooterLink[] = [
  { label: 'TB Diagnostics', href: '/tools/trial-balance' },
  { label: 'Testing Suite', href: '/tools/journal-entry-testing' },
  { label: 'Diagnostic Workspace', href: '/engagements' },
  { label: 'Pricing', href: '/pricing' },
]

const COMPANY_LINKS: FooterLink[] = [
  { label: 'About', href: '/about' },
  { label: 'Our Approach', href: '/approach' },
  { label: 'Trust & Security', href: '/trust' },
  { label: 'Contact', href: '/contact' },
]

const LEGAL_LINKS: FooterLink[] = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
]

function FooterLinkList({ title, links }: { title: string; links: FooterLink[] }) {
  return (
    <div>
      <h4 className="font-serif text-xs font-semibold text-oatmeal-300 uppercase tracking-[0.15em] mb-4">
        {title}
      </h4>
      <ul className="space-y-2.5">
        {links.map((link) => (
          <li key={link.href}>
            <Link
              href={link.href}
              className="group inline-flex items-center font-sans text-sm text-oatmeal-500 hover:text-oatmeal-200 transition-colors duration-200"
            >
              <span className="relative">
                {link.label}
                <span className="absolute -bottom-0.5 left-0 right-0 h-px bg-sage-500/50 scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
              </span>
            </Link>
          </li>
        ))}
      </ul>
    </div>
  )
}

export function MarketingFooter() {
  return (
    <footer className="relative z-10">
      {/* Sage accent line */}
      <div className="h-px bg-gradient-to-r from-transparent via-sage-500/30 to-transparent" />

      {/* Main Footer */}
      <div className="border-t border-obsidian-500/20 bg-obsidian-900/70">
        <div className="max-w-6xl mx-auto px-6 py-12">
          <div className="grid grid-cols-2 md:grid-cols-4 gap-10 md:gap-8">
            {/* Column 1: Brand */}
            <div className="col-span-2 md:col-span-1">
              <Link href="/" className="inline-block mb-4 group">
                <Image
                  src="/PaciolusLogo_DarkBG.png"
                  alt="Paciolus"
                  width={370}
                  height={510}
                  className="h-8 w-auto object-contain transition-opacity group-hover:opacity-80"
                />
              </Link>
              <p className="font-sans text-sm text-oatmeal-500 leading-relaxed mb-4">
                Professional audit diagnostic intelligence.
                <br />
                Built for financial professionals.
              </p>
              {/* Zero-Storage badge */}
              <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-obsidian-800/60 border border-obsidian-500/20">
                <BrandIcon name="padlock" className="w-3.5 h-3.5 text-sage-500" />
                <span className="font-sans text-xs text-oatmeal-400">Zero-Storage Architecture</span>
              </div>
            </div>

            {/* Column 2: Solutions */}
            <FooterLinkList title="Solutions" links={SOLUTIONS_LINKS} />

            {/* Column 3: Company */}
            <FooterLinkList title="Company" links={COMPANY_LINKS} />

            {/* Column 4: Legal + Auth */}
            <div>
              <h4 className="font-serif text-xs font-semibold text-oatmeal-300 uppercase tracking-[0.15em] mb-4">
                Legal
              </h4>
              <ul className="space-y-2.5">
                {LEGAL_LINKS.map((link) => (
                  <li key={link.href}>
                    <Link
                      href={link.href}
                      className="group inline-flex items-center font-sans text-sm text-oatmeal-500 hover:text-oatmeal-200 transition-colors duration-200"
                    >
                      <span className="relative">
                        {link.label}
                        <span className="absolute -bottom-0.5 left-0 right-0 h-px bg-sage-500/50 scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                      </span>
                    </Link>
                  </li>
                ))}
              </ul>

              {/* Auth shortcuts */}
              <div className="mt-6 pt-4 border-t border-obsidian-500/20 space-y-2.5">
                <Link
                  href="/register"
                  className="group inline-flex items-center gap-1.5 font-sans text-sm text-sage-400 hover:text-sage-300 transition-colors duration-200"
                >
                  <span className="relative">
                    Start Free Trial
                    <span className="absolute -bottom-0.5 left-0 right-0 h-px bg-sage-400/50 scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                  </span>
                  <BrandIcon name="chevron-right" className="w-3.5 h-3.5 transform group-hover:translate-x-0.5 transition-transform duration-200" />
                </Link>
                <br />
                <Link
                  href="/login"
                  className="group inline-flex items-center font-sans text-sm text-oatmeal-500 hover:text-oatmeal-200 transition-colors duration-200"
                >
                  <span className="relative">
                    Sign In
                    <span className="absolute -bottom-0.5 left-0 right-0 h-px bg-sage-500/50 scale-x-0 group-hover:scale-x-100 transition-transform duration-300 origin-left" />
                  </span>
                </Link>
              </div>
            </div>
          </div>

          {/* Motto */}
          <div className="mt-10 pt-6 border-t border-obsidian-500/15 flex items-center justify-center">
            <p className="font-serif text-xs text-oatmeal-600 italic tracking-wide">
              &ldquo;Particularis de Computis et Scripturis&rdquo;
            </p>
          </div>
        </div>
      </div>

      {/* Disclaimer Bar */}
      <div className="border-t border-obsidian-500/15 bg-obsidian-900/90">
        <div className="max-w-6xl mx-auto px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
          <p className="font-sans text-[11px] text-oatmeal-700 leading-relaxed max-w-2xl">
            Paciolus is a data analytics tool for financial professionals. It does not perform audits,
            provide assurance opinions, or generate audit evidence. Professional judgment is required
            to evaluate all platform outputs.
          </p>
          <p className="font-sans text-[11px] text-oatmeal-700 shrink-0">
            &copy; {new Date().getFullYear()} Paciolus, Inc.
          </p>
        </div>
      </div>
    </footer>
  )
}
