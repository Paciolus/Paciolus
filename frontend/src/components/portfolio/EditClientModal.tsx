'use client';

import { useEffect, useMemo, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useFormValidation, commonValidators, useFocusTrap } from '@/hooks';
import type { Client, ClientUpdateInput, Industry, IndustryOption } from '@/types/client';
import { FISCAL_YEAR_END_OPTIONS } from '@/types/client';
import {
  getInputClasses,
  getSelectClasses,
  MODAL_OVERLAY_VARIANTS,
  MODAL_CONTENT_VARIANTS,
} from '@/utils';

/**
 * EditClientModal - Sprint 56 Portfolio Enhancement
 *
 * Design: "Obsidian Vault" modal aesthetic with Tier 2 Form Validation
 * - Pre-populated with existing client data
 * - Sage Green border shift for active/focused inputs
 * - Clay Red for validation errors
 * - Smooth enter/exit animations
 *
 * ZERO-STORAGE: Updates client metadata only, no financial data
 */

interface EditClientModalProps {
  isOpen: boolean;
  client: Client | null;
  onClose: () => void;
  onSubmit: (id: number, data: ClientUpdateInput) => Promise<Client | null>;
  industries: IndustryOption[];
  isLoading?: boolean;
}

type ClientFormValues = {
  name: string;
  industry: Industry;
  fiscal_year_end: string;
}

