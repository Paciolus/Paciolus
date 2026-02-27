'use client';

/**
 * Paciolus Column Mapping Modal
 * Triggered when backend column detection confidence is below 80%.
 * Allows users to manually select which CSV columns represent Account Name, Debit, and Credit.
 *
 * Zero-Storage Compliance:
 * - Column mappings stored in React state only
 * - Cleared on session termination
 * - Never persisted to localStorage or server
 *
 * Oat & Obsidian Theme Compliance:
 * - Uses obsidian-*, oatmeal-*, sage-*, clay-* tokens only
 * - Headers use font-serif, body uses font-sans
 */

import React, { useState, useEffect } from 'react';
import { useFocusTrap } from '@/hooks';

export interface ColumnMapping {
  account_column: string;
  debit_column: string;
  credit_column: string;
}

export interface ColumnDetectionInfo {
  account_column: string | null;
  debit_column: string | null;
  credit_column: string | null;
  account_confidence: number;
  debit_confidence: number;
  credit_confidence: number;
  overall_confidence: number;
  requires_mapping: boolean;
  all_columns: string[];
  detection_notes: string[];
}

interface ColumnMappingModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: (mapping: ColumnMapping) => void;
  columnDetection: ColumnDetectionInfo;
  filename: string;
}

export function ColumnMappingModal({
  isOpen,
  onClose,
  onConfirm,
  columnDetection,
  filename
}: ColumnMappingModalProps) {
  // Initialize state with detected values (if any)
  const [accountColumn, setAccountColumn] = useState<string>(
    columnDetection.account_column || ''
  );
  const [debitColumn, setDebitColumn] = useState<string>(
    columnDetection.debit_column || ''
  );
  const [creditColumn, setCreditColumn] = useState<string>(
    columnDetection.credit_column || ''
  );
  const focusTrapRef = useFocusTrap(isOpen, onClose);

  // Update state when columnDetection changes
  useEffect(() => {
    setAccountColumn(columnDetection.account_column || '');
    setDebitColumn(columnDetection.debit_column || '');
    setCreditColumn(columnDetection.credit_column || '');
  }, [columnDetection]);

  const handleConfirm = () => {
    if (accountColumn && debitColumn && creditColumn) {
      onConfirm({
        account_column: accountColumn,
        debit_column: debitColumn,
        credit_column: creditColumn,
      });
    }
  };

  const isValid = accountColumn && debitColumn && creditColumn &&
    accountColumn !== debitColumn &&
    accountColumn !== creditColumn &&
    debitColumn !== creditColumn;

  // Format confidence as percentage with color coding
  const getConfidenceDisplay = (confidence: number) => {
    const percentage = Math.round(confidence * 100);
    if (confidence >= 0.8) {
      return <span className="text-sage-400 font-mono">{percentage}%</span>;
    } else if (confidence >= 0.5) {
      return <span className="text-content-primary font-mono">{percentage}%</span>;
    } else {
      return <span className="text-clay-400 font-mono">{percentage}%</span>;
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center">
      {/* Backdrop */}
      <div
        className="absolute inset-0 bg-obsidian-900/80 backdrop-blur-xs"
        onClick={onClose}
        aria-hidden="true"
      />

      {/* Modal */}
      <div
        ref={focusTrapRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby="column-mapping-title"
        className="relative bg-surface-card border border-theme rounded-2xl shadow-2xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto"
      >
        {/* Header */}
        <div className="p-6 border-b border-theme">
          <div className="flex items-center gap-3 mb-2">
            <div className="w-10 h-10 rounded-full bg-clay-500/20 border border-clay-500/40 flex items-center justify-center">
              <svg className="w-5 h-5 text-clay-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <div>
              <h2 id="column-mapping-title" className="text-xl font-serif font-bold text-content-primary">
                Column Mapping Required
              </h2>
              <p className="text-content-secondary text-sm font-sans">
                Confidence: {getConfidenceDisplay(columnDetection.overall_confidence)}
              </p>
            </div>
          </div>
          <p className="text-content-secondary font-sans text-sm mt-3">
            We couldn&apos;t confidently identify all columns in <span className="text-content-primary font-mono">{filename}</span>.
            Please select which columns contain the account data.
          </p>
        </div>

        {/* Detection Notes */}
        {columnDetection.detection_notes.length > 0 && (
          <div className="px-6 py-3 bg-surface-card-secondary border-b border-theme">
            <p className="text-xs text-content-tertiary font-sans font-medium mb-1">Detection Notes:</p>
            <ul className="text-xs text-content-secondary font-sans space-y-0.5">
              {columnDetection.detection_notes.map((note, idx) => (
                <li key={idx} className="flex items-start gap-1">
                  <span className="text-clay-400">•</span>
                  {note}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Column Selection Form */}
        <div className="p-6 space-y-5">
          {/* Account Column */}
          <div>
            <label htmlFor="account-column" className="block text-sm font-sans font-medium text-content-primary mb-2">
              Account Name Column
              <span className="ml-2 text-xs text-content-tertiary">
                (detected: {getConfidenceDisplay(columnDetection.account_confidence)})
              </span>
            </label>
            <select
              id="account-column"
              value={accountColumn}
              onChange={(e) => setAccountColumn(e.target.value)}
              className="w-full px-4 py-3 bg-surface-card-secondary border border-theme rounded-xl text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            >
              <option value="">-- Select Account Column --</option>
              {columnDetection.all_columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                  {col === columnDetection.account_column ? ' (detected)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Debit Column */}
          <div>
            <label htmlFor="debit-column" className="block text-sm font-sans font-medium text-content-primary mb-2">
              Debit Column
              <span className="ml-2 text-xs text-content-tertiary">
                (detected: {getConfidenceDisplay(columnDetection.debit_confidence)})
              </span>
            </label>
            <select
              id="debit-column"
              value={debitColumn}
              onChange={(e) => setDebitColumn(e.target.value)}
              className="w-full px-4 py-3 bg-surface-card-secondary border border-theme rounded-xl text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            >
              <option value="">-- Select Debit Column --</option>
              {columnDetection.all_columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                  {col === columnDetection.debit_column ? ' (detected)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Credit Column */}
          <div>
            <label htmlFor="credit-column" className="block text-sm font-sans font-medium text-content-primary mb-2">
              Credit Column
              <span className="ml-2 text-xs text-content-tertiary">
                (detected: {getConfidenceDisplay(columnDetection.credit_confidence)})
              </span>
            </label>
            <select
              id="credit-column"
              value={creditColumn}
              onChange={(e) => setCreditColumn(e.target.value)}
              className="w-full px-4 py-3 bg-surface-card-secondary border border-theme rounded-xl text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
            >
              <option value="">-- Select Credit Column --</option>
              {columnDetection.all_columns.map((col) => (
                <option key={col} value={col}>
                  {col}
                  {col === columnDetection.credit_column ? ' (detected)' : ''}
                </option>
              ))}
            </select>
          </div>

          {/* Validation Warning */}
          {accountColumn && debitColumn && creditColumn && !isValid && (
            <div className="flex items-center gap-2 p-3 bg-clay-500/10 border border-clay-500/30 rounded-lg">
              <svg className="w-4 h-4 text-clay-400 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
              <span className="text-clay-300 text-sm font-sans">
                Each column must be unique. Please select different columns.
              </span>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-6 border-t border-theme flex gap-3 justify-end">
          <button
            onClick={onClose}
            className="px-5 py-2.5 bg-surface-card-secondary hover:bg-surface-card text-content-primary font-sans font-medium rounded-xl border border-theme transition-colors"
          >
            Cancel
          </button>
          <button
            onClick={handleConfirm}
            disabled={!isValid}
            className="px-5 py-2.5 bg-sage-500 hover:bg-sage-400 text-oatmeal-50 font-sans font-bold rounded-xl transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Confirm Mapping
          </button>
        </div>

        {/* Zero-Storage Badge */}
        <div className="absolute top-4 right-4">
          <div className="flex items-center gap-1 px-2 py-1 bg-sage-500/10 border border-sage-500/30 rounded-full">
            <svg className="w-3 h-3 text-sage-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
            </svg>
            <span className="text-sage-400 text-[10px] font-sans font-medium">Session Only</span>
          </div>
        </div>
      </div>
    </div>
  );
}
