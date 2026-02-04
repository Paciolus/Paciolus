'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { ClientCreateInput, Industry, IndustryOption } from '@/types/client';
import { FISCAL_YEAR_END_OPTIONS } from '@/types/client';
import {
  getInputClasses,
  getSelectClasses,
  MODAL_OVERLAY_VARIANTS,
  MODAL_CONTENT_VARIANTS,
} from '@/utils';

/**
 * CreateClientModal - Sprint 17 Portfolio Dashboard Component
 *
 * Design: "Obsidian Vault" modal aesthetic with Tier 2 Form Validation
 * - Sage Green border shift for active/focused inputs
 * - Clay Red for validation errors
 * - Smooth enter/exit animations
 *
 * ZERO-STORAGE: Creates client metadata only, no financial data
 */

interface CreateClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: ClientCreateInput) => Promise<boolean>;
  industries: IndustryOption[];
  isLoading?: boolean;
}

interface FormErrors {
  name?: string;
  industry?: string;
  fiscal_year_end?: string;
}

export function CreateClientModal({
  isOpen,
  onClose,
  onSubmit,
  industries,
  isLoading = false,
}: CreateClientModalProps) {
  // Form state
  const [name, setName] = useState('');
  const [industry, setIndustry] = useState<Industry>('other');
  const [fiscalYearEnd, setFiscalYearEnd] = useState('12-31');
  const [errors, setErrors] = useState<FormErrors>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Ref for auto-focus
  const nameInputRef = useRef<HTMLInputElement>(null);

  // Reset form when modal opens
  useEffect(() => {
    if (isOpen) {
      setName('');
      setIndustry('other');
      setFiscalYearEnd('12-31');
      setErrors({});
      setTouched({});
      // Auto-focus name input after animation
      setTimeout(() => nameInputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  // Validate form
  const validate = (): boolean => {
    const newErrors: FormErrors = {};

    if (!name.trim()) {
      newErrors.name = 'Client name is required';
    } else if (name.trim().length < 2) {
      newErrors.name = 'Name must be at least 2 characters';
    } else if (name.trim().length > 255) {
      newErrors.name = 'Name must be less than 255 characters';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  // Handle blur for touched state
  const handleBlur = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
    validate();
  };

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Mark all fields as touched
    setTouched({ name: true, industry: true, fiscal_year_end: true });

    if (!validate()) return;

    setIsSubmitting(true);

    const success = await onSubmit({
      name: name.trim(),
      industry,
      fiscal_year_end: fiscalYearEnd,
    });

    setIsSubmitting(false);

    if (success) {
      onClose();
    }
  };

  // Helper to get input classes using shared utility
  const getFieldInputClasses = (field: keyof FormErrors, value: string) => {
    const isTouched = touched[field] ?? false;
    const hasError = !!(errors[field]);
    const hasValue = value.trim().length > 0;
    const disabled = isSubmitting || isLoading;
    return getInputClasses(isTouched, hasError, hasValue, disabled);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          className="fixed inset-0 z-50 flex items-center justify-center p-4"
          variants={MODAL_OVERLAY_VARIANTS}
          initial="hidden"
          animate="visible"
          exit="hidden"
        >
          {/* Backdrop */}
          <motion.div
            className="absolute inset-0 bg-obsidian-900/80 backdrop-blur-sm"
            onClick={onClose}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
          />

          {/* Modal */}
          <motion.div
            variants={MODAL_CONTENT_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative bg-obsidian-800 rounded-2xl border border-obsidian-600/50 shadow-2xl w-full max-w-md overflow-hidden"
          >
            {/* Header */}
            <div className="px-6 py-5 border-b border-obsidian-600/50">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-sage-500/10 border border-sage-500/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-serif font-semibold text-oatmeal-100">
                    New Client
                  </h2>
                  <p className="text-oatmeal-500 text-sm font-sans">
                    Add a client to your portfolio
                  </p>
                </div>
              </div>

              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
                aria-label="Close modal"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            {/* Form */}
            <form onSubmit={handleSubmit} className="p-6 space-y-5">
              {/* Client Name */}
              <div>
                <label htmlFor="client-name" className="block text-oatmeal-200 font-sans font-medium mb-2">
                  Client Name <span className="text-clay-400">*</span>
                </label>
                <input
                  ref={nameInputRef}
                  id="client-name"
                  type="text"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  onBlur={() => handleBlur('name')}
                  placeholder="e.g., Acme Corporation"
                  className={getFieldInputClasses('name', name)}
                  disabled={isSubmitting || isLoading}
                />
                {touched.name && errors.name && (
                  <motion.p
                    initial={{ opacity: 0, y: -5 }}
                    animate={{ opacity: 1, y: 0 }}
                    className="mt-2 text-sm text-clay-400 font-sans flex items-center gap-1.5"
                  >
                    <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
                    </svg>
                    {errors.name}
                  </motion.p>
                )}
              </div>

              {/* Industry */}
              <div>
                <label htmlFor="client-industry" className="block text-oatmeal-200 font-sans font-medium mb-2">
                  Industry
                </label>
                <div className="relative">
                  <select
                    id="client-industry"
                    value={industry}
                    onChange={(e) => setIndustry(e.target.value as Industry)}
                    className={getSelectClasses(isSubmitting || isLoading)}
                    disabled={isSubmitting || isLoading}
                  >
                    {industries.map((ind) => (
                      <option key={ind.value} value={ind.value}>
                        {ind.label}
                      </option>
                    ))}
                  </select>
                  {/* Dropdown arrow */}
                  <svg className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-oatmeal-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {/* Fiscal Year End */}
              <div>
                <label htmlFor="client-fye" className="block text-oatmeal-200 font-sans font-medium mb-2">
                  Fiscal Year End
                </label>
                <div className="relative">
                  <select
                    id="client-fye"
                    value={fiscalYearEnd}
                    onChange={(e) => setFiscalYearEnd(e.target.value)}
                    className={getSelectClasses(isSubmitting || isLoading)}
                    disabled={isSubmitting || isLoading}
                  >
                    {FISCAL_YEAR_END_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  {/* Dropdown arrow */}
                  <svg className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-oatmeal-400 pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <motion.button
                  type="submit"
                  disabled={isSubmitting || isLoading}
                  whileHover={{ y: -2 }}
                  whileTap={{ y: 0, scale: 0.98 }}
                  className="w-full py-3.5 bg-sage-500 hover:bg-sage-400 disabled:bg-sage-500/50 disabled:cursor-not-allowed text-oatmeal-50 font-sans font-bold rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  {isSubmitting || isLoading ? (
                    <>
                      <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Creating...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                      </svg>
                      Create Client
                    </>
                  )}
                </motion.button>
              </div>
            </form>

            {/* Zero-Storage Badge */}
            <div className="px-6 pb-5">
              <div className="flex items-center justify-center gap-2 text-xs font-sans text-oatmeal-500">
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                Only client metadata is stored. No financial data.
              </div>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

export default CreateClientModal;
