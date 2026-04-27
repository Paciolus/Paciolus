'use client';

/**
 * Sprint 728b — AnalyticalExpectationsPanel (ISA 520).
 *
 * List + create/edit + capture-result UI for analytical-procedure
 * expectations. Sits on the workspace detail page as the
 * "Expectations" tab.
 *
 * Design mandate: Oat & Obsidian tokens only. Financial numbers
 * use font-mono; headers font-serif.
 */

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type {
  AnalyticalExpectation,
  AnalyticalExpectationCreateInput,
  AnalyticalExpectationUpdateInput,
  ExpectationTargetType,
  ExpectationCorroborationTag,
} from '@/types/analytical-expectations';
import {
  EXPECTATION_TARGET_LABELS,
  EXPECTATION_TAG_LABELS,
  EXPECTATION_STATUS_LABELS,
  EXPECTATION_STATUS_COLORS,
} from '@/types/analytical-expectations';
import { formatCurrency } from '@/utils/formatting';

interface Props {
  engagementId: number;
  items: AnalyticalExpectation[];
  isLoading: boolean;
  onCreate: (
    engagementId: number,
    data: AnalyticalExpectationCreateInput,
  ) => Promise<AnalyticalExpectation | null>;
  onUpdate: (
    expectationId: number,
    data: AnalyticalExpectationUpdateInput,
  ) => Promise<AnalyticalExpectation | null>;
  onArchive: (expectationId: number) => Promise<boolean>;
  onDownload: () => void;
}

const TARGET_TYPES: ExpectationTargetType[] = ['account', 'balance', 'ratio', 'flux_line'];
const TAG_OPTIONS: ExpectationCorroborationTag[] = [
  'industry_data',
  'prior_period',
  'budget',
  'regression_model',
  'other',
];

function formatExpected(e: AnalyticalExpectation): string {
  if (e.expected_value !== null) return formatCurrency(e.expected_value);
  if (e.expected_range_low !== null && e.expected_range_high !== null) {
    return `${formatCurrency(e.expected_range_low)} – ${formatCurrency(e.expected_range_high)}`;
  }
  return '—';
}

function formatThreshold(e: AnalyticalExpectation): string {
  if (e.precision_threshold_amount !== null) {
    return formatCurrency(e.precision_threshold_amount);
  }
  if (e.precision_threshold_percent !== null) {
    return `${e.precision_threshold_percent.toFixed(2)}%`;
  }
  return '—';
}

