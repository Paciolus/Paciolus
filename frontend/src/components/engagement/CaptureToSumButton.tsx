'use client';

/**
 * Sprint 729c — CaptureToSumButton.
 *
 * Renders a button that, when clicked, opens the SUM capture modal
 * pre-filled from an AJE or sampling-projection source. Avoids forcing
 * the auditor to retype the AJE/sample data into the SUM workpaper.
 *
 * Usage:
 *   <CaptureToSumButton
 *     engagementId={123}
 *     prefillFromAdjustingEntry={entry}
 *     onCreated={() => refresh()}
 *   />
 */

import { useState } from 'react';
import { useUncorrectedMisstatements } from '@/hooks/useUncorrectedMisstatements';
import type {
  UncorrectedMisstatement,
  AccountAffected,
} from '@/types/uncorrected-misstatements';
import { CreateMisstatementModal } from './CreateMisstatementModal';
import type { CreateMisstatementInitialValues } from './CreateMisstatementModal';

/**
 * AJE shape we read from. Kept as a structural interface so this
 * component doesn't depend on the AdjustingEntry type module
 * (avoids tight coupling between the engagement layer and the
 * adjustments domain).
 */
interface AdjustingEntryLike {
  reference: string;
  description: string;
  lines: Array<{
    account: string;
    debit: number;
    credit: number;
  }>;
  notes?: string;
}

interface SamplingProjectionLike {
  /** Free-text description of the sampling test (e.g., "Inventory test, n=100"). */
  test_description: string;
  /** Account affected. */
  account: string;
  /** UEL — Upper Error Limit (projected misstatement amount). */
  upper_error_limit: number;
  /** Auditor's tolerable misstatement for the test. */
  tolerable_misstatement: number;
}

interface Props {
  engagementId: number;
  /** AJE to pre-fill from. Mutually exclusive with prefillFromSampleProjection. */
  prefillFromAdjustingEntry?: AdjustingEntryLike;
  /** Sample projection to pre-fill from. Mutually exclusive with prefillFromAdjustingEntry. */
  prefillFromSampleProjection?: SamplingProjectionLike;
  /** Optional callback invoked after successful creation. */
  onCreated?: (m: UncorrectedMisstatement) => void;
  className?: string;
  label?: string;
}

function aJEToInitialValues(entry: AdjustingEntryLike): CreateMisstatementInitialValues {
  // Use the largest line as the canonical "account affected" for the prefill;
  // auditor can edit if the AJE has multiple lines.
  const largestLine = [...entry.lines].sort(
    (a, b) => Math.max(b.debit, b.credit) - Math.max(a.debit, a.credit),
  )[0];

  const acctAmt = Math.max(largestLine?.debit ?? 0, largestLine?.credit ?? 0);
  const acctSide: 'DR' | 'CR' = (largestLine?.debit ?? 0) > (largestLine?.credit ?? 0) ? 'DR' : 'CR';

  return {
    source_type: 'adjusting_entry_passed',
    classification: 'judgmental',
    source_reference: `${entry.reference} — ${entry.description}`.slice(0, 240),
    description: entry.description,
    account_name: largestLine?.account ?? '',
    account_side: acctSide,
    account_amount: acctAmt,
    fs_impact_net_income: 0, // auditor must explicitly fill these
    fs_impact_net_assets: 0,
    cpa_notes: entry.notes ?? '',
  };
}

function projectionToInitialValues(
  proj: SamplingProjectionLike,
): CreateMisstatementInitialValues {
  return {
    source_type: 'sample_projection',
    classification: 'projected',
    source_reference: `${proj.test_description} — UEL: ${proj.upper_error_limit.toLocaleString(
      undefined,
      { style: 'currency', currency: 'USD' },
    )} vs tolerable: ${proj.tolerable_misstatement.toLocaleString(undefined, {
      style: 'currency',
      currency: 'USD',
    })}`.slice(0, 240),
    description: `Projected misstatement from sampling. UEL exceeds tolerable misstatement.`,
    account_name: proj.account,
    account_side: 'DR',
    account_amount: proj.upper_error_limit,
    fs_impact_net_income: 0,
    fs_impact_net_assets: 0,
  };
}

export function CaptureToSumButton({
  engagementId,
  prefillFromAdjustingEntry,
  prefillFromSampleProjection,
  onCreated,
  className,
  label,
}: Props) {
  const [showModal, setShowModal] = useState(false);
  const { createItem } = useUncorrectedMisstatements();

  const initialValues: CreateMisstatementInitialValues | undefined =
    prefillFromAdjustingEntry
      ? aJEToInitialValues(prefillFromAdjustingEntry)
      : prefillFromSampleProjection
        ? projectionToInitialValues(prefillFromSampleProjection)
        : undefined;

  const buttonLabel =
    label ??
    (prefillFromAdjustingEntry
      ? 'Add to SUM'
      : prefillFromSampleProjection
        ? 'Capture as SUM projection'
        : 'Capture to SUM');

  return (
    <>
      <button
        type="button"
        onClick={() => setShowModal(true)}
        className={
          className ??
          'inline-flex items-center gap-1 px-2 py-1 text-xs font-sans text-sage-700 hover:text-sage-800 border border-sage-200 rounded hover:border-sage-300 hover:bg-sage-50 transition-colors'
        }
      >
        {buttonLabel}
      </button>
      {showModal && (
        <CreateMisstatementModal
          engagementId={engagementId}
          initialValues={initialValues}
          onClose={() => setShowModal(false)}
          onCreate={async (engId, data) => {
            const created = await createItem(engId, data);
            if (created && onCreated) onCreated(created);
            return created;
          }}
        />
      )}
    </>
  );
}
