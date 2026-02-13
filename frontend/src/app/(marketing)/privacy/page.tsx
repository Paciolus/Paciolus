'use client'

import { motion } from 'framer-motion'
import Link from 'next/link'

export default function PrivacyPolicy() {
  return (
    <div className="min-h-screen bg-gradient-obsidian">
      {/* Hero Section */}
      <motion.section
        className="relative pt-32 pb-16 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-4xl mx-auto">
          <h1 className="font-serif text-5xl text-oatmeal-100 mb-4">
            Privacy Policy
          </h1>
          <p className="font-sans text-lg text-oatmeal-400 mb-8">
            Effective Date: February 4, 2026
          </p>

          {/* Commitment Bullets */}
          <div className="grid md:grid-cols-2 gap-4 mb-12">
            {[
              'We never store your financial data',
              'We collect only what\u0027s necessary',
              'We never sell your personal information',
              'You control your data and can delete it anytime'
            ].map((commitment, idx) => (
              <div key={idx} className="flex items-start gap-3 bg-sage-500/10 border border-sage-500/20 rounded-lg p-4">
                <svg className="w-6 h-6 text-sage-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
                <p className="font-sans text-oatmeal-200">{commitment}</p>
              </div>
            ))}
          </div>
        </div>
      </motion.section>

      {/* Main Content */}
      <section className="relative pb-24 px-6">
        <div className="max-w-4xl mx-auto">
          {/* Table of Contents */}
          <nav className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 mb-12 sticky top-24 z-10">
            <h2 className="font-serif text-xl text-oatmeal-100 mb-4">Table of Contents</h2>
            <ol className="space-y-2 font-sans text-sm">
              {[
                'Information We Collect',
                'How We Use Your Information',
                'Zero-Storage Architecture',
                'Information We Share',
                'Your Rights and Choices',
                'Data Security',
                'International Data Transfers',
                'Children\u0027s Privacy',
                'Changes to This Policy',
                'Contact Us',
                'GDPR-Specific Information',
                'CCPA-Specific Information'
              ].map((section, idx) => (
                <li key={idx}>
                  <a
                    href={`#section-${idx + 1}`}
                    className="text-sage-400 hover:text-sage-300 underline"
                  >
                    {idx + 1}. {section}
                  </a>
                </li>
              ))}
            </ol>
          </nav>

          {/* Section 1: Information We Collect */}
          <article className="mb-12">
            <h2 id="section-1" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              1. Information We Collect
            </h2>

            {/* 1.1 Information You Provide Directly */}
            <h3 className="font-serif text-xl text-oatmeal-200 mb-4">
              1.1 Information You Provide Directly
            </h3>
            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Category</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Examples</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Purpose</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Account Registration</td>
                  <td className="p-4 font-sans text-oatmeal-400">Name, email address, password</td>
                  <td className="p-4 font-sans text-oatmeal-400">Account creation, authentication</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Client Metadata</td>
                  <td className="p-4 font-sans text-oatmeal-400">Client name, industry, fiscal year-end</td>
                  <td className="p-4 font-sans text-oatmeal-400">Client management, benchmark selection</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Support Requests</td>
                  <td className="p-4 font-sans text-oatmeal-400">Issue description, contact info</td>
                  <td className="p-4 font-sans text-oatmeal-400">Customer support, troubleshooting</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Payment Information</td>
                  <td className="p-4 font-sans text-oatmeal-400">Billing address (processed by Stripe)</td>
                  <td className="p-4 font-sans text-oatmeal-400">Subscription management</td>
                </tr>
              </tbody>
            </table>

            {/* 1.2 Information We Collect Automatically */}
            <h3 className="font-serif text-xl text-oatmeal-200 mb-4">
              1.2 Information We Collect Automatically
            </h3>
            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Category</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Examples</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Purpose</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Usage Data</td>
                  <td className="p-4 font-sans text-oatmeal-400">Feature usage counts, session duration</td>
                  <td className="p-4 font-sans text-oatmeal-400">Analytics, product improvement</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Device Information</td>
                  <td className="p-4 font-sans text-oatmeal-400">Browser type, OS, screen resolution</td>
                  <td className="p-4 font-sans text-oatmeal-400">Compatibility, performance optimization</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Cookies</td>
                  <td className="p-4 font-sans text-oatmeal-400">Session token, preferences</td>
                  <td className="p-4 font-sans text-oatmeal-400">Authentication, user experience</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Log Data</td>
                  <td className="p-4 font-sans text-oatmeal-400">IP address, timestamps, error logs</td>
                  <td className="p-4 font-sans text-oatmeal-400">Security, debugging, fraud prevention</td>
                </tr>
              </tbody>
            </table>

            {/* 1.3 Information We DO NOT Collect */}
            <h3 className="font-serif text-xl text-oatmeal-200 mb-4">
              1.3 Information We DO NOT Collect
            </h3>
            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-6 rounded-r-lg mb-6">
              <p className="font-sans text-oatmeal-300 mb-4">
                <strong className="text-oatmeal-100">Critical Distinction:</strong> We do NOT store financial data uploaded to our platform.
              </p>
              <table className="w-full border-collapse">
                <thead>
                  <tr className="bg-obsidian-900 border-b border-obsidian-700">
                    <th className="text-left p-3 font-serif text-oatmeal-100">Category</th>
                    <th className="text-left p-3 font-serif text-oatmeal-100">Examples</th>
                    <th className="text-center p-3 font-serif text-oatmeal-100">Stored?</th>
                  </tr>
                </thead>
                <tbody>
                  <tr className="border-b border-obsidian-700">
                    <td className="p-3 font-sans text-oatmeal-300">Trial Balance Data</td>
                    <td className="p-3 font-sans text-oatmeal-400">Account names, balances, classifications</td>
                    <td className="p-3 text-center">
                      <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="bg-obsidian-900/50 border-b border-obsidian-700">
                    <td className="p-3 font-sans text-oatmeal-300">Account Balances</td>
                    <td className="p-3 font-sans text-oatmeal-400">Dollar amounts, percentages, ratios</td>
                    <td className="p-3 text-center">
                      <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="border-b border-obsidian-700">
                    <td className="p-3 font-sans text-oatmeal-300">Transaction Details</td>
                    <td className="p-3 font-sans text-oatmeal-400">Journal entries, invoices, payments</td>
                    <td className="p-3 text-center">
                      <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="bg-obsidian-900/50 border-b border-obsidian-700">
                    <td className="p-3 font-sans text-oatmeal-300">Uploaded Files</td>
                    <td className="p-3 font-sans text-oatmeal-400">CSV/Excel files, bank statements</td>
                    <td className="p-3 text-center">
                      <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                  </tr>
                  <tr className="border-b border-obsidian-700">
                    <td className="p-3 font-sans text-oatmeal-300">Anomaly Details</td>
                    <td className="p-3 font-sans text-oatmeal-400">Specific flagged accounts, amounts</td>
                    <td className="p-3 text-center">
                      <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </article>

          {/* Section 2: How We Use Your Information */}
          <article className="mb-12">
            <h2 id="section-2" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              2. How We Use Your Information
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              We use the information we collect for the following purposes:
            </p>

            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Purpose</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Description</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Provide Service</td>
                  <td className="p-4 font-sans text-oatmeal-400">Process uploaded files, run analytics, generate reports</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Account Management</td>
                  <td className="p-4 font-sans text-oatmeal-400">Maintain user accounts, handle authentication</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Security</td>
                  <td className="p-4 font-sans text-oatmeal-400">Detect fraud, prevent abuse, enforce terms of service</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Analytics</td>
                  <td className="p-4 font-sans text-oatmeal-400">Improve product features, understand usage patterns</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Support</td>
                  <td className="p-4 font-sans text-oatmeal-400">Respond to inquiries, troubleshoot issues</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Legal Compliance</td>
                  <td className="p-4 font-sans text-oatmeal-400">Comply with laws, regulations, legal processes</td>
                </tr>
              </tbody>
            </table>

            <div className="bg-sage-500/10 border-l-4 border-sage-500 p-6 rounded-r-lg mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Aggregate Statistics</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-3">
                We may store anonymized, aggregated statistics such as:
              </p>
              <ul className="list-disc list-inside space-y-2 font-sans text-oatmeal-400">
                <li>"12 users uploaded trial balances in January 2026"</li>
                <li>"Average session duration: 18 minutes"</li>
                <li>"Journal Entry Testing used 347 times this month"</li>
              </ul>
              <p className="font-sans text-oatmeal-300 leading-relaxed mt-3">
                These statistics cannot be used to identify you or reconstruct your financial data.
              </p>
            </div>

            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-6 rounded-r-lg mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">We Do NOT:</h4>
              <ul className="space-y-2 font-sans text-oatmeal-300">
                {[
                  'Sell your personal information to third parties',
                  'Use your financial data for advertising or marketing',
                  'Share your data with data brokers or affiliates',
                  'Train AI models on your uploaded financial data'
                ].map((item, idx) => (
                  <li key={idx} className="flex items-start gap-3">
                    <svg className="w-5 h-5 text-clay-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          </article>

          {/* Section 3: Zero-Storage Architecture */}
          <article className="mb-12">
            <h2 id="section-3" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              3. Zero-Storage Architecture
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              Paciolus is built on a <strong className="text-oatmeal-200">Zero-Storage architecture</strong> for financial data. This is our core privacy commitment.
            </p>

            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-4">How It Works</h4>
              <ol className="space-y-4 font-sans text-oatmeal-300">
                <li className="flex gap-3">
                  <span className="font-mono text-sage-400 flex-shrink-0">1.</span>
                  <span>You upload a trial balance, journal entry file, or other financial document</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-mono text-sage-400 flex-shrink-0">2.</span>
                  <span>Our server reads the file into ephemeral memory (RAM only)</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-mono text-sage-400 flex-shrink-0">3.</span>
                  <span>We run analytics, detect anomalies, and generate reports</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-mono text-sage-400 flex-shrink-0">4.</span>
                  <span>Results are streamed back to your browser in real-time</span>
                </li>
                <li className="flex gap-3">
                  <span className="font-mono text-sage-400 flex-shrink-0">5.</span>
                  <span className="text-sage-300 font-medium">All data is immediately destroyed when the response completes (typically &lt;5 seconds)</span>
                </li>
              </ol>
            </div>

            <div className="grid md:grid-cols-3 gap-4 mb-6">
              <div className="bg-sage-500/10 border border-sage-500/20 rounded-lg p-4">
                <h5 className="font-serif text-oatmeal-100 mb-2">Security</h5>
                <p className="font-sans text-sm text-oatmeal-400">No database to breach, no files to leak</p>
              </div>
              <div className="bg-sage-500/10 border border-sage-500/20 rounded-lg p-4">
                <h5 className="font-serif text-oatmeal-100 mb-2">Privacy</h5>
                <p className="font-sans text-sm text-oatmeal-400">Zero retention = zero risk of unauthorized access</p>
              </div>
              <div className="bg-sage-500/10 border border-sage-500/20 rounded-lg p-4">
                <h5 className="font-serif text-oatmeal-100 mb-2">Compliance</h5>
                <p className="font-sans text-sm text-oatmeal-400">Simplifies GDPR/CCPA — no PI to delete</p>
              </div>
            </div>

            <p className="font-sans text-oatmeal-400 leading-relaxed">
              <strong className="text-oatmeal-200">Technical Details:</strong> Uploaded files exist in server memory for the duration of the HTTP request only. We do not write to disk, cache layers, or persistent storage. PDF/Excel exports are generated on-the-fly and streamed directly to your browser.
            </p>
          </article>

          {/* Section 4: Information We Share */}
          <article className="mb-12">
            <h2 id="section-4" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              4. Information We Share
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              We share limited personal information with the following third-party service providers:
            </p>

            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Provider</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Service</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Data Shared</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Vercel</td>
                  <td className="p-4 font-sans text-oatmeal-400">Frontend hosting</td>
                  <td className="p-4 font-sans text-oatmeal-400">IP address, browser info, access logs</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Render</td>
                  <td className="p-4 font-sans text-oatmeal-400">Backend hosting</td>
                  <td className="p-4 font-sans text-oatmeal-400">API request logs, error traces</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">PostgreSQL (Render)</td>
                  <td className="p-4 font-sans text-oatmeal-400">Metadata storage</td>
                  <td className="p-4 font-sans text-oatmeal-400">User accounts, client metadata</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Stripe</td>
                  <td className="p-4 font-sans text-oatmeal-400">Payment processing</td>
                  <td className="p-4 font-sans text-oatmeal-400">Email, billing address, payment method</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Sentry</td>
                  <td className="p-4 font-sans text-oatmeal-400">Error monitoring</td>
                  <td className="p-4 font-sans text-oatmeal-400">Error logs, stack traces, user ID (anonymized)</td>
                </tr>
              </tbody>
            </table>

            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-6 rounded-r-lg mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Legal Requirements</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-3">
                We may disclose personal information if required to do so by law or in response to:
              </p>
              <ul className="list-disc list-inside space-y-2 font-sans text-oatmeal-400">
                <li>Valid court orders or subpoenas</li>
                <li>Government investigations</li>
                <li>Requests from law enforcement agencies</li>
              </ul>
            </div>

            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Business Transfers</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                In the event of a merger, acquisition, or sale of assets, your personal information may be transferred to the acquiring entity. We will notify you via email at least 30 days before any such transfer.
              </p>
            </div>
          </article>

          {/* Section 5: Your Rights and Choices */}
          <article className="mb-12">
            <h2 id="section-5" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              5. Your Rights and Choices
            </h2>

            <div className="space-y-6">
              {/* Access and Portability */}
              <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
                <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Access and Portability</h4>
                <p className="font-sans text-oatmeal-300 leading-relaxed mb-2">
                  <strong className="text-oatmeal-200">Right:</strong> GDPR Article 15, CCPA § 1798.100
                </p>
                <p className="font-sans text-oatmeal-400 leading-relaxed">
                  You can request a copy of all personal information we hold about you. We will provide it in a machine-readable format (JSON) within 30 days.
                </p>
              </div>

              {/* Correction */}
              <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
                <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Correction</h4>
                <p className="font-sans text-oatmeal-300 leading-relaxed mb-2">
                  <strong className="text-oatmeal-200">Right:</strong> GDPR Article 16
                </p>
                <p className="font-sans text-oatmeal-400 leading-relaxed">
                  You can update your account information (name, email, practice settings) at any time via the Settings page. For corrections requiring verification, contact <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">privacy@paciolus.com</a>.
                </p>
              </div>

              {/* Deletion */}
              <div className="bg-clay-500/10 border border-clay-500/30 rounded-lg p-6">
                <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Deletion ("Right to be Forgotten")</h4>
                <p className="font-sans text-oatmeal-300 leading-relaxed mb-2">
                  <strong className="text-oatmeal-200">Right:</strong> GDPR Article 17, CCPA § 1798.105
                </p>
                <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
                  You can delete your account and all associated data at any time. Deletion is <strong className="text-oatmeal-200">immediate and irreversible</strong>.
                </p>
                <div className="bg-obsidian-900 border border-obsidian-700 rounded-lg p-4">
                  <p className="font-sans text-sm text-oatmeal-400 mb-2">What gets deleted:</p>
                  <ul className="list-disc list-inside space-y-1 font-sans text-sm text-oatmeal-400">
                    <li>User account record (email, password hash, profile)</li>
                    <li>Client metadata (names, industries, fiscal year-ends)</li>
                    <li>Engagement records (diagnostic workspace data)</li>
                    <li>Follow-up items (issue narratives)</li>
                  </ul>
                  <p className="font-sans text-sm text-oatmeal-300 mt-4">
                    <strong>Note:</strong> Financial data uploaded during active sessions is already deleted per our Zero-Storage architecture.
                  </p>
                </div>
              </div>

              {/* Objection and Restriction */}
              <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
                <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Objection and Restriction</h4>
                <p className="font-sans text-oatmeal-300 leading-relaxed mb-2">
                  <strong className="text-oatmeal-200">Right:</strong> GDPR Articles 18, 21
                </p>
                <p className="font-sans text-oatmeal-400 leading-relaxed">
                  You can object to specific processing activities or request temporary restriction. Contact <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">privacy@paciolus.com</a> to exercise this right.
                </p>
              </div>

              {/* Do Not Sell */}
              <div className="bg-sage-500/10 border border-sage-500/30 rounded-lg p-6">
                <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Do Not Sell My Personal Information</h4>
                <p className="font-sans text-oatmeal-300 leading-relaxed mb-2">
                  <strong className="text-oatmeal-200">Right:</strong> CCPA § 1798.120
                </p>
                <p className="font-sans text-oatmeal-400 leading-relaxed">
                  <strong className="text-sage-300">We do not sell personal information.</strong> We have never sold user data and never will. No opt-out mechanism is necessary because sale never occurs.
                </p>
              </div>
            </div>
          </article>

          {/* Section 6: Data Security */}
          <article className="mb-12">
            <h2 id="section-6" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              6. Data Security
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              We implement industry-standard security measures to protect your personal information:
            </p>

            <div className="grid md:grid-cols-2 gap-4 mb-6">
              {[
                { label: 'TLS 1.3 Encryption', desc: 'All data in transit is encrypted end-to-end' },
                { label: 'bcrypt Password Hashing', desc: 'Passwords salted and hashed with 12 rounds' },
                { label: 'JWT Authentication', desc: 'Stateless token-based session management' },
                { label: 'Multi-Tenant Isolation', desc: 'User data segregated at database level' },
                { label: 'Zero-Storage for Financial Data', desc: 'No persistent storage = no data breach risk' },
                { label: 'Rate Limiting', desc: 'Protection against brute-force attacks' }
              ].map((item, idx) => (
                <div key={idx} className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-4">
                  <h5 className="font-serif text-oatmeal-100 mb-2">{item.label}</h5>
                  <p className="font-sans text-sm text-oatmeal-400">{item.desc}</p>
                </div>
              ))}
            </div>

            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-6 rounded-r-lg">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Breach Notification</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                In the unlikely event of a data breach affecting personal information, we will:
              </p>
              <ul className="list-decimal list-inside space-y-2 font-sans text-oatmeal-400 mt-3">
                <li>Notify affected users via email within <strong className="text-oatmeal-200">72 hours</strong></li>
                <li>Report to relevant supervisory authorities (EU DPA, California AG)</li>
                <li>Provide details on the nature of the breach and mitigation steps</li>
              </ul>
            </div>
          </article>

          {/* Section 7: International Data Transfers */}
          <article className="mb-12">
            <h2 id="section-7" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              7. International Data Transfers
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              Paciolus operates globally. Your personal information may be transferred to and processed in the following jurisdictions:
            </p>

            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Service</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Data Location</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Safeguards</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Frontend (Vercel)</td>
                  <td className="p-4 font-sans text-oatmeal-400">United States (Virginia)</td>
                  <td className="p-4 font-sans text-oatmeal-400">Standard Contractual Clauses (SCCs)</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Backend (Render)</td>
                  <td className="p-4 font-sans text-oatmeal-400">United States (Oregon)</td>
                  <td className="p-4 font-sans text-oatmeal-400">Standard Contractual Clauses (SCCs)</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Database (PostgreSQL)</td>
                  <td className="p-4 font-sans text-oatmeal-400">United States (Oregon)</td>
                  <td className="p-4 font-sans text-oatmeal-400">Encryption at rest, TLS in transit</td>
                </tr>
              </tbody>
            </table>

            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">EEA Users</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                For users in the European Economic Area (EEA), we rely on <strong className="text-oatmeal-100">Standard Contractual Clauses (SCCs)</strong> approved by the European Commission for international data transfers. These clauses ensure your data receives equivalent protection as required under GDPR.
              </p>
            </div>
          </article>

          {/* Section 8: Children's Privacy */}
          <article className="mb-12">
            <h2 id="section-8" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              8. Children's Privacy
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              Paciolus is a professional financial platform intended for use by licensed accountants, auditors, and financial professionals. Our services are <strong className="text-oatmeal-200">not directed to individuals under the age of 16</strong>.
            </p>

            <div className="bg-clay-500/10 border-l-4 border-clay-500 p-6 rounded-r-lg">
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                We do not knowingly collect personal information from children under 16. If you believe we have inadvertently collected such information, contact <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">privacy@paciolus.com</a> immediately, and we will delete it within 48 hours.
              </p>
            </div>
          </article>

          {/* Section 9: Changes to This Policy */}
          <article className="mb-12">
            <h2 id="section-9" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              9. Changes to This Policy
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-4">
              We may update this Privacy Policy from time to time to reflect changes in our practices, legal requirements, or service offerings.
            </p>

            <div className="bg-sage-500/10 border-l-4 border-sage-500 p-6 rounded-r-lg mb-4">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Material Changes</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                For material changes (e.g., new data sharing practices, changes to your rights), we will:
              </p>
              <ul className="list-decimal list-inside space-y-2 font-sans text-oatmeal-400 mt-3">
                <li>Email you at least <strong className="text-oatmeal-200">30 days in advance</strong></li>
                <li>Display a prominent notice on the platform</li>
                <li>Update the "Effective Date" at the top of this document</li>
              </ul>
            </div>

            <p className="font-sans text-oatmeal-400 leading-relaxed">
              <strong className="text-oatmeal-200">Non-Material Changes:</strong> Minor updates (e.g., clarifications, typo fixes, contact email changes) will be posted immediately with an updated "Effective Date."
            </p>
          </article>

          {/* Section 10: Contact Us */}
          <article className="mb-12">
            <h2 id="section-10" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              10. Contact Us
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              For privacy-related inquiries, data requests, or security concerns, contact us at:
            </p>

            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Request Type</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Contact</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">General Privacy Questions</td>
                  <td className="p-4 font-sans text-oatmeal-400">
                    <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">
                      privacy@paciolus.com
                    </a>
                  </td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Data Access Requests</td>
                  <td className="p-4 font-sans text-oatmeal-400">
                    <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">
                      privacy@paciolus.com
                    </a>
                  </td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Data Deletion Requests</td>
                  <td className="p-4 font-sans text-oatmeal-400">
                    <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">
                      privacy@paciolus.com
                    </a>
                  </td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">GDPR/CCPA Compliance</td>
                  <td className="p-4 font-sans text-oatmeal-400">
                    <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">
                      privacy@paciolus.com
                    </a>
                  </td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Security Incidents / Breach Notifications</td>
                  <td className="p-4 font-sans text-oatmeal-400">
                    <a href="mailto:security@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">
                      security@paciolus.com
                    </a>
                  </td>
                </tr>
              </tbody>
            </table>

            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Response Time</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                We aim to respond to all privacy inquiries within <strong className="text-oatmeal-100">5 business days</strong>. Data access requests will be fulfilled within <strong className="text-oatmeal-100">30 days</strong> as required by GDPR Article 15.
              </p>
            </div>
          </article>

          {/* Section 11: GDPR-Specific Information */}
          <article className="mb-12">
            <h2 id="section-11" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              11. GDPR-Specific Information
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              For users in the European Economic Area (EEA), the following additional information applies:
            </p>

            {/* Data Controller */}
            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Data Controller</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                Paciolus LLC is the data controller responsible for your personal information under GDPR.
              </p>
            </div>

            {/* Lawful Basis */}
            <h4 className="font-serif text-xl text-oatmeal-200 mb-4">Lawful Basis for Processing</h4>
            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Processing Activity</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Lawful Basis (GDPR Article 6)</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Account creation and authentication</td>
                  <td className="p-4 font-sans text-oatmeal-400">Contract (Article 6(1)(b)) — necessary to provide service</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Payment processing</td>
                  <td className="p-4 font-sans text-oatmeal-400">Contract (Article 6(1)(b)) — necessary to fulfill subscription</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Security monitoring and fraud prevention</td>
                  <td className="p-4 font-sans text-oatmeal-400">Legitimate Interests (Article 6(1)(f)) — protect platform integrity</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Product analytics and improvement</td>
                  <td className="p-4 font-sans text-oatmeal-400">Legitimate Interests (Article 6(1)(f)) — improve user experience</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Legal compliance and law enforcement</td>
                  <td className="p-4 font-sans text-oatmeal-400">Legal Obligation (Article 6(1)(c))</td>
                </tr>
              </tbody>
            </table>

            {/* DPO */}
            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Data Protection Officer (DPO)</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                You can contact our Data Protection Officer at <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">privacy@paciolus.com</a> for GDPR-related inquiries.
              </p>
            </div>

            {/* Supervisory Authority */}
            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Supervisory Authority</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed">
                If you are located in the EEA, you have the right to lodge a complaint with your local supervisory authority if you believe we have violated your data protection rights.
              </p>
            </div>
          </article>

          {/* Section 12: CCPA-Specific Information */}
          <article className="mb-12">
            <h2 id="section-12" className="font-serif text-3xl text-oatmeal-100 mb-6 pt-8">
              12. CCPA-Specific Information
            </h2>

            <p className="font-sans text-oatmeal-400 leading-relaxed mb-6">
              For California residents, the following additional information applies under the California Consumer Privacy Act (CCPA):
            </p>

            {/* Categories of PI */}
            <h4 className="font-serif text-xl text-oatmeal-200 mb-4">Categories of Personal Information Collected</h4>
            <table className="w-full border-collapse mb-6">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Category</th>
                  <th className="text-left p-4 font-serif text-oatmeal-100">Examples</th>
                  <th className="text-center p-4 font-serif text-oatmeal-100">Collected?</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Identifiers</td>
                  <td className="p-4 font-sans text-oatmeal-400">Name, email, IP address, unique ID</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Commercial Information</td>
                  <td className="p-4 font-sans text-oatmeal-400">Subscription tier, payment history</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Internet/Network Activity</td>
                  <td className="p-4 font-sans text-oatmeal-400">Browser type, device info, usage data</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Professional Information</td>
                  <td className="p-4 font-sans text-oatmeal-400">Practice name, client metadata</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Sensitive Personal Information</td>
                  <td className="p-4 font-sans text-oatmeal-400">Account credentials (password hash)</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Geolocation Data</td>
                  <td className="p-4 font-sans text-oatmeal-400">Precise GPS coordinates</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Biometric Information</td>
                  <td className="p-4 font-sans text-oatmeal-400">Fingerprints, facial recognition</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                </tr>
              </tbody>
            </table>

            {/* Business Purposes */}
            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6 mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Business Purposes for Collection</h4>
              <ul className="list-disc list-inside space-y-2 font-sans text-oatmeal-300">
                <li>Providing and maintaining the service</li>
                <li>Processing transactions and payments</li>
                <li>Detecting security incidents and fraud</li>
                <li>Debugging and error resolution</li>
                <li>Internal analytics and product improvement</li>
              </ul>
            </div>

            {/* Sale of PI */}
            <div className="bg-sage-500/10 border-l-4 border-sage-500 p-6 rounded-r-lg mb-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Sale of Personal Information</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-2">
                <strong className="text-sage-300">We do NOT sell personal information.</strong>
              </p>
              <p className="font-sans text-oatmeal-400 leading-relaxed">
                Paciolus has not sold personal information in the past 12 months and does not share personal information with third parties for cross-context behavioral advertising.
              </p>
            </div>

            {/* California Rights */}
            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
              <h4 className="font-serif text-lg text-oatmeal-100 mb-3">Your California Privacy Rights</h4>
              <p className="font-sans text-oatmeal-300 leading-relaxed mb-3">
                California residents have the following rights under CCPA:
              </p>
              <ul className="list-disc list-inside space-y-2 font-sans text-oatmeal-400">
                <li><strong className="text-oatmeal-200">Right to Know:</strong> Request disclosure of PI collected, sources, purposes, and third parties</li>
                <li><strong className="text-oatmeal-200">Right to Delete:</strong> Request deletion of PI we hold about you</li>
                <li><strong className="text-oatmeal-200">Right to Opt-Out:</strong> Opt out of sale of PI (not applicable — we don't sell)</li>
                <li><strong className="text-oatmeal-200">Right to Non-Discrimination:</strong> We will not discriminate against you for exercising CCPA rights</li>
              </ul>
              <p className="font-sans text-oatmeal-300 leading-relaxed mt-4">
                To exercise these rights, contact <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">privacy@paciolus.com</a>.
              </p>
            </div>
          </article>

          {/* Summary Table */}
          <article className="mb-12">
            <h2 className="font-serif text-3xl text-oatmeal-100 mb-6">
              Summary: What We Collect vs. Store
            </h2>

            <table className="w-full border-collapse">
              <thead>
                <tr className="bg-obsidian-800 border-b border-obsidian-600">
                  <th className="text-left p-4 font-serif text-oatmeal-100">Data Type</th>
                  <th className="text-center p-4 font-serif text-oatmeal-100">Collected?</th>
                  <th className="text-center p-4 font-serif text-oatmeal-100">Stored?</th>
                  <th className="text-center p-4 font-serif text-oatmeal-100">Retention</th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Account Information (name, email)</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center font-sans text-oatmeal-400">Until account deletion</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Client Metadata (names, industries)</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center font-sans text-oatmeal-400">Until account deletion</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Usage Statistics (aggregated)</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center font-sans text-oatmeal-400">Indefinitely (anonymized)</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Trial Balance Data</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="p-4 text-center font-mono text-clay-300">&lt;5 seconds (ephemeral)</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Journal Entries / Invoices</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="p-4 text-center font-mono text-clay-300">&lt;5 seconds (ephemeral)</td>
                </tr>
                <tr className="bg-obsidian-800/50 border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Uploaded CSV/Excel Files</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="p-4 text-center font-mono text-clay-300">&lt;5 seconds (ephemeral)</td>
                </tr>
                <tr className="border-b border-obsidian-700">
                  <td className="p-4 font-sans text-oatmeal-300">Anomaly Details (amounts, accounts)</td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-sage-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  </td>
                  <td className="p-4 text-center">
                    <svg className="w-6 h-6 text-clay-400 mx-auto" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </td>
                  <td className="p-4 text-center font-mono text-clay-300">&lt;5 seconds (ephemeral)</td>
                </tr>
              </tbody>
            </table>
          </article>

          {/* Footer CTA */}
          <div className="bg-sage-500/10 border-l-4 border-sage-500 p-6 rounded-r-lg">
            <h3 className="font-serif text-xl text-oatmeal-100 mb-3">
              Questions About This Policy?
            </h3>
            <p className="font-sans text-oatmeal-300 leading-relaxed mb-4">
              We're committed to transparency and protecting your privacy. If you have questions or concerns about this Privacy Policy, contact us at <a href="mailto:privacy@paciolus.com" className="text-sage-400 hover:text-sage-300 underline">privacy@paciolus.com</a>.
            </p>
            <p className="font-sans text-sm text-oatmeal-400">
              Last updated: February 4, 2026
            </p>
          </div>
        </div>
      </section>

    </div>
  )
}