export function AnalyticalExpectationsPanel({
  engagementId,
  items,
  isLoading,
  onCreate,
  onUpdate,
  onArchive,
  onDownload,
}: Props) {
  const [showCreate, setShowCreate] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);
  const [actualInput, setActualInput] = useState<Record<number, string>>({});

  const counts = useMemo(() => {
    return {
      total: items.length,
      not_evaluated: items.filter(i => i.result_status === 'not_evaluated').length,
      within: items.filter(i => i.result_status === 'within_threshold').length,
      exceeds: items.filter(i => i.result_status === 'exceeds_threshold').length,
    };
  }, [items]);

  const handleCaptureActual = async (id: number) => {
    const raw = actualInput[id];
    if (!raw) return;
    const value = parseFloat(raw);
    if (Number.isNaN(value)) return;
    setSavingId(id);
    await onUpdate(id, { result_actual_value: value });
    setSavingId(null);
    setActualInput(prev => {
      const next = { ...prev };
      delete next[id];
      return next;
    });
  };

  const handleClearResult = async (id: number) => {
    setSavingId(id);
    await onUpdate(id, { clear_result: true });
    setSavingId(null);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-serif font-semibold text-content-primary">
            Analytical Expectations
          </h3>
          <p className="text-xs font-sans text-content-tertiary mt-0.5">
            ISA 520 / AU-C 520 workpaper. Document the expected value, precision, basis, and conclusion for each analytical procedure.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={onDownload}
            disabled={items.length === 0}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-sans text-content-secondary hover:text-content-primary border border-theme rounded-lg hover:border-sage-200 transition-colors disabled:opacity-40 disabled:cursor-not-allowed"
          >
            Download workpaper
          </button>
          <button
            type="button"
            onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 px-3 py-1.5 text-sm font-sans bg-sage-500 text-white rounded-lg hover:bg-sage-600 transition-colors"
          >
            + Add Expectation
          </button>
        </div>
      </div>

      {/* Status counts */}
      <div className="grid grid-cols-4 gap-3">
        <div className="bg-surface-card border border-theme rounded-lg px-3 py-2">
          <p className="text-xs font-sans text-content-tertiary">Total</p>
          <p className="text-lg font-mono text-content-primary">{counts.total}</p>
        </div>
        <div className="bg-surface-card border border-theme rounded-lg px-3 py-2">
          <p className="text-xs font-sans text-content-tertiary">Not Evaluated</p>
          <p className="text-lg font-mono text-content-primary">{counts.not_evaluated}</p>
        </div>
        <div className="bg-surface-card border border-sage-200 rounded-lg px-3 py-2">
          <p className="text-xs font-sans text-sage-700">Within</p>
          <p className="text-lg font-mono text-sage-700">{counts.within}</p>
        </div>
        <div className="bg-surface-card border border-clay-200 rounded-lg px-3 py-2">
          <p className="text-xs font-sans text-clay-700">Exceeds</p>
          <p className="text-lg font-mono text-clay-700">{counts.exceeds}</p>
        </div>
      </div>

      {/* Items */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="w-6 h-6 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="bg-oatmeal-50 border border-theme rounded-lg p-6 text-center">
          <p className="text-sm font-sans text-content-secondary">
            No analytical expectations recorded yet.
          </p>
          <p className="text-xs font-sans text-content-tertiary mt-1">
            Add an expectation before running flux, ratio, or multi-period TB procedures.
          </p>
        </div>
      ) : (
        <div className="space-y-2">
          <AnimatePresence>
            {items.map(item => (
              <motion.div
                key={item.id}
                layout
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                className="bg-surface-card border border-theme rounded-lg p-4"
                data-testid={`expectation-row-${item.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-sans bg-oatmeal-100 text-content-secondary border border-theme">
                        {EXPECTATION_TARGET_LABELS[item.procedure_target_type]}
                      </span>
                      <span className="font-mono text-sm text-content-primary">
                        {item.procedure_target_label}
                      </span>
                      <span
                        className={`inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-sans border ${EXPECTATION_STATUS_COLORS[item.result_status]}`}
                      >
                        {EXPECTATION_STATUS_LABELS[item.result_status]}
                      </span>
                    </div>
                    <div className="grid grid-cols-3 gap-3 text-xs">
                      <div>
                        <p className="font-sans text-content-tertiary">Expected</p>
                        <p className="font-mono text-content-primary">{formatExpected(item)}</p>
                      </div>
                      <div>
                        <p className="font-sans text-content-tertiary">Threshold</p>
                        <p className="font-mono text-content-primary">{formatThreshold(item)}</p>
                      </div>
                      <div>
                        <p className="font-sans text-content-tertiary">Variance</p>
                        <p className="font-mono text-content-primary">
                          {item.result_variance_amount === null
                            ? '—'
                            : formatCurrency(item.result_variance_amount)}
                        </p>
                      </div>
                    </div>
                    <p className="text-xs font-sans text-content-secondary mt-2 italic">
                      {item.corroboration_basis_text}
                    </p>
                    {item.corroboration_tags.length > 0 && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {item.corroboration_tags.map(tag => (
                          <span
                            key={tag}
                            className="inline-flex items-center px-1.5 py-0.5 rounded text-[10px] font-sans bg-oatmeal-100 text-content-secondary"
                          >
                            {EXPECTATION_TAG_LABELS[tag as ExpectationCorroborationTag] ?? tag}
                          </span>
                        ))}
                      </div>
                    )}
                  </div>
                  <button
                    type="button"
                    onClick={() => onArchive(item.id)}
                    className="text-xs font-sans text-content-tertiary hover:text-clay-600 transition-colors"
                    aria-label={`Archive expectation ${item.procedure_target_label}`}
                  >
                    Archive
                  </button>
                </div>

                {/* Capture-actual inline */}
                <div className="mt-3 pt-3 border-t border-theme-divider flex items-center gap-2">
                  {item.result_status === 'not_evaluated' ? (
                    <>
                      <label className="text-xs font-sans text-content-tertiary" htmlFor={`actual-${item.id}`}>
                        Actual:
                      </label>
                      <input
                        id={`actual-${item.id}`}
                        type="number"
                        step="0.01"
                        value={actualInput[item.id] ?? ''}
                        onChange={e =>
                          setActualInput(prev => ({ ...prev, [item.id]: e.target.value }))
                        }
                        className="font-mono text-sm border border-theme rounded px-2 py-1 w-32 focus:outline-none focus:border-sage-500"
                      />
                      <button
                        type="button"
                        onClick={() => handleCaptureActual(item.id)}
                        disabled={savingId === item.id || !actualInput[item.id]}
                        className="px-3 py-1 text-xs font-sans bg-sage-500 text-white rounded hover:bg-sage-600 transition-colors disabled:opacity-40"
                      >
                        Capture
                      </button>
                    </>
                  ) : (
                    <>
                      <span className="text-xs font-sans text-content-tertiary">Actual:</span>
                      <span className="font-mono text-sm text-content-primary">
                        {formatCurrency(item.result_actual_value ?? 0)}
                      </span>
                      <button
                        type="button"
                        onClick={() => handleClearResult(item.id)}
                        disabled={savingId === item.id}
                        className="text-xs font-sans text-content-tertiary hover:text-clay-600 transition-colors ml-auto"
                      >
                        Re-evaluate
                      </button>
                    </>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {/* Create modal */}
      {showCreate && (
        <CreateExpectationModal
          engagementId={engagementId}
          onClose={() => setShowCreate(false)}
          onCreate={onCreate}
        />
      )}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Create modal
// ---------------------------------------------------------------------------

interface ModalProps {
  engagementId: number;
  onClose: () => void;
  onCreate: (
    engagementId: number,
    data: AnalyticalExpectationCreateInput,
  ) => Promise<AnalyticalExpectation | null>;
}

function CreateExpectationModal({ engagementId, onClose, onCreate }: ModalProps) {
  const [targetType, setTargetType] = useState<ExpectationTargetType>('account');
  const [label, setLabel] = useState('');
  const [expectedMode, setExpectedMode] = useState<'value' | 'range'>('value');
  const [expectedValue, setExpectedValue] = useState('');
  const [rangeLow, setRangeLow] = useState('');
  const [rangeHigh, setRangeHigh] = useState('');
  const [thresholdMode, setThresholdMode] = useState<'amount' | 'percent'>('amount');
  const [thresholdAmount, setThresholdAmount] = useState('');
  const [thresholdPercent, setThresholdPercent] = useState('');
  const [tags, setTags] = useState<ExpectationCorroborationTag[]>([]);
  const [basis, setBasis] = useState('');
  const [notes, setNotes] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  const toggleTag = (tag: ExpectationCorroborationTag) => {
    setTags(prev => (prev.includes(tag) ? prev.filter(t => t !== tag) : [...prev, tag]));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitError(null);
    setSubmitting(true);

    const payload: AnalyticalExpectationCreateInput = {
      procedure_target_type: targetType,
      procedure_target_label: label.trim(),
      corroboration_basis_text: basis.trim(),
      corroboration_tags: tags,
      cpa_notes: notes.trim() || null,
    };

    if (expectedMode === 'value') {
      const v = parseFloat(expectedValue);
      if (Number.isNaN(v)) {
        setSubmitError('Expected value must be numeric');
        setSubmitting(false);
        return;
      }
      payload.expected_value = v;
    } else {
      const lo = parseFloat(rangeLow);
      const hi = parseFloat(rangeHigh);
      if (Number.isNaN(lo) || Number.isNaN(hi)) {
        setSubmitError('Range bounds must be numeric');
        setSubmitting(false);
        return;
      }
      if (hi <= lo) {
        setSubmitError('Range high must be greater than range low');
        setSubmitting(false);
        return;
      }
      payload.expected_range_low = lo;
      payload.expected_range_high = hi;
    }

    if (thresholdMode === 'amount') {
      const t = parseFloat(thresholdAmount);
      if (Number.isNaN(t) || t <= 0) {
        setSubmitError('Threshold amount must be positive');
        setSubmitting(false);
        return;
      }
      payload.precision_threshold_amount = t;
    } else {
      const p = parseFloat(thresholdPercent);
      if (Number.isNaN(p) || p <= 0) {
        setSubmitError('Threshold percent must be positive');
        setSubmitting(false);
        return;
      }
      payload.precision_threshold_percent = p;
    }

    if (tags.length === 0) {
      setSubmitError('Select at least one corroboration basis');
      setSubmitting(false);
      return;
    }

    const created = await onCreate(engagementId, payload);
    setSubmitting(false);
    if (created) onClose();
    else setSubmitError('Failed to create expectation');
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-obsidian-deep/50 px-4">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        className="bg-surface-card rounded-xl border border-theme shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto p-6"
      >
        <h4 className="text-lg font-serif font-semibold text-content-primary mb-4">
          New Analytical Expectation
        </h4>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <label className="block">
              <span className="text-xs font-sans text-content-secondary">Target type</span>
              <select
                value={targetType}
                onChange={e => setTargetType(e.target.value as ExpectationTargetType)}
                className="mt-1 w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
              >
                {TARGET_TYPES.map(t => (
                  <option key={t} value={t}>
                    {EXPECTATION_TARGET_LABELS[t]}
                  </option>
                ))}
              </select>
            </label>
            <label className="block">
              <span className="text-xs font-sans text-content-secondary">Target label</span>
              <input
                type="text"
                required
                value={label}
                onChange={e => setLabel(e.target.value)}
                placeholder="e.g., Revenue, Current Ratio"
                className="mt-1 w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
              />
            </label>
          </div>

          <fieldset className="border border-theme rounded p-3">
            <legend className="text-xs font-sans text-content-secondary px-1">Expected</legend>
            <div className="flex gap-3 mb-2">
              <label className="text-xs font-sans">
                <input
                  type="radio"
                  checked={expectedMode === 'value'}
                  onChange={() => setExpectedMode('value')}
                />{' '}
                Single value
              </label>
              <label className="text-xs font-sans">
                <input
                  type="radio"
                  checked={expectedMode === 'range'}
                  onChange={() => setExpectedMode('range')}
                />{' '}
                Range
              </label>
            </div>
            {expectedMode === 'value' ? (
              <input
                type="number"
                step="0.01"
                required
                value={expectedValue}
                onChange={e => setExpectedValue(e.target.value)}
                className="w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
              />
            ) : (
              <div className="grid grid-cols-2 gap-2">
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="Low"
                  value={rangeLow}
                  onChange={e => setRangeLow(e.target.value)}
                  className="font-mono text-sm border border-theme rounded px-2 py-1.5"
                />
                <input
                  type="number"
                  step="0.01"
                  required
                  placeholder="High"
                  value={rangeHigh}
                  onChange={e => setRangeHigh(e.target.value)}
                  className="font-mono text-sm border border-theme rounded px-2 py-1.5"
                />
              </div>
            )}
          </fieldset>

          <fieldset className="border border-theme rounded p-3">
            <legend className="text-xs font-sans text-content-secondary px-1">Precision threshold</legend>
            <div className="flex gap-3 mb-2">
              <label className="text-xs font-sans">
                <input
                  type="radio"
                  checked={thresholdMode === 'amount'}
                  onChange={() => setThresholdMode('amount')}
                />{' '}
                Amount
              </label>
              <label className="text-xs font-sans">
                <input
                  type="radio"
                  checked={thresholdMode === 'percent'}
                  onChange={() => setThresholdMode('percent')}
                />{' '}
                Percent
              </label>
            </div>
            {thresholdMode === 'amount' ? (
              <input
                type="number"
                step="0.01"
                required
                value={thresholdAmount}
                onChange={e => setThresholdAmount(e.target.value)}
                className="w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
              />
            ) : (
              <input
                type="number"
                step="0.01"
                required
                placeholder="e.g., 5.0 for 5%"
                value={thresholdPercent}
                onChange={e => setThresholdPercent(e.target.value)}
                className="w-full font-mono text-sm border border-theme rounded px-2 py-1.5"
              />
            )}
          </fieldset>

          <fieldset className="border border-theme rounded p-3">
            <legend className="text-xs font-sans text-content-secondary px-1">Corroboration basis</legend>
            <div className="flex flex-wrap gap-2 mb-2">
              {TAG_OPTIONS.map(tag => (
                <button
                  key={tag}
                  type="button"
                  onClick={() => toggleTag(tag)}
                  className={`text-xs font-sans px-2 py-1 rounded border transition-colors ${
                    tags.includes(tag)
                      ? 'bg-sage-500 text-white border-sage-500'
                      : 'bg-oatmeal-50 text-content-secondary border-theme hover:border-sage-200'
                  }`}
                >
                  {EXPECTATION_TAG_LABELS[tag]}
                </button>
              ))}
            </div>
            <textarea
              required
              value={basis}
              onChange={e => setBasis(e.target.value)}
              placeholder="Describe the source data and rationale (ISA 520 §A12-A13)"
              className="w-full font-sans text-sm border border-theme rounded px-2 py-1.5 mt-1"
              rows={3}
            />
          </fieldset>

          <label className="block">
            <span className="text-xs font-sans text-content-secondary">CPA notes (optional)</span>
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
