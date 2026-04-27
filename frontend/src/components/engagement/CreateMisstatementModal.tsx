'use client';

/**
 * Sprint 729b/729c — CreateMisstatementModal.
 *
 * Extracted from SumSchedulePanel so it can be reused with pre-filled
 * initial values from AJE workflow / sampling capture helpers (Sprint 729c).
 */

import { useState } from 'react';
import { motion } from 'framer-motion';
import type {
  UncorrectedMisstatement,
  UncorrectedMisstatementCreateInput,
  MisstatementSourceType,
  MisstatementClassification,
  AccountAffected,
} from '@/types/uncorrected-misstatements';
import {
  SOURCE_TYPE_LABELS,
  CLASSIFICATION_LABELS,
} from '@/types/uncorrected-misstatements';

const SOURCE_TYPES: MisstatementSourceType[] = [
  'adjusting_entry_passed',
  'sample_projection',
  'known_error',
];
const CLASSIFICATIONS: MisstatementClassification[] = ['factual', 'judgmental', 'projected'];

export interface CreateMisstatementInitialValues {
  source_type?: MisstatementSourceType;
  classification?: MisstatementClassification;
  source_reference?: string;
  description?: string;
  account_name?: string;
  account_side?: 'DR' | 'CR';
  account_amount?: number;
  fs_impact_net_income?: number;
  fs_impact_net_assets?: number;
  cpa_notes?: string;
}

interface Props {
  engagementId: number;
  initialValues?: CreateMisstatementInitialValues;
  onClose: () => void;
  onCreate: (
    engagementId: number,
    data: UncorrectedMisstatementCreateInput,
  ) => Promise<UncorrectedMisstatement | null>;
}

