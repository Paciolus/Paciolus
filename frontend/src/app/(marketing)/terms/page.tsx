import Link from 'next/link'
import { Reveal } from '@/components/ui/Reveal'

export default function TermsPage() {
  return (
    <div className="relative z-10 min-h-screen bg-gradient-obsidian">
      <main id="main-content" className="max-w-4xl mx-auto px-6 py-16">
        {/* Hero */}
        <Reveal className="mb-12">
          <h1 className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-4">
            Terms of Service
          </h1>
          <p className="font-sans text-oatmeal-400 text-lg mb-4">
            Effective Date: February 4, 2026
          </p>
          <div className="bg-clay-500/10 border-l-4 border-clay-500 p-4 rounded-r-lg">
            <p className="font-sans text-oatmeal-300">
              This is a legal agreement between you and Paciolus, Inc. Please read it carefully.
            </p>
          </div>
        </Reveal>

        {/* Table of Contents */}
        <Reveal delay={0.1} className="bg-obsidian-800 border border-obsidian-700 rounded-lg p-6 mb-12">
          <h2 className="font-serif text-2xl text-oatmeal-100 mb-4">Table of Contents</h2>
          <nav aria-label="Table of contents" className="grid grid-cols-1 md:grid-cols-2 gap-2">
            <Link href="#section-1" className="text-sage-400 hover:text-sage-300 underline font-sans">
              1. Service Description
            </Link>
            <Link href="#section-2" className="text-sage-400 hover:text-sage-300 underline font-sans">
              2. Eligibility
            </Link>
            <Link href="#section-3" className="text-sage-400 hover:text-sage-300 underline font-sans">
              3. Account Registration
            </Link>
            <Link href="#section-4" className="text-sage-400 hover:text-sage-300 underline font-sans">
              4. Acceptable Use
            </Link>
            <Link href="#section-5" className="text-sage-400 hover:text-sage-300 underline font-sans">
              5. How We Handle Your Data
            </Link>
            <Link href="#section-6" className="text-sage-400 hover:text-sage-300 underline font-sans">
              6. Intellectual Property
            </Link>
            <Link href="#section-7" className="text-sage-400 hover:text-sage-300 underline font-sans">
              7. User Content
            </Link>
            <Link href="#section-8" className="text-sage-400 hover:text-sage-300 underline font-sans">
              8. Fees and Payment
            </Link>
            <Link href="#section-9" className="text-sage-400 hover:text-sage-300 underline font-sans">
              9. Disclaimer of Warranties
            </Link>
            <Link href="#section-10" className="text-sage-400 hover:text-sage-300 underline font-sans">
              10. Limitation of Liability
            </Link>
            <Link href="#section-11" className="text-sage-400 hover:text-sage-300 underline font-sans">
              11. Indemnification
            </Link>
            <Link href="#section-12" className="text-sage-400 hover:text-sage-300 underline font-sans">
              12. Termination
            </Link>
            <Link href="#section-13" className="text-sage-400 hover:text-sage-300 underline font-sans">
              13. Dispute Resolution
            </Link>
            <Link href="#section-14" className="text-sage-400 hover:text-sage-300 underline font-sans">
              14. Modifications
            </Link>
            <Link href="#section-15" className="text-sage-400 hover:text-sage-300 underline font-sans">
              15. General Provisions
            </Link>
            <Link href="#section-16" className="text-sage-400 hover:text-sage-300 underline font-sans">
              16. Contact Information
            </Link>
          </nav>
        </Reveal>

        {/* Content */}
        <Reveal delay={0.2} className="prose prose-invert max-w-none">
          {/* Section 1: Service Description */}
          <section id="section-1">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              1. Service Description
            </h2>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              1.1 What Paciolus Provides
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              Paciolus is a trial balance diagnostic intelligence platform designed for professional accountants, auditors, and financial analysts. Our service includes:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Trial balance upload and analysis (CSV/Excel format)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Automated account classification and anomaly detection</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Materiality threshold configuration</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Diagnostic summary reports (PDF/Excel exports)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Client metadata management</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Activity history tracking (aggregate summaries only)</span>
              </li>
            </ul>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              1.2 What Paciolus Does NOT Provide
            </h3>
            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-4 rounded-r-lg mb-6">
              <p className="font-sans text-oatmeal-300 font-semibold mb-3">CRITICAL: Paciolus does NOT provide:</p>
              <ul className="space-y-2">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Accounting services</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Audit services or audit opinions</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Tax advice or preparation</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Financial advisory services</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Assurance or attestation services</span>
                </li>
              </ul>
            </div>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              1.3 Professional Judgment Required
            </h3>
            <div className="bg-sage-500/10 border-l-4 border-sage-500 p-4 rounded-r-lg mb-6">
              <p className="font-sans text-oatmeal-300">
                All outputs from Paciolus are diagnostic indicators, not conclusions. Users must apply professional judgment, perform independent verification, and comply with all applicable professional standards. Paciolus does not replace audit procedures, substantive testing, or professional skepticism.
              </p>
            </div>
          </section>

          {/* Section 2: Eligibility */}
          <section id="section-2">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              2. Eligibility
            </h2>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              To use Paciolus, you must:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Be at least 18 years of age</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Be a professional accountant, auditor, financial analyst, or similar role (CPA, CA, ACCA, or equivalent credential preferred)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Have the legal capacity to enter into binding agreements</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Not be prohibited from using the service under applicable laws</span>
              </li>
            </ul>
          </section>

          {/* Section 3: Account Registration */}
          <section id="section-3">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              3. Account Registration
            </h2>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              When you create a Paciolus account:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You must provide accurate, complete, and current information</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You are limited to one account per person</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You are responsible for maintaining the confidentiality of your password</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You accept responsibility for all activity under your account</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You must notify us immediately of any unauthorized access</span>
              </li>
            </ul>
          </section>

          {/* Section 4: Acceptable Use */}
          <section id="section-4">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              4. Acceptable Use
            </h2>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              4.1 Permitted Uses
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              You may use Paciolus for:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Professional financial analysis and diagnostic purposes</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Internal quality control and review procedures</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Educational and training purposes within your organization</span>
              </li>
            </ul>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              4.2 Prohibited Uses
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              You may NOT:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Use the service for any illegal purpose or in violation of professional standards</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Upload data you do not have permission to analyze</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Reverse engineer, decompile, or attempt to derive source code from the platform</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Engage in excessive automated queries, stress testing, or denial-of-service attacks</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Resell, sublicense, or redistribute Paciolus outputs as a standalone service</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Share your account credentials with others</span>
              </li>
            </ul>
          </section>

          {/* Section 5: How We Handle Your Data (Sprint 841: facts corrected; counsel reviews the wording) */}
          <section id="section-5">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              5. How We Handle Your Data
            </h2>
            <div className="bg-sage-500/10 border-l-4 border-sage-500 p-4 rounded-r-lg mb-6">
              <p className="font-sans text-oatmeal-300 font-semibold mb-2">
                Your uploaded files are processed in memory and not kept after analysis.
              </p>
              <p className="font-sans text-oatmeal-400">
                We do store your account, your client list, a summary of each analysis and anything you enter in an engagement, as described below and in our <Link href="/privacy" className="text-sage-400 hover:text-sage-300 underline">Privacy Policy</Link>.
              </p>
            </div>
            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              5.1 Processing an Upload
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              When you upload a file:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">The file is held in server memory for the duration of the request and is not written to disk</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Analysis results are returned to your browser</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">The uploaded file and the line-level rows in it are then released from memory and not kept</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">If you previewed the file first, its contents are held in memory for up to 10 minutes so the tool can reuse them, then released</span>
              </li>
            </ul>
            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              5.2 What We Store
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              Paciolus stores:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Your account details (name, email, hashed password)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Client metadata (company names, industry classifications, fiscal year-ends)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Practice configuration settings (materiality thresholds, testing thresholds, preferences)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">A summary of each analysis: category totals, ratios, row counts, total debits and credits, the materiality used, anomaly counts, the first characters of the filename and a hash of it</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">The names of accounts a tool flagged (without amounts or entry details)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Anything you enter in an engagement, including materiality, follow-up items, intercompany mappings, analytical expectations (expected and actual values) and uncorrected misstatements (account, debit or credit, amount)</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Reports you choose to share by link, stored encrypted with our storage provider for up to 48 hours and then deleted</span>
              </li>
            </ul>
            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              5.3 What We Do Not Store
            </h3>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Uploaded files, or copies of them</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">The line-level rows in your uploads: individual account balances, journal entries, invoices, payments or payroll records</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">The detail behind a flag (the specific entries and amounts), beyond the flagged account names above</span>
              </li>
            </ul>
            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              5.4 What This Means for You
            </h3>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Your saved history holds summaries, not your files; to re-run a test you upload the file again</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Line-level detail lives in the reports you export, so download the reports you need for your workpapers</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Because we keep summaries and engagement entries, they are covered by our security measures and the deletion rights in our Privacy Policy</span>
              </li>
            </ul>
          </section>

          {/* Section 6: Intellectual Property */}
          <section id="section-6">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              6. Intellectual Property
            </h2>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              Paciolus, Inc. retains all rights, title, and interest in:
            </p>
            <ul className="space-y-2 mb-4">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">The Paciolus platform, software, and algorithms</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Trademarks, logos, and branding</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">All diagnostic methodologies and classification logic</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Report templates and export formats</span>
              </li>
            </ul>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              You retain all rights to your own data (client metadata, trial balances you upload, etc.).
            </p>
          </section>

          {/* Section 7: User Content */}
          <section id="section-7">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              7. User Content
            </h2>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              You own all content you create in Paciolus, including:
            </p>
            <ul className="space-y-2 mb-4">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Follow-up item narratives and documentation</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Client metadata and customizations</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Practice configuration settings</span>
              </li>
            </ul>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              By using Paciolus, you grant us a limited, non-exclusive license to:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Display and process your content to provide the service</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Make backups and maintain system integrity</span>
              </li>
            </ul>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              This license ends when you delete your account or terminate service.
            </p>
          </section>

          {/* Section 8: Fees and Payment */}
          <section id="section-8">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              8. Fees and Payment
            </h2>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              8.1 Subscription Tiers
            </h3>
            <div className="overflow-x-auto">
            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-700">
                  <th className="font-serif text-oatmeal-100 text-left p-3">Tier</th>
                  <th className="font-serif text-oatmeal-100 text-left p-3">Price</th>
                  <th className="font-serif text-oatmeal-100 text-left p-3">Features</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="font-sans text-oatmeal-300 p-3">Free</td>
                  <td className="font-mono text-oatmeal-300 p-3">$0</td>
                  <td className="font-sans text-oatmeal-400 p-3">Basic ratio analysis, limited diagnostics (10/mo, 3 clients)</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="font-sans text-oatmeal-300 p-3">Solo</td>
                  <td className="font-mono text-oatmeal-300 p-3">$100/mo or $1,000/yr</td>
                  <td className="font-sans text-oatmeal-400 p-3">All 18 tools, PDF/Excel/CSV export, 100 uploads/mo, unlimited clients</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="font-sans text-oatmeal-300 p-3">Professional</td>
                  <td className="font-mono text-oatmeal-300 p-3">$500/mo or $5,000/yr</td>
                  <td className="font-sans text-oatmeal-400 p-3">All 18 tools, all exports, 500 uploads/mo, unlimited clients, 7 seats included (up to 20), admin dashboard</td>
                </tr>
                <tr>
                  <td className="font-sans text-oatmeal-300 p-3">Enterprise</td>
                  <td className="font-mono text-oatmeal-300 p-3">$1,000/mo or $10,000/yr</td>
                  <td className="font-sans text-oatmeal-400 p-3">All 18 tools, all exports, unlimited uploads/clients, 20 seats included (up to 100), custom PDF branding, bulk upload</td>
                </tr>
              </tbody>
            </table>
            </div>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              8.2 Payment Terms
            </h3>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Payments are processed through Stripe</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Subscriptions auto-renew unless cancelled</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You may cancel at any time with no penalty</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Price changes require 30 days advance notice</span>
              </li>
            </ul>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              8.3 Refund Policy
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              We offer a 30-day money-back guarantee for first-time paid subscribers (Solo, Professional or Enterprise). Refunds are issued manually. To request a refund, contact{' '}
              <Link href="mailto:support@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">
                support@paciolus.com
              </Link>
              .
            </p>
          </section>

          {/* Section 9: Disclaimer of Warranties */}
          <section id="section-9">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              9. Disclaimer of Warranties
            </h2>
            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-6 rounded-r-lg mb-6">
              <p className="font-sans text-oatmeal-300 font-bold text-lg mb-4 uppercase">
                Important Legal Disclaimer
              </p>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-4">
                PACIOLUS IS PROVIDED "AS IS" AND "AS AVAILABLE" WITHOUT WARRANTIES OF ANY KIND, EITHER EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO:
              </p>
              <ul className="space-y-2 mb-4">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Warranties of merchantability or fitness for a particular purpose</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Warranties that the service will be uninterrupted, error-free, or secure</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Warranties that diagnostic outputs are complete, accurate, or suitable for use as audit evidence</span>
                </li>
              </ul>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-4">
                WE DO NOT WARRANT THAT:
              </p>
              <ul className="space-y-2 mb-4">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Paciolus will detect all anomalies, errors, or fraud in financial data</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Outputs are suitable as a substitute for professional audit procedures</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Use of Paciolus will satisfy any regulatory or professional standard requirements</span>
                </li>
              </ul>
              <p className="font-sans text-oatmeal-300 leading-relaxed font-semibold">
                YOU ARE SOLELY RESPONSIBLE FOR VERIFYING ALL OUTPUTS AND EXERCISING PROFESSIONAL JUDGMENT.
              </p>
            </div>
          </section>

          {/* Section 10: Limitation of Liability */}
          <section id="section-10">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              10. Limitation of Liability
            </h2>
            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-6 rounded-r-lg mb-6">
              <p className="font-sans text-oatmeal-300 font-bold text-lg mb-4 uppercase">
                Critical Liability Cap
              </p>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-4">
                TO THE MAXIMUM EXTENT PERMITTED BY LAW, PACIOLUS, INC.'S TOTAL LIABILITY TO YOU FOR ALL CLAIMS ARISING FROM OR RELATED TO THE SERVICE IS LIMITED TO THE AMOUNT YOU PAID US IN THE 12 MONTHS PRECEDING THE CLAIM (OR $100 IF YOU ARE ON THE FREE TIER).
              </p>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-4">
                IN NO EVENT WILL PACIOLUS BE LIABLE FOR:
              </p>
              <ul className="space-y-2 mb-4">
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Indirect, incidental, special, consequential, or punitive damages</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Lost profits, revenue, or business opportunities</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Loss of data, goodwill, or reputation</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Professional liability or malpractice claims arising from your use of Paciolus</span>
                </li>
                <li className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-clay-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
                  </svg>
                  <span className="font-sans text-oatmeal-300">Regulatory penalties or sanctions resulting from reliance on Paciolus outputs</span>
                </li>
              </ul>
              <p className="font-sans text-oatmeal-300 leading-relaxed font-semibold">
                THIS LIMITATION APPLIES EVEN IF PACIOLUS HAS BEEN ADVISED OF THE POSSIBILITY OF SUCH DAMAGES.
              </p>
            </div>
          </section>

          {/* Section 11: Indemnification */}
          <section id="section-11">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              11. Indemnification
            </h2>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              You agree to indemnify, defend, and hold harmless Paciolus, Inc., its officers, directors, employees, and agents from any claims, damages, losses, liabilities, and expenses (including reasonable attorneys' fees) arising from:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Your use or misuse of the service</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Your violation of these Terms of Service</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Your violation of any third-party rights</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Professional services you provide using Paciolus outputs</span>
              </li>
            </ul>
          </section>

          {/* Section 12: Termination */}
          <section id="section-12">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              12. Termination
            </h2>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              12.1 Your Right to Terminate
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              You may terminate your account at any time by contacting{' '}
              <Link href="mailto:support@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">
                support@paciolus.com
              </Link>
              {' '}or using the account deletion feature in Settings.
            </p>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              12.2 Our Right to Terminate
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              We may suspend or terminate your account if:
            </p>
            <ul className="space-y-2 mb-4">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You violate these Terms of Service</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Your payment fails or your account is past due</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">You engage in prohibited activities or abuse the service</span>
              </li>
            </ul>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              12.3 Effect of Termination
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              Upon termination:
            </p>
            <ul className="space-y-2 mb-6">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Your access to Paciolus will be revoked immediately</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">All stored metadata (client names, settings) will be deleted within 30 days</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Uploaded files were never kept; the analysis summaries and engagement entries we hold are deleted with your other stored data</span>
              </li>
            </ul>
          </section>

          {/* Section 13: Dispute Resolution */}
          <section id="section-13">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              13. Dispute Resolution
            </h2>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              13.1 Governing Law
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              These Terms are governed by the laws of the State of Delaware, United States, without regard to conflict of law principles.
            </p>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              13.2 Mandatory Arbitration
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              Any dispute, claim, or controversy arising from or related to these Terms or the use of Paciolus will be resolved by binding arbitration administered by JAMS (Judicial Arbitration and Mediation Services) in accordance with its Streamlined Arbitration Rules and Procedures.
            </p>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              13.3 Class Action Waiver
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              You agree that any arbitration or proceeding will be limited to the dispute between you and Paciolus individually. You waive any right to participate in a class action, collective action, or representative proceeding.
            </p>
          </section>

          {/* Section 14: Modifications */}
          <section id="section-14">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              14. Modifications to Terms
            </h2>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              We reserve the right to modify these Terms at any time. Material changes will be communicated via:
            </p>
            <ul className="space-y-2 mb-4">
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Email to your registered address</span>
              </li>
              <li className="flex items-start gap-3">
                <svg className="w-5 h-5 text-sage-400 mt-0.5 flex-shrink-0" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                </svg>
                <span className="font-sans text-oatmeal-400">Notice on the Paciolus platform</span>
              </li>
            </ul>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              You will have 30 days to review changes before they take effect. Continued use of Paciolus after the effective date constitutes acceptance of the modified Terms.
            </p>
          </section>

          {/* Section 15: General Provisions */}
          <section id="section-15">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              15. General Provisions
            </h2>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              15.1 Severability
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              If any provision of these Terms is found to be invalid or unenforceable, the remaining provisions will remain in full force and effect.
            </p>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              15.2 Waiver
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              Our failure to enforce any right or provision of these Terms will not constitute a waiver of that right or provision.
            </p>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              15.3 Entire Agreement
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              These Terms, together with our Privacy Policy, constitute the entire agreement between you and Paciolus regarding the service.
            </p>

            <h3 className="font-serif text-xl text-oatmeal-200 mb-3">
              15.4 Assignment
            </h3>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              You may not assign or transfer these Terms or your account without our written consent. We may assign these Terms at any time.
            </p>
          </section>

          {/* Section 16: Contact Information */}
          <section id="section-16">
            <h2 className="font-serif text-2xl text-oatmeal-100 mb-4 pt-8">
              16. Contact Information
            </h2>
            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              For questions or concerns about these Terms, please contact us:
            </p>
            <div className="bg-obsidian-800 border border-obsidian-700 rounded-lg p-6 mb-12">
              <div className="space-y-3">
                <div>
                  <p className="font-sans text-oatmeal-300 font-semibold mb-1">Legal Inquiries:</p>
                  <Link href="mailto:legal@paciolus.com" className="text-sage-400 hover:text-sage-300 underline font-sans">
                    legal@paciolus.com
                  </Link>
                </div>
                <div>
                  <p className="font-sans text-oatmeal-300 font-semibold mb-1">Privacy Matters:</p>
                  <Link href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline font-sans">
                    privacy@paciolus.com
                  </Link>
                </div>
                <div>
                  <p className="font-sans text-oatmeal-300 font-semibold mb-1">General Support:</p>
                  <Link href="mailto:support@paciolus.com" className="text-sage-400 hover:text-sage-300 underline font-sans">
                    support@paciolus.com
                  </Link>
                </div>
              </div>
            </div>
          </section>
        </Reveal>
      </main>

    </div>
  )
}
