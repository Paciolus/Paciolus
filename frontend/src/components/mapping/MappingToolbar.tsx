'use client';

/**
 * Mapping Toolbar Component
 * Provides export/import/clear functionality for account mappings
 *
 * Zero-Storage Compliance:
 * - Export saves to user's local machine
 * - Import reads from user's local file
 * - No server-side persistence
 */

import React, { useRef, useState } from 'react';
import { useMappings } from '@/contexts/MappingContext';
import { MappingConfig } from '@/types/mapping';

interface MappingToolbarProps {
  onRerunAudit?: () => void;
  disabled?: boolean;
}

export function MappingToolbar({ onRerunAudit, disabled = false }: MappingToolbarProps) {
  const {
    manualMappingCount,
    downloadConfig,
    importConfig,
    clearAllMappings
  } = useMappings();

  const fileInputRef = useRef<HTMLInputElement>(null);
  const [showClearConfirm, setShowClearConfirm] = useState(false);

  const handleImportClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      const text = await file.text();
      const config = JSON.parse(text) as MappingConfig;

      if (!config.mappings || typeof config.mappings !== 'object') {
        throw new Error('Invalid mapping configuration');
      }

      importConfig(config);

      // Re-run audit with new mappings if callback provided
      if (onRerunAudit) {
        onRerunAudit();
      }
    } catch (error) {
      console.error('Failed to import mappings:', error);
      // Could add toast notification here
    }

    // Reset file input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleClearAll = () => {
    if (manualMappingCount === 0) return;
    setShowClearConfirm(true);
  };

  const confirmClear = () => {
    clearAllMappings();
    setShowClearConfirm(false);
    if (onRerunAudit) {
      onRerunAudit();
    }
  };

  return (
    <div className="flex flex-wrap items-center gap-2 p-3 bg-surface-card-secondary border border-theme rounded-lg">
      {/* Hidden file input for import */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".json"
        onChange={handleFileChange}
        className="hidden"
        aria-label="Import mappings file"
      />

      {/* Mapping count */}
      <div className="flex items-center gap-2 text-sm text-content-secondary font-sans">
        <svg
          className="w-4 h-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
          aria-hidden="true"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <span>
          {manualMappingCount === 0
            ? 'No manual mappings'
            : `${manualMappingCount} manual mapping${manualMappingCount === 1 ? '' : 's'}`
          }
        </span>
      </div>

      <div className="flex-1" />

      {/* Action buttons */}
      <div className="flex items-center gap-2">
        {/* Import button */}
        <button
          onClick={handleImportClick}
          disabled={disabled}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs
            bg-surface-card hover:bg-surface-card-secondary
            text-content-primary font-sans font-medium rounded-md
            border border-theme
            transition-colors
            focus:outline-hidden focus:ring-2 focus:ring-obsidian-400 focus:ring-offset-2 focus:ring-offset-surface-page
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-8l-4-4m0 0L8 8m4-4v12"
            />
          </svg>
          Import
        </button>

        {/* Export button */}
        <button
          onClick={downloadConfig}
          disabled={disabled || manualMappingCount === 0}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs
            bg-sage-500/20 hover:bg-sage-500/30
            text-sage-300 font-sans font-medium rounded-md
            border border-sage-500/40
            transition-colors
            focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:ring-offset-2 focus:ring-offset-surface-page
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4"
            />
          </svg>
          Export
        </button>

        {/* Clear button */}
        <button
          onClick={handleClearAll}
          disabled={disabled || manualMappingCount === 0}
          className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs
            bg-clay-500/10 hover:bg-clay-500/20
            text-clay-400 font-sans font-medium rounded-md
            border border-clay-500/30
            transition-colors
            focus:outline-hidden focus:ring-2 focus:ring-clay-500 focus:ring-offset-2 focus:ring-offset-surface-page
            disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <svg
            className="w-3.5 h-3.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16"
            />
          </svg>
          Clear
        </button>
      </div>

      {showClearConfirm && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            role="button"
            tabIndex={-1}
            className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-xs"
            onClick={() => setShowClearConfirm(false)}
            onKeyDown={(e) => { if (e.key === 'Escape') setShowClearConfirm(false); }}
          />
          <div className="relative bg-surface-card rounded-2xl border border-theme shadow-theme-elevated w-full max-w-sm p-6">
            <div className="flex items-center gap-3 mb-4">
              <div className="w-10 h-10 rounded-full bg-clay-50 flex items-center justify-center">
                <svg className="w-5 h-5 text-clay-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <div>
                <h3 className="text-lg font-serif font-semibold text-content-primary">Clear Mappings</h3>
                <p className="text-content-tertiary text-sm font-sans">This action cannot be undone</p>
              </div>
            </div>
            <p className="text-content-secondary font-sans mb-6">
              Clear all <span className="font-semibold font-mono text-content-primary">{manualMappingCount}</span> manual mapping{manualMappingCount === 1 ? '' : 's'}? The audit will re-run with auto-detected mappings.
            </p>
            <div className="flex gap-3">
              <button
                onClick={() => setShowClearConfirm(false)}
                className="flex-1 px-4 py-2.5 bg-surface-card-secondary hover:bg-surface-card border border-theme text-content-primary font-sans font-medium rounded-lg transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={confirmClear}
                className="flex-1 px-4 py-2.5 bg-clay-600 hover:bg-clay-700 text-oatmeal-50 font-sans font-medium rounded-lg transition-colors"
              >
                Clear All
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
