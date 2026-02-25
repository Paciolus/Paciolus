'use client'

import { useState, Suspense } from 'react'
import { useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { apiPost } from '@/utils/apiClient'

const INQUIRY_TYPES = ['General', 'Walkthrough Request', 'Support', 'Enterprise'] as const

function ContactForm() {
  const searchParams = useSearchParams()
  const preselectedInquiry = searchParams.get('inquiry') || ''

  const [form, setForm] = useState({
    name: '',
    email: '',
    company: '',
    inquiry_type: INQUIRY_TYPES.includes(preselectedInquiry as typeof INQUIRY_TYPES[number])
      ? preselectedInquiry
      : '',
    message: '',
    honeypot: '',
  })
  const [errors, setErrors] = useState<Record<string, string>>({})
  const [submitting, setSubmitting] = useState(false)
  const [submitted, setSubmitted] = useState(false)
  const [submitError, setSubmitError] = useState('')

  function validate(): Record<string, string> {
    const errs: Record<string, string> = {}
    if (!form.name.trim()) errs.name = 'Name is required'
    if (!form.email.trim()) errs.email = 'Email is required'
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(form.email)) errs.email = 'Invalid email format'
    if (!form.inquiry_type) errs.inquiry_type = 'Please select an inquiry type'
    if (!form.message.trim()) errs.message = 'Message is required'
    else if (form.message.trim().length < 10) errs.message = 'Message must be at least 10 characters'
    return errs
  }

  function handleChange(e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) {
    const { name, value } = e.target
    setForm(prev => ({ ...prev, [name]: value }))
    if (errors[name]) setErrors(prev => { const next = { ...prev }; delete next[name]; return next })
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setSubmitError('')

    const validationErrors = validate()
    if (Object.keys(validationErrors).length > 0) {
      setErrors(validationErrors)
      return
    }

    setSubmitting(true)
    try {
      const res = await apiPost('/contact/submit', null, form as Record<string, unknown>)

      if (!res.ok) {
        throw new Error(res.error || 'Failed to send message')
      }

      setSubmitted(true)
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : 'Something went wrong. Please try again.')
    } finally {
      setSubmitting(false)
    }
  }

  if (submitted) {
    return (
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.4, ease: 'easeOut' as const }}
        className="bg-sage-500/10 border border-sage-500/30 rounded-lg p-8 text-center"
      >
        <svg className="w-16 h-16 text-sage-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <h3 className="font-serif text-2xl text-oatmeal-100 mb-2">Message Sent</h3>
        <p className="font-sans text-oatmeal-400">
          We&apos;ll respond within 1&ndash;2 business days.
        </p>
      </motion.div>
    )
  }

  const inputClasses = "w-full bg-obsidian-800 border border-obsidian-600 rounded-lg px-4 py-3 font-sans text-oatmeal-200 placeholder-oatmeal-600 focus:border-sage-500 focus:ring-1 focus:ring-sage-500/30 outline-none transition-colors"
  const labelClasses = "block font-sans text-sm text-oatmeal-300 mb-2"
  const errorClasses = "font-sans text-xs text-clay-400 mt-1"

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      {submitError && (
        <div className="bg-clay-500/10 border border-clay-500/30 rounded-lg p-4">
          <p className="font-sans text-sm text-clay-300">{submitError}</p>
        </div>
      )}

      {/* Honeypot — hidden from users, bots fill it */}
      <div className="absolute opacity-0 -z-10" aria-hidden="true">
        <label htmlFor="honeypot">Leave this empty</label>
        <input
          type="text"
          id="honeypot"
          name="honeypot"
          value={form.honeypot}
          onChange={handleChange}
          tabIndex={-1}
          autoComplete="off"
        />
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Name */}
        <div>
          <label htmlFor="name" className={labelClasses}>Name *</label>
          <input
            type="text"
            id="name"
            name="name"
            value={form.name}
            onChange={handleChange}
            className={inputClasses}
            placeholder="Your name"
          />
          {errors.name && <p className={errorClasses}>{errors.name}</p>}
        </div>

        {/* Email */}
        <div>
          <label htmlFor="email" className={labelClasses}>Email *</label>
          <input
            type="email"
            id="email"
            name="email"
            value={form.email}
            onChange={handleChange}
            className={inputClasses}
            placeholder="you@company.com"
          />
          {errors.email && <p className={errorClasses}>{errors.email}</p>}
        </div>
      </div>

      <div className="grid md:grid-cols-2 gap-6">
        {/* Company */}
        <div>
          <label htmlFor="company" className={labelClasses}>Company</label>
          <input
            type="text"
            id="company"
            name="company"
            value={form.company}
            onChange={handleChange}
            className={inputClasses}
            placeholder="Your firm or organization"
          />
        </div>

        {/* Inquiry Type */}
        <div>
          <label htmlFor="inquiry_type" className={labelClasses}>Inquiry Type *</label>
          <select
            id="inquiry_type"
            name="inquiry_type"
            value={form.inquiry_type}
            onChange={handleChange}
            className={inputClasses}
          >
            <option value="" disabled>Select inquiry type</option>
            {INQUIRY_TYPES.map(type => (
              <option key={type} value={type}>{type}</option>
            ))}
          </select>
          {errors.inquiry_type && <p className={errorClasses}>{errors.inquiry_type}</p>}
        </div>
      </div>

      {/* Message */}
      <div>
        <label htmlFor="message" className={labelClasses}>Message *</label>
        <textarea
          id="message"
          name="message"
          value={form.message}
          onChange={handleChange}
          rows={6}
          className={inputClasses + ' resize-none'}
          placeholder="Tell us how we can help..."
        />
        {errors.message && <p className={errorClasses}>{errors.message}</p>}
      </div>

      <button
        type="submit"
        disabled={submitting}
        className="w-full bg-sage-600 hover:bg-sage-500 text-oatmeal-100 font-sans font-medium py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
      >
        {submitting ? 'Sending...' : 'Send Message'}
      </button>
    </form>
  )
}

export default function ContactPage() {
  return (
    <div className="relative z-10 min-h-screen bg-gradient-obsidian">
      <motion.section
        className="relative pt-32 pb-24 px-6"
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, ease: 'easeOut' as const }}
      >
        <div className="max-w-2xl mx-auto">
          <h1 className="font-serif text-4xl md:text-5xl text-oatmeal-100 mb-4">
            Contact Us
          </h1>
          <p className="font-sans text-lg text-oatmeal-400 mb-10">
            Have questions about the platform? Need a walkthrough? We&apos;d love to hear from you.
          </p>

          <Suspense fallback={
            <div className="animate-pulse space-y-6">
              <div className="h-12 bg-obsidian-800 rounded-lg" />
              <div className="h-12 bg-obsidian-800 rounded-lg" />
              <div className="h-32 bg-obsidian-800 rounded-lg" />
            </div>
          }>
            <ContactForm />
          </Suspense>

          {/* Contact Info */}
          <div className="mt-12 grid md:grid-cols-2 gap-6">
            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
              <h3 className="font-serif text-lg text-oatmeal-100 mb-2">General Inquiries</h3>
              <a href="mailto:contact@paciolus.io" className="font-sans text-sage-400 hover:text-sage-300 underline">
                contact@paciolus.io
              </a>
            </div>
            <div className="bg-obsidian-800 border border-obsidian-600 rounded-lg p-6">
              <h3 className="font-serif text-lg text-oatmeal-100 mb-2">Response Time</h3>
              <p className="font-sans text-oatmeal-400">
                1&ndash;2 business days
              </p>
            </div>
          </div>
        </div>
      </motion.section>

    </div>
  )
}
