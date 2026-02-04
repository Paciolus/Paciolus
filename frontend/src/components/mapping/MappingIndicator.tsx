'use client';

/**
 * Mapping Indicator Badge
 * Shows whether an account type was auto-detected or manually set
 *
 * Accessibility:
 * - Uses multiple visual cues (not color-only)
 * - Icon + text + border styling
 * - Screen reader announcements
 */

import React from 'react';

interface MappingIndicatorProps {
  isManual: boolean;
  confidence?: number;
  accountName?: string;
}

export function MappingIndicator({ isManual, confidence, accountName }: MappingIndicatorProps) {
  if (isManual) {
    return (
      <>
        <span
          className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px]
            font-sans font-medium rounded-full
            bg-sage-500/20 text-sage-300
            border border-sage-500/40"
        >
          <svg
            className="w-2.5 h-2.5"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
            />
          </svg>
          <span>Manual</span>
        </span>
        {accountName && (
          <span className="sr-only">
            {accountName} has been manually classified
          </span>
        )}
      </>
    );
  }

  // Auto-detected badge with confidence indicator
  const confidenceLabel = confidence !== undefined
    ? confidence >= 0.7 ? 'high' : confidence >= 0.4 ? 'medium' : 'low'
    : null;

  return (
    <>
      <span
        className="inline-flex items-center gap-1 px-1.5 py-0.5 text-[10px]
          font-sans font-medium rounded-full
          bg-obsidian-600 text-oatmeal-400
          border border-obsidian-500"
      >
        <span
          className={`w-1.5 h-1.5 rounded-full ${
            confidenceLabel === 'high' ? 'bg-sage-400' :
            confidenceLabel === 'medium' ? 'bg-oatmeal-400' :
            confidenceLabel === 'low' ? 'bg-clay-400' :
            'bg-obsidian-400'
          }`}
          aria-hidden="true"
        />
        <span>Auto</span>
        {confidenceLabel && (
          <span className="text-[9px] opacity-70">({Math.round((confidence || 0) * 100)}%)</span>
        )}
      </span>
      {accountName && (
        <span className="sr-only">
          {accountName} was auto-detected{confidence !== undefined ? ` with ${Math.round(confidence * 100)}% confidence` : ''}
        </span>
      )}
    </>
  );
}
