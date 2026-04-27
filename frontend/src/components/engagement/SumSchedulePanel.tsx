'use client';

/**
 * Sprint 729b — SumSchedulePanel (ISA 450).
 *
 * Displays the Summary of Uncorrected Misstatements: items grouped by
 * classification, materiality bucket box (driven by aggregate / overall
 * materiality), per-row disposition controls, and three-variant capture
 * form (passed AJE / sample projection / known error).
 *
 * Bucket color treatment per design mandate: sage for trivial/immaterial,
 * clay (reduced opacity) for approaching, clay for material. No yellow
 * token in Oat & Obsidian.
 */

import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type {
  UncorrectedMisstatement,
  UncorrectedMisstatementCreateInput,
  UncorrectedMisstatementUpdateInput,
  SumScheduleResponse,
  MisstatementSourceType,
  MisstatementClassification,
  MisstatementDisposition,
  MaterialityBucket,
} from '@/types/uncorrected-misstatements';
import {
  SOURCE_TYPE_LABELS,
  CLASSIFICATION_LABELS,
  DISPOSITION_LABELS,
  BUCKET_LABELS,
  BUCKET_TONE,
} from '@/types/uncorrected-misstatements';
import { formatCurrency } from '@/utils/formatting';
import { CreateMisstatementModal } from './CreateMisstatementModal';

interface Props {
  engagementId: number;
  schedule: SumScheduleResponse | null;
  isLoading: boolean;
  onCreate: (
    engagementId: number,
    data: UncorrectedMisstatementCreateInput,
  ) => Promise<UncorrectedMisstatement | null>;
  onUpdate: (
    misstatementId: number,
    data: UncorrectedMisstatementUpdateInput,
  ) => Promise<UncorrectedMisstatement | null>;
  onArchive: (misstatementId: number) => Promise<boolean>;
  onDownload: () => void;
}

const DISPOSITIONS: MisstatementDisposition[] = [
  'not_yet_reviewed',
  'auditor_proposes_correction',
  'auditor_accepts_as_immaterial',
];

function bucketBoxClasses(bucket: MaterialityBucket): string {
  const tone = BUCKET_TONE[bucket];
  if (tone === 'sage') {
    return 'bg-sage-50 border-sage-300 text-sage-700';
  }
  if (tone === 'clay-soft') {
    return 'bg-clay-50/50 border-clay-200 text-clay-700';
  }
  return 'bg-clay-50 border-clay-300 text-clay-700';
}

function formatSigned(value: number): string {
  if (value === 0) return '$0.00';
  if (value < 0) return `(${formatCurrency(Math.abs(value))})`;
  return formatCurrency(value);
}

