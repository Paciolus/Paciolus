'use client';

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useFocusTrap } from '@/hooks';
import { MODAL_OVERLAY_VARIANTS, MODAL_CONTENT_VARIANTS } from '@/utils/themeUtils';
import { getInputClasses, getSelectClasses } from '@/utils/themeUtils';
import type { Client } from '@/types/client';
import type { EngagementCreateInput, MaterialityBasis } from '@/types/engagement';

interface CreateEngagementModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSubmit: (data: EngagementCreateInput) => Promise<boolean>;
  clients: Client[];
  isLoading: boolean;
}

export function CreateEngagementModal({
  isOpen,
  onClose,
  onSubmit,
  clients,
  isLoading,
}: CreateEngagementModalProps) {
  const [clientId, setClientId] = useState('');
  const [periodStart, setPeriodStart] = useState('');
  const [periodEnd, setPeriodEnd] = useState('');
  const [materialityBasis, setMaterialityBasis] = useState<MaterialityBasis | ''>('');
  const [materialityPercentage, setMaterialityPercentage] = useState('');
  const [materialityAmount, setMaterialityAmount] = useState('');
  const [pmFactor, setPmFactor] = useState('0.75');
  const [trivialFactor, setTrivialFactor] = useState('0.05');
  const [error, setError] = useState<string | null>(null);
  const [touched, setTouched] = useState<Record<string, boolean>>({});

  const resetForm = () => {
    setClientId('');
    setPeriodStart('');
    setPeriodEnd('');
    setMaterialityBasis('');
    setMaterialityPercentage('');
    setMaterialityAmount('');
    setPmFactor('0.75');
    setTrivialFactor('0.05');
    setError(null);
    setTouched({});
  };

  const handleClose = () => {
    resetForm();
    onClose();
  };

  const focusTrapRef = useFocusTrap(isOpen, handleClose);

  const validate = (): string | null => {
    if (!clientId) return 'Please select a client';
    if (!periodStart) return 'Period start date is required';
    if (!periodEnd) return 'Period end date is required';
    if (new Date(periodEnd) <= new Date(periodStart)) {
      return 'Period end must be after period start';
    }
    if (materialityAmount && isNaN(parseFloat(materialityAmount))) {
      return 'Materiality amount must be a number';
    }
    if (materialityPercentage && (isNaN(parseFloat(materialityPercentage)) || parseFloat(materialityPercentage) <= 0 || parseFloat(materialityPercentage) > 100)) {
      return 'Materiality percentage must be between 0 and 100';
    }
    return null;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    const validationError = validate();
    if (validationError) {
      setError(validationError);
      return;
    }

    const data: EngagementCreateInput = {
      client_id: parseInt(clientId, 10),
      period_start: new Date(periodStart).toISOString(),
      period_end: new Date(periodEnd).toISOString(),
    };

    if (materialityBasis) {
      data.materiality_basis = materialityBasis;
    }
    if (materialityPercentage) {
      data.materiality_percentage = parseFloat(materialityPercentage);
    }
    if (materialityAmount) {
      data.materiality_amount = parseFloat(materialityAmount);
    }
    if (pmFactor) {
      data.performance_materiality_factor = parseFloat(pmFactor);
    }
    if (trivialFactor) {
      data.trivial_threshold_factor = parseFloat(trivialFactor);
    }

    const success = await onSubmit(data);
    if (success) {
      handleClose();
    }
  };

  const markTouched = (field: string) => {
    setTouched(prev => ({ ...prev, [field]: true }));
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          {/* Overlay */}
          <motion.div
            variants={MODAL_OVERLAY_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="hidden"
            className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-sm"
            onClick={handleClose}
          />

          {/* Modal */}
          <motion.div
            ref={focusTrapRef}
            role="dialog"
            aria-modal="true"
            aria-labelledby="create-engagement-title"
            variants={MODAL_CONTENT_VARIANTS}
            initial="hidden"
            animate="visible"
            exit="exit"
            className="relative bg-surface-card rounded-2xl border border-theme shadow-theme-elevated w-full max-w-lg max-h-[90vh] overflow-y-auto"
          >
            <form onSubmit={handleSubmit}>
              {/* Header */}
              <div className="px-6 py-5 border-b border-theme">
                <h2 id="create-engagement-title" className="text-xl font-serif font-semibold text-content-primary">
                  New Diagnostic Workspace
                </h2>
                <p className="text-sm font-sans text-content-tertiary mt-1">
                  Configure a workspace to organize your tool runs
                </p>
              </div>

              {/* Body */}
              <div className="px-6 py-5 space-y-5">
                {/* Error display */}
                {error && (
                  <div className="p-3 bg-clay-50 border border-clay-200 rounded-lg">
                    <p className="text-clay-700 text-sm font-sans">{error}</p>
                  </div>
                )}

                {/* Client selector */}
                <div>
                  <label htmlFor="engagement-client" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                    Client
                  </label>
                  <select
                    id="engagement-client"
                    value={clientId}
                    onChange={(e) => { setClientId(e.target.value); markTouched('client'); }}
                    className={getSelectClasses()}
                  >
                    <option value="">Select a client...</option>
                    {clients.map(client => (
                      <option key={client.id} value={client.id.toString()}>
                        {client.name}
                      </option>
                    ))}
                  </select>
                </div>

                {/* Period dates */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="engagement-period-start" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                      Period Start
                    </label>
                    <input
                      id="engagement-period-start"
                      type="date"
                      value={periodStart}
                      onChange={(e) => { setPeriodStart(e.target.value); markTouched('periodStart'); }}
                      onBlur={() => markTouched('periodStart')}
                      className={getInputClasses(!!touched.periodStart, !periodStart && !!touched.periodStart, !!periodStart)}
                    />
                  </div>
                  <div>
                    <label htmlFor="engagement-period-end" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                      Period End
                    </label>
                    <input
                      id="engagement-period-end"
                      type="date"
                      value={periodEnd}
                      onChange={(e) => { setPeriodEnd(e.target.value); markTouched('periodEnd'); }}
                      onBlur={() => markTouched('periodEnd')}
                      className={getInputClasses(!!touched.periodEnd, !periodEnd && !!touched.periodEnd, !!periodEnd)}
                    />
                  </div>
                </div>

                {/* Materiality section */}
                <div className="border-t border-theme-divider pt-5">
                  <h3 className="text-sm font-serif font-semibold text-content-primary mb-3">
                    Materiality (Optional)
                  </h3>

                  <div className="space-y-4">
                    {/* Basis */}
                    <div>
                      <label htmlFor="materiality-basis" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                        Basis
                      </label>
                      <select
                        id="materiality-basis"
                        value={materialityBasis}
                        onChange={(e) => setMaterialityBasis(e.target.value as MaterialityBasis | '')}
                        className={getSelectClasses()}
                      >
                        <option value="">None</option>
                        <option value="revenue">Revenue</option>
                        <option value="assets">Total Assets</option>
                        <option value="manual">Manual Entry</option>
                      </select>
                    </div>

                    {/* Amount + Percentage row */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="materiality-amount" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                          Amount ($)
                        </label>
                        <input
                          id="materiality-amount"
                          type="number"
                          step="0.01"
                          min="0"
                          value={materialityAmount}
                          onChange={(e) => setMaterialityAmount(e.target.value)}
                          placeholder="e.g. 50000"
                          className={getInputClasses(false, false, !!materialityAmount)}
                        />
                      </div>
                      <div>
                        <label htmlFor="materiality-percentage" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                          Percentage (%)
                        </label>
                        <input
                          id="materiality-percentage"
                          type="number"
                          step="0.01"
                          min="0"
                          max="100"
                          value={materialityPercentage}
                          onChange={(e) => setMaterialityPercentage(e.target.value)}
                          placeholder="e.g. 5"
                          className={getInputClasses(false, false, !!materialityPercentage)}
                        />
                      </div>
                    </div>

                    {/* PM + Trivial factors */}
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <label htmlFor="pm-factor" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                          PM Factor
                        </label>
                        <input
                          id="pm-factor"
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={pmFactor}
                          onChange={(e) => setPmFactor(e.target.value)}
                          className={getInputClasses(false, false, !!pmFactor)}
                        />
                        <p className="text-xs font-sans text-content-tertiary mt-1">Default: 0.75 (75%)</p>
                      </div>
                      <div>
                        <label htmlFor="trivial-factor" className="block text-sm font-sans font-medium text-content-secondary mb-1.5">
                          Trivial Factor
                        </label>
                        <input
                          id="trivial-factor"
                          type="number"
                          step="0.01"
                          min="0"
                          max="1"
                          value={trivialFactor}
                          onChange={(e) => setTrivialFactor(e.target.value)}
                          className={getInputClasses(false, false, !!trivialFactor)}
                        />
                        <p className="text-xs font-sans text-content-tertiary mt-1">Default: 0.05 (5%)</p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              {/* Footer */}
              <div className="px-6 py-4 border-t border-theme flex gap-3 justify-end">
                <button
                  type="button"
                  onClick={handleClose}
                  disabled={isLoading}
                  className="px-5 py-2.5 bg-surface-card border border-oatmeal-300 text-content-primary hover:bg-surface-card-secondary font-sans font-medium rounded-xl transition-colors"
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  disabled={isLoading}
                  className="px-5 py-2.5 bg-sage-600 hover:bg-sage-700 disabled:bg-sage-500/50 text-white font-sans font-bold rounded-xl transition-colors flex items-center gap-2"
                >
                  {isLoading ? (
                    <>
                      <svg className="w-4 h-4 animate-spin" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
                      </svg>
                      Creating...
                    </>
                  ) : (
                    'Create Workspace'
                  )}
                </button>
              </div>
            </form>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
}
