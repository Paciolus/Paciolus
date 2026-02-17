import Link from 'next/link'
import Image from 'next/image'

const footerLinks = [
  { label: 'Privacy Policy', href: '/privacy' },
  { label: 'Terms of Service', href: '/terms' },
  { label: 'Trust & Security', href: '/trust' },
  { label: 'Contact', href: '/contact' },
]

/**
 * Shared marketing footer for public pages.
 * 3-column layout with links + mandatory professional disclaimer.
 */
export function MarketingFooter() {
  return (
    <footer className="border-t border-obsidian-600/30 bg-obsidian-900/50">
      {/* Main Footer */}
      <div className="max-w-6xl mx-auto px-6 py-10">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* Column 1: Brand */}
          <div>
            <Link href="/" className="inline-block mb-3">
              <Image
                src="/PaciolusLogo_DarkBG.png"
                alt="Paciolus"
                width={370}
                height={510}
                className="h-8 w-auto object-contain"
              />
            </Link>
            <p className="font-sans text-sm text-oatmeal-600 leading-relaxed">
              Professional Audit Analytics Platform.
              <br />
              Zero-Storage architecture by design.
            </p>
          </div>

          {/* Column 2: Links */}
          <div>
            <h4 className="font-serif text-sm font-semibold text-oatmeal-300 mb-4 uppercase tracking-wider">
              Resources
            </h4>
            <ul className="space-y-2">
              {footerLinks.map((link) => (
                <li key={link.href}>
                  <Link
                    href={link.href}
                    className="font-sans text-sm text-oatmeal-500 hover:text-oatmeal-300 transition-colors"
                  >
                    {link.label}
                  </Link>
                </li>
              ))}
              <li>
                <Link
                  href="/about"
                  className="font-sans text-sm text-oatmeal-500 hover:text-oatmeal-300 transition-colors"
                >
                  About
                </Link>
              </li>
              <li>
                <Link
                  href="/approach"
                  className="font-sans text-sm text-oatmeal-500 hover:text-oatmeal-300 transition-colors"
                >
                  Our Approach
                </Link>
              </li>
            </ul>
          </div>

          {/* Column 3: Motto + Copyright */}
          <div className="flex flex-col justify-between">
            <div>
              <h4 className="font-serif text-sm font-semibold text-oatmeal-300 mb-4 uppercase tracking-wider">
                Get Started
              </h4>
              <ul className="space-y-2">
                <li>
                  <Link
                    href="/pricing"
                    className="font-sans text-sm text-oatmeal-500 hover:text-oatmeal-300 transition-colors"
                  >
                    Pricing
                  </Link>
                </li>
                <li>
                  <Link
                    href="/register"
                    className="font-sans text-sm text-oatmeal-500 hover:text-oatmeal-300 transition-colors"
                  >
                    Create Account
                  </Link>
                </li>
                <li>
                  <Link
                    href="/login"
                    className="font-sans text-sm text-oatmeal-500 hover:text-oatmeal-300 transition-colors"
                  >
                    Sign In
                  </Link>
                </li>
              </ul>
            </div>
            <p className="font-sans text-xs text-oatmeal-600 italic mt-6">
              &ldquo;Particularis de Computis et Scripturis&rdquo;
            </p>
          </div>
        </div>
      </div>

      {/* Disclaimer Bar */}
      <div className="border-t border-obsidian-600/20 bg-obsidian-900/80">
        <div className="max-w-6xl mx-auto px-6 py-4">
          <p className="font-sans text-xs text-oatmeal-700 leading-relaxed text-center">
            Paciolus is a data analytics tool for financial professionals. It does not perform audits,
            provide assurance opinions, or generate audit evidence. Professional judgment is required
            to evaluate all platform outputs.
          </p>
          <p className="font-sans text-xs text-oatmeal-700 text-center mt-2">
            &copy; {new Date().getFullYear()} Paciolus, Inc. All rights reserved.
          </p>
        </div>
      </div>
    </footer>
  )
}