export function CreateMisstatementModal({
  engagementId,
  initialValues,
  onClose,
  onCreate,
}: Props) {
  const [sourceType, setSourceType] = useState<MisstatementSourceType>(
    initialValues?.source_type ?? 'known_error',
  );
  const [classification, setClassification] = useState<MisstatementClassification>(
    initialValues?.classification ?? 'factual',
  );
  const [reference, setReference] = useState(initialValues?.source_reference ?? '');
  const [description, setDescription] = useState(initialValues?.description ?? '');
  const [accountName, setAccountName] = useState(initialValues?.account_name ?? '');
  const [accountSide, setAccountSide] = useState<'DR' | 'CR'>(
    initialValues?.account_side ?? 'DR',
  );
  const [accountAmount, setAccountAmount] = useState(
    initialValues?.account_amount !== undefined ? String(initialValues.account_amount) : '',
  );
  const [niImpact, setNiImpact] = useState(
    initialValues?.fs_impact_net_income !== undefined
      ? String(initialValues.fs_impact_net_income)
      : '',
  );
  const [naImpact, setNaImpact] = useState(
    initialValues?.fs_impact_net_assets !== undefined
      ? String(initialValues.fs_impact_net_assets)
      : '',
  );
  const [notes, setNotes] = useState(initialValues?.cpa_notes ?? '');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const onSourceTypeChange = (st: MisstatementSourceType) => {
    setSourceType(st);
    if (st === 'sample_projection') setClassification('projected');
    else if (st === 'adjusting_entry_passed') setClassification('judgmental');
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);

    const acctAmt = parseFloat(accountAmount);
    const ni = parseFloat(niImpact);
    const na = parseFloat(naImpact);

    if (Number.isNaN(acctAmt) || acctAmt <= 0) {
      setSubmitError('Account amount must be positive');
      setSubmitting(false);
      return;
    }
    if (Number.isNaN(ni) || Number.isNaN(na)) {
      setSubmitError('F/S impacts must be numeric');
      setSubmitting(false);
      return;
    }

    const accounts: AccountAffected[] = [
      { account: accountName.trim(), debit_credit: accountSide, amount: acctAmt },
    ];

    const created = await onCreate(engagementId, {
      source_type: sourceType,
      classification,
      source_reference: reference.trim(),
      description: description.trim(),
      accounts_affected: accounts,
      fs_impact_net_income: ni,
      fs_impact_net_assets: na,
      cpa_notes: notes.trim() || null,
    });

    setSubmitting(false);
    if (created) onClose();
    else setSubmitError('Failed to create misstatement');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-obsidian-deep/50 px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface-card rounded-xl border border-theme shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6"
      >
        <h4 className="text-lg font-serif font-semibold text-content-primary mb-4">
          New Misstatement
        </h4>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs font-sans text-content-secondary">Source</span>
              <select
                value={sourceType}
                onChange={e => onSourceTypeChange(e.target.value as MisstatementSourceType)}
                className="mt-1 w-full font-sans text-sm border border-theme rounded px-2 py-1.5"
              >
                {SOURCE_TYPES.map(t => (
                  <option key={t} value={t}>
                    {SOURCE_TYPE_LABELS[t]}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs font-sans text-content-secondary">Classification</span>
              <select
                value={classification}
                onChange={e =>
                  setClassification(e.target.value as MisstatementClassification)
                }
                className="mt-1 w-full font-sans text-sm border border-theme rounded px-2 py-1.5"
              >
                {CLASSIFICATIONS.map(c => (
                  <option key={c} value={c}>
                    {CLASSIFICATION_LABELS[c]}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <label className="block">
            <span className="text-xs font-sans text-content-secondary">Source reference</span>
            <input
              type="text"
              required
              value={reference}
              onChange={e => setReference(e.target.value)}
              className="mt-1 w-full font-sans text-sm border border-theme rounded px-2 py-1.5"
            />
          </label>

          <label className="block">
            <span className="text-xs font-sans text-content-secondary">Description</span>
            <textarea
              required
              value={description}
              onChange={e => setDescription(e.target.value)}
              className="mt-1 w-full font-sans text-sm border border-theme rounded px-2 py-1.5"
              rows={2}
            />
          </label>

          <fieldset className="border border-theme rounded p-3">
            <legend className="text-xs font-sans text-content-secondary px-1">
              Account affected
            </legend>
            <div className="grid grid-cols-3 gap-2">
              <input
                type="text"
                required
                placeholder="Account name"
                value={accountName}
                onChange={e => setAccountName(e.target.value)}
                className="col-span-2 font-mono text-sm border border-theme rounded px-2 py-1.5"
              />
              <select
                value={accountSide}
                onChange={e => setAccountSide(e.target.value as 'DR' | 'CR')}
                className="font-mono text-sm border border-theme rounded px-2 py-1.5"
              >
                <option value="DR">DR</option>
                <option value="CR">CR</option>
              </select>
            </div>
            <input
              type="number"
              step="0.01"
              required
              placeholder="Amount"
              value={accountAmount}
              onChange={e => setAccountAmount(e.target.value)}
              className="mt-2 w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
            />
          </fieldset>

          <fieldset className="border border-theme rounded p-3">
            <legend className="text-xs font-sans text-content-secondary px-1">
              F/S impact (signed; negative = decrease)
            </legend>
            <div className="grid grid-cols-2 gap-2">
              <label className="block">
                <span className="text-xs font-sans text-content-tertiary">Net Income Δ</span>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={niImpact}
                  onChange={e => setNiImpact(e.target.value)}
                  className="mt-1 w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
                />
              </label>
              <label className="block">
                <span className="text-xs font-sans text-content-tertiary">Net Assets Δ</span>
                <input
                  type="number"
                  step="0.01"
                  required
                  value={naImpact}
                  onChange={e => setNaImpact(e.target.value)}
                  className="mt-1 w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
                />
              </label>
            </div>
          </fieldset>

          <label className="block">
            <span className="text-xs font-sans text-content-secondary">CPA notes (optional — required for MATERIAL aggregate override)</span>
            <textarea
              value={notes}
              onChange={e => setNotes(e.target.value)}
              className="mt-1 w-full font-sans text-sm border border-theme rounded px-2 py-1.5"
              rows={2}
            />
          </label>

          {submitError && (
            <p className="text-xs font-sans text-clay-600">{submitError}</p>
          )}

          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={onClose}
              className="px-3 py-1.5 text-sm font-sans text-content-secondary hover:text-content-primary border border-theme rounded-lg"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={submitting}
              className="px-4 py-1.5 text-sm font-sans bg-sage-500 text-white rounded-lg hover:bg-sage-600 transition-colors disabled:opacity-40"
            >
              {submitting ? 'Creating…' : 'Create'}
            </button>
          </div>
        </form>
      </motion.div>
    </div>
  );
}
