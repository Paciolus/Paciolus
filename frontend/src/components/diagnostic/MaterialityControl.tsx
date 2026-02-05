'use client';

import React from 'react';

interface MaterialityControlProps {
  /** Unique ID prefix for form elements (e.g., "guest" or "workspace") */
  idPrefix?: string;
  /** Current materiality threshold value */
  value: number;
  /** Callback when threshold changes */
  onChange: (value: number) => void;
  /** Optional: Show live update indicator when file is loaded */
  showLiveIndicator?: boolean;
  /** Optional: Filename to show in live indicator */
  filename?: string;
}

/**
 * MaterialityControl - Reusable materiality threshold input component.
 *
 * Sprint 25: Extracted from page.tsx to eliminate duplicate code
 * between guest and authenticated views.
 *
 * Features:
 * - Numerical input with dollar prefix
 * - Range slider (0 to $10,000)
 * - Tooltip explaining materiality concept
 * - Optional live update indicator
 */
export function MaterialityControl({
  idPrefix = 'materiality',
  value,
  onChange,
  showLiveIndicator = false,
  filename,
}: MaterialityControlProps) {
  const inputId = `${idPrefix}-threshold`;
  const descriptionId = `${idPrefix}-threshold-description`;

  return (
    <div className="card mb-6">
      <div className="flex items-center gap-2 mb-4">
        <label
          htmlFor={inputId}
          className="text-oatmeal-200 font-sans font-medium"
        >
          Materiality Threshold
        </label>
        {/* Tooltip */}
        <div className="relative group">
          <button
            type="button"
            aria-label="What is materiality threshold?"
            className="w-5 h-5 rounded-full bg-obsidian-500 text-oatmeal-300 text-xs flex items-center justify-center hover:bg-obsidian-400 transition-colors"
          >
            ?
          </button>
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 px-3 py-2 bg-obsidian-900 border border-obsidian-500 rounded-lg text-sm text-oatmeal-300 w-64 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10">
            <p className="font-sans font-medium text-oatmeal-200 mb-1">
              What is Materiality?
            </p>
            <p className="font-sans">
              Balances below this dollar amount are considered
              &quot;Indistinct&quot; and won&apos;t trigger high-priority
              alerts. This helps reduce alert fatigue on large trial balances.
            </p>
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-obsidian-500"></div>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-4">
        {/* Numerical Input */}
        <div className="flex items-center gap-2">
          <span className="text-oatmeal-400">$</span>
          <input
            id={inputId}
            type="number"
            min="0"
            step="100"
            value={value}
            onChange={(e) => onChange(Math.max(0, Number(e.target.value)))}
            aria-describedby={descriptionId}
            className="w-28 px-3 py-2 bg-obsidian-800 border border-obsidian-500 rounded-lg text-oatmeal-200 text-right font-mono focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent"
          />
        </div>

        {/* Slider */}
        <div className="flex-1 w-full">
          <input
            type="range"
            min="0"
            max="10000"
            step="100"
            value={value}
            onChange={(e) => onChange(Number(e.target.value))}
            aria-label={`Materiality threshold slider, current value $${value}`}
            className="w-full h-2 bg-obsidian-600 rounded-lg appearance-none cursor-pointer accent-sage-500"
          />
          <div className="flex justify-between text-xs text-oatmeal-500 mt-1 font-sans">
            <span>$0</span>
            <span>$5,000</span>
            <span>$10,000</span>
          </div>
        </div>
      </div>

      <p
        id={descriptionId}
        className="text-oatmeal-500 text-sm font-sans mt-3"
      >
        Current: Balances under{' '}
        <span className="text-oatmeal-200 font-mono">
          ${value.toLocaleString()}
        </span>{' '}
        will be marked as Indistinct
      </p>

      {/* Live update indicator when file is loaded */}
      {showLiveIndicator && (
        <div className="flex items-center gap-2 mt-3 text-xs font-sans">
          <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse"></div>
          <span className="text-sage-400">
            Live: Adjusting threshold will automatically recalculate
          </span>
          {filename && <span className="text-oatmeal-500">({filename})</span>}
        </div>
      )}
    </div>
  );
}

export default MaterialityControl;
