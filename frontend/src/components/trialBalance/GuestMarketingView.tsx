'use client'

import { useState } from 'react'
import { motion } from 'framer-motion'
import { FeaturePillars, ProcessTimeline, DemoZone } from '@/components/marketing'
import type { UploadStatus } from '@/types/shared'
import { apiPost } from '@/utils/apiClient'

export function GuestMarketingView() {
  const [email, setEmail] = useState('')
  const [status, setStatus] = useState<UploadStatus>('idle')
  const [message, setMessage] = useState('')

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setStatus('loading')

    try {
      const response = await apiPost<{ message: string }>('/waitlist', null, { email })

      if (response.ok && response.data) {
        setStatus('success')
        setMessage(response.data.message)
        setEmail('')
      } else {
        setStatus('error')
        setMessage(response.error || 'Something went wrong. Please try again.')
      }
    } catch (error) {
      setStatus('error')
      setMessage('Unable to connect. Please try again later.')
    }
  }

  return (
    <>
      {/* Hero Section with Staggered Animations */}
      <section className="pt-32 pb-20 px-6">
        <motion.div
          className="max-w-4xl mx-auto text-center"
          initial="hidden"
          animate="visible"
          variants={{
            hidden: { opacity: 0 },
            visible: {
              opacity: 1,
              transition: { staggerChildren: 0.15, delayChildren: 0.1 }
            }
          }}
        >
          {/* Badge */}
          <motion.div
            className="inline-flex items-center gap-2 bg-sage-50 border border-sage-200 rounded-full px-4 py-1.5 mb-8"
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
            }}
          >
            <span className="w-2 h-2 bg-sage-500 rounded-full animate-pulse"></span>
            <span className="text-sage-700 text-sm font-sans font-medium tracking-wide">Zero-Storage Processing</span>
          </motion.div>

          {/* Main Headline */}
          <motion.h1
            className="text-5xl md:text-6xl lg:text-8xl font-serif font-bold text-content-primary mb-6 leading-[0.95] tracking-tight"
            variants={{
              hidden: { opacity: 0, y: 30 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.6, ease: 'easeOut' as const } }
            }}
          >
            Surgical Precision
            <span className="block text-sage-600 mt-2">for Trial Balance Diagnostics</span>
          </motion.h1>

          {/* Sub-headline */}
          <motion.p
            className="text-xl md:text-2xl text-content-secondary font-sans mb-10 max-w-3xl mx-auto leading-relaxed"
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
            }}
          >
            Financial Professionals: Eliminate sign errors and misclassifications with automated
            <span className="text-content-primary font-semibold"> Close Health Reports</span>.
          </motion.p>

          {/* 3-Step Workflow */}
          <motion.div
            className="flex flex-col md:flex-row items-center justify-center gap-4 md:gap-8 mb-12"
            variants={{
              hidden: { opacity: 0 },
              visible: {
                opacity: 1,
                transition: { staggerChildren: 0.1, delayChildren: 0.2 }
              }
            }}
          >
            {[
              { step: '1', label: 'Upload' },
              { step: '2', label: 'Map' },
              { step: '3', label: 'Export' }
            ].map((item, index) => (
              <motion.div
                key={item.step}
                className="flex items-center gap-3"
                variants={{
                  hidden: { opacity: 0, scale: 0.8 },
                  visible: { opacity: 1, scale: 1, transition: { duration: 0.4 } }
                }}
              >
                {index > 0 && (
                  <svg className="w-6 h-6 text-content-tertiary hidden md:block mr-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                  </svg>
                )}
                <div className="w-12 h-12 rounded-full bg-sage-50 border border-sage-200 flex items-center justify-center">
                  <span className="text-sage-600 font-bold font-mono text-lg">{item.step}</span>
                </div>
                <span className="text-content-primary font-sans font-medium text-lg">{item.label}</span>
              </motion.div>
            ))}
          </motion.div>

          {/* Waitlist Form */}
          <motion.form
            onSubmit={handleSubmit}
            className="max-w-md mx-auto"
            variants={{
              hidden: { opacity: 0, y: 20 },
              visible: { opacity: 1, y: 0, transition: { duration: 0.5 } }
            }}
          >
            <div className="flex flex-col sm:flex-row gap-3">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="Enter your work email"
                required
                className="input flex-1"
              />
              <button
                type="submit"
                disabled={status === 'loading'}
                className="btn-primary disabled:opacity-50 disabled:cursor-not-allowed shadow-lg shadow-sage-500/30"
              >
                {status === 'loading' ? 'Joining...' : 'Join Waitlist'}
              </button>
            </div>

            {status === 'success' && (
              <p className="mt-4 text-sage-600 font-sans font-medium">{message}</p>
            )}
            {status === 'error' && (
              <p className="mt-4 text-clay-600 font-sans font-medium" role="alert">{message}</p>
            )}
          </motion.form>

          <motion.p
            className="mt-6 text-content-tertiary text-sm font-sans"
            variants={{
              hidden: { opacity: 0 },
              visible: { opacity: 1, transition: { duration: 0.5, delay: 0.2 } }
            }}
          >
            Your data never leaves your browser&apos;s memory. Zero storage, zero risk.
          </motion.p>
        </motion.div>
      </section>

      <FeaturePillars />
      <ProcessTimeline />
      <DemoZone />

      {/* CTA Section */}
      <section className="py-20 px-6">
        <div className="max-w-3xl mx-auto text-center bg-sage-50 border border-sage-200 rounded-3xl p-12">
          <h2 className="text-3xl font-serif font-bold text-content-primary mb-4">
            Ready to streamline your close process?
          </h2>
          <p className="text-content-secondary font-sans mb-8">
            Join the waitlist and be the first to know when we launch.
          </p>
          <a
            href="#"
            onClick={(e) => {
              e.preventDefault()
              window.scrollTo({ top: 0, behavior: 'smooth' })
            }}
            className="btn-primary inline-block"
          >
            Get Early Access
          </a>
        </div>
      </section>

      {/* Footer with Maker's Mark */}
      <footer className="py-12 px-6 border-t border-theme relative overflow-hidden">
        <div className="absolute inset-0 opacity-[0.02]">
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-[20rem] font-serif text-content-primary select-none pointer-events-none">
            P
          </div>
        </div>

        <div className="max-w-6xl mx-auto relative">
          <div className="flex flex-col md:flex-row justify-between items-center gap-6 mb-8">
            <div className="text-content-tertiary text-sm font-sans">
              © 2025 Paciolus. Built for Financial Professionals.
            </div>
            <div className="text-content-tertiary text-sm font-sans">
              Zero-Storage Architecture. Your data stays yours.
            </div>
          </div>

          <div className="text-center pt-6 border-t border-theme">
            <p className="makers-mark mb-2">
              In the tradition of Luca Pacioli
            </p>
            <p className="text-content-tertiary text-xs font-mono tracking-wider">
              Assets = Liabilities + Equity
            </p>
          </div>
        </div>
      </footer>
    </>
  )
}