export function EditClientModal({
  isOpen,
  client,
  onClose,
  onSubmit,
  industries,
  isLoading = false,
}: EditClientModalProps) {
  // Ref for auto-focus
  const nameInputRef = useRef<HTMLInputElement>(null);
  const focusTrapRef = useFocusTrap(isOpen, onClose);
  const prevClientIdRef = useRef<number | null>(null);

  // Initial values from the client being edited (memoized to stabilize reset identity)
  const initialValues = useMemo<ClientFormValues>(() => ({
    name: client?.name || '',
    industry: (client?.industry as Industry) || 'other',
    fiscal_year_end: client?.fiscal_year_end || '12-31',
  }), [client?.name, client?.industry, client?.fiscal_year_end]);

  // Form state via useFormValidation hook
  const {
    values,
    errors,
    isSubmitting,
    setValue,
    handleBlur,
    handleSubmit,
    reset,
    getFieldState,
  } = useFormValidation<ClientFormValues>({
    initialValues,
    validationRules: {
      name: [
        commonValidators.required('Client name is required'),
        commonValidators.minLength(2, 'Name must be at least 2 characters'),
        commonValidators.maxLength(255, 'Name must be less than 255 characters'),
      ],
    },
    onSubmit: async (formValues) => {
      if (!client) return;

      // Only send changed fields
      const updates: ClientUpdateInput = {};
      if (formValues.name.trim() !== client.name) {
        updates.name = formValues.name.trim();
      }
      if (formValues.industry !== client.industry) {
        updates.industry = formValues.industry;
      }
      if (formValues.fiscal_year_end !== client.fiscal_year_end) {
        updates.fiscal_year_end = formValues.fiscal_year_end;
      }

      // Only submit if there are changes
      if (Object.keys(updates).length === 0) {
        onClose();
        return;
      }

      const result = await onSubmit(client.id, updates);
      if (result) {
        onClose();
      }
    },
  });

  // Reset form when modal opens with a (possibly different) client
  useEffect(() => {
    if (isOpen && client && client.id !== prevClientIdRef.current) {
      prevClientIdRef.current = client.id;
      reset(initialValues);
      // Auto-focus name input after animation
      setTimeout(() => nameInputRef.current?.focus(), 100);
    }
    if (!isOpen) {
      prevClientIdRef.current = null;
    }
  }, [isOpen, client, reset, initialValues]);

  // Helper to get input classes using shared utility
  const getFieldInputClasses = (field: keyof ClientFormValues) => {
    const state = getFieldState(field);
    const disabled = isSubmitting || isLoading;
    return getInputClasses(state.touched, state.hasError, state.hasValue, disabled);
  };

  // Computed disabled state
  const isDisabled = isSubmitting || isLoading;

  if (!client) return null;

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
            ref={focusTrapRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="edit-client-title"
            variants={MODAL_CONTENT_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative bg-surface-card rounded-2xl border border-theme shadow-2xl w-full max-w-md overflow-hidden"
          >
            {/* Header */}
            <div className="px-6 py-5 border-b border-theme">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-oatmeal-500/10 border border-oatmeal-500/30 flex items-center justify-center">
                  <svg className="w-5 h-5 text-content-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                  </svg>
                </div>
                <div>
                  <h2 id="edit-client-title" className="text-xl font-serif font-semibold text-content-primary">
                    Edit Client
                  </h2>
                  <p className="text-content-tertiary text-sm font-sans">
                    Update client information
                  </p>
                </div>
              </div>

              {/* Close button */}
              <button
                onClick={onClose}
                className="absolute top-4 right-4 p-2 text-content-secondary hover:text-content-primary transition-colors"
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
                <label htmlFor="edit-client-name" className="block text-content-primary font-sans font-medium mb-2">
                  Client Name <span className="text-clay-400">*</span>
                </label>
                <input
                  ref={nameInputRef}
                  id="edit-client-name"
                  type="text"
                  value={values.name}
                  onChange={(e) => setValue('name', e.target.value)}
                  onBlur={handleBlur('name')}
                  placeholder="e.g., Acme Corporation"
                  className={getFieldInputClasses('name')}
                  disabled={isDisabled}
                />
                {getFieldState('name').showError && (
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
                <label htmlFor="edit-client-industry" className="block text-content-primary font-sans font-medium mb-2">
                  Industry
                </label>
                <div className="relative">
                  <select
                    id="edit-client-industry"
                    value={values.industry}
                    onChange={(e) => setValue('industry', e.target.value as Industry)}
                    className={getSelectClasses(isDisabled)}
                    disabled={isDisabled}
                  >
                    {industries.map((ind) => (
                      <option key={ind.value} value={ind.value}>
                        {ind.label}
                      </option>
                    ))}
                  </select>
                  {/* Dropdown arrow */}
                  <svg className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-content-secondary pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {/* Fiscal Year End */}
              <div>
                <label htmlFor="edit-client-fye" className="block text-content-primary font-sans font-medium mb-2">
                  Fiscal Year End
                </label>
                <div className="relative">
                  <select
                    id="edit-client-fye"
                    value={values.fiscal_year_end}
                    onChange={(e) => setValue('fiscal_year_end', e.target.value)}
                    className={getSelectClasses(isDisabled)}
                    disabled={isDisabled}
                  >
                    {FISCAL_YEAR_END_OPTIONS.map((opt) => (
                      <option key={opt.value} value={opt.value}>
                        {opt.label}
                      </option>
                    ))}
                  </select>
                  {/* Dropdown arrow */}
                  <svg className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-content-secondary pointer-events-none" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
                  </svg>
                </div>
              </div>

              {/* Submit Button */}
              <div className="pt-2">
                <motion.button
                  type="submit"
                  disabled={isDisabled}
                  whileHover={{ y: -2 }}
                  whileTap={{ y: 0, scale: 0.98 }}
                  className="w-full py-3.5 bg-sage-500 hover:bg-sage-400 disabled:bg-sage-500/50 disabled:cursor-not-allowed text-oatmeal-50 font-sans font-bold rounded-xl transition-colors flex items-center justify-center gap-2"
                >
                  {isDisabled ? (
                    <>
                      <svg className="w-5 h-5 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Saving...
                    </>
                  ) : (
                    <>
                      <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                      </svg>
                      Save Changes
                    </>
                  )}
                </motion.button>
              </div>
            </form>

            {/* Zero-Storage Badge */}
            <div className="px-6 pb-5">
              <div className="flex items-center justify-center gap-2 text-xs font-sans text-content-tertiary">
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

export default EditClientModal;