export function SumSchedulePanel({
  engagementId,
  schedule,
  isLoading,
  onCreate,
  onUpdate,
  onArchive,
  onDownload,
}: Props) {
  const [showCreate, setShowCreate] = useState(false);
  const [savingId, setSavingId] = useState<number | null>(null);

  const items = schedule?.items ?? [];

  const handleDispositionChange = async (
    id: number,
    disposition: MisstatementDisposition,
  ) => {
    setSavingId(id);
    await onUpdate(id, { cpa_disposition: disposition });
    setSavingId(null);
  };

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h3 className="text-lg font-serif font-semibold text-content-primary">
            Summary of Uncorrected Misstatements
          </h3>
          <p className="text-xs font-sans text-content-tertiary mt-0.5">
            ISA 450 / AU-C 450 workpaper. Capture each identified misstatement, classify it, and record your disposition.
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
            + Add Misstatement
          </button>
        </div>
      </div>

      {/* Bucket + aggregate summary */}
      {schedule && (
        <div
          data-testid="sum-bucket-box"
          className={`border-2 rounded-lg p-4 ${bucketBoxClasses(schedule.bucket)}`}
        >
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
            <div>
              <p className="text-xs font-sans uppercase tracking-wide opacity-80">
                Materiality bucket
              </p>
              <p className="text-2xl font-serif font-semibold mt-0.5">
                {BUCKET_LABELS[schedule.bucket]}
              </p>
              {schedule.bucket === 'material' && (
                <p className="text-xs font-sans mt-2 opacity-90">
                  Aggregate exceeds overall materiality. ISA 450 §11 requires
                  documented disposition (override) before engagement completion.
                </p>
              )}
            </div>
            <div className="grid grid-cols-2 gap-3 text-right">
              <div>
                <p className="text-xs font-sans opacity-70">Net Income</p>
                <p className="text-lg font-mono">
                  {formatSigned(schedule.aggregate.net_income)}
                </p>
              </div>
              <div>
                <p className="text-xs font-sans opacity-70">Net Assets</p>
                <p className="text-lg font-mono">
                  {formatSigned(schedule.aggregate.net_assets)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Materiality cascade reference */}
      {schedule && (
        <div className="grid grid-cols-3 gap-3 text-xs">
          <div className="bg-surface-card border border-theme rounded p-2.5">
            <p className="font-sans text-content-tertiary">Overall</p>
            <p className="font-mono text-content-primary">
              {formatCurrency(schedule.materiality.overall)}
            </p>
          </div>
          <div className="bg-surface-card border border-theme rounded p-2.5">
            <p className="font-sans text-content-tertiary">Performance</p>
            <p className="font-mono text-content-primary">
              {formatCurrency(schedule.materiality.performance)}
            </p>
          </div>
          <div className="bg-surface-card border border-theme rounded p-2.5">
            <p className="font-sans text-content-tertiary">Trivial</p>
            <p className="font-mono text-content-primary">
              {formatCurrency(schedule.materiality.trivial)}
            </p>
          </div>
        </div>
      )}

      {/* Items */}
      {isLoading ? (
        <div className="flex items-center justify-center py-8">
          <div className="w-6 h-6 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
        </div>
      ) : items.length === 0 ? (
        <div className="bg-oatmeal-50 border border-theme rounded-lg p-6 text-center">
          <p className="text-sm font-sans text-content-secondary">
            No uncorrected misstatements recorded yet.
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
                data-testid={`sum-row-${item.id}`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-sans bg-oatmeal-100 text-content-secondary border border-theme">
                        {CLASSIFICATION_LABELS[item.classification]}
                      </span>
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-[10px] font-sans bg-oatmeal-50 text-content-tertiary border border-theme">
                        {SOURCE_TYPE_LABELS[item.source_type]}
                      </span>
                    </div>
                    <p className="text-sm font-sans text-content-primary">
                      {item.description}
                    </p>
                    <p className="text-xs font-sans text-content-tertiary mt-1 italic">
                      {item.source_reference}
                    </p>
                    <div className="grid grid-cols-2 gap-3 mt-2 text-xs">
                      <div>
                        <p className="font-sans text-content-tertiary">Net Income Δ</p>
                        <p className="font-mono text-content-primary">
                          {formatSigned(item.fs_impact_net_income)}
                        </p>
                      </div>
                      <div>
                        <p className="font-sans text-content-tertiary">Net Assets Δ</p>
                        <p className="font-mono text-content-primary">
                          {formatSigned(item.fs_impact_net_assets)}
                        </p>
                      </div>
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => onArchive(item.id)}
                    className="text-xs font-sans text-content-tertiary hover:text-clay-600 transition-colors"
                    aria-label={`Archive misstatement ${item.id}`}
                  >
                    Archive
                  </button>
                </div>

                <div className="mt-3 pt-3 border-t border-theme-divider flex items-center gap-2">
                  <label
                    className="text-xs font-sans text-content-tertiary"
                    htmlFor={`disposition-${item.id}`}
                  >
                    Disposition:
                  </label>
                  <select
                    id={`disposition-${item.id}`}
                    value={item.cpa_disposition}
                    disabled={savingId === item.id}
                    onChange={e =>
                      handleDispositionChange(
                        item.id,
                        e.target.value as MisstatementDisposition,
                      )
                    }
                    className="font-sans text-xs border border-theme rounded px-2 py-1"
                  >
                    {DISPOSITIONS.map(d => (
                      <option key={d} value={d}>
                        {DISPOSITION_LABELS[d]}
                      </option>
                    ))}
                  </select>
                  {item.cpa_notes && (
                    <span className="text-[10px] font-sans text-content-tertiary italic ml-2 truncate">
                      Note: {item.cpa_notes.slice(0, 60)}
                      {item.cpa_notes.length > 60 ? '…' : ''}
                    </span>
                  )}
                </div>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
      )}

      {showCreate && (
        <CreateMisstatementModal
          engagementId={engagementId}
          onClose={() => setShowCreate(false)}
          onCreate={onCreate}
        />
      )}
    </div>
  );
}

