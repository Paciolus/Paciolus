'use client';

import React, { useMemo } from 'react';

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
  /** Optional: Total TB population (gross debits) for dynamic range calculation */
  totalPopulation?: number;
}

/**
 * MaterialityControl - Reusable materiality threshold input component.
 *
 * Sprint 25: Extracted from page.tsx to eliminate duplicate code
 * Sprint 525: Dynamic range based on TB population (0.5% recommended, 2% max)
 *
 * Features:
 * - Numerical input with dollar prefix
 * - Dynamic range slider based on TB population
 * - Tooltip explaining materiality concept
 * - Optional live update indicator
 * - Recommended materiality marker (0.5% of total TB value)
 */
export function MaterialityControl({
  idPrefix = 'materiality',
  value,
  onChange,
  showLiveIndicator = false,
  filename,
  totalPopulation,
}: MaterialityControlProps) {
  const inputId = `${idPrefix}-threshold`;
  const descriptionId = `${idPrefix}-threshold-description`;

  // Dynamic range calculation based on TB population
  const { sliderMax, sliderStep, recommended, midLabel } = useMemo(() => {
    if (totalPopulation && totalPopulation > 0) {
      const rec = Math.round((totalPopulation * 0.005) / 1000) * 1000; // 0.5%, rounded to nearest $1,000
      const max = Math.round((totalPopulation * 0.02) / 1000) * 1000;  // 2% of TB
      const safeMax = Math.max(max, 10000); // Ensure a reasonable minimum range
      const step = safeMax <= 50000 ? 500 : safeMax <= 500000 ? 1000 : 5000;
      const mid = Math.round(safeMax / 2 / 1000) * 1000;
      return {
        sliderMax: safeMax,
        sliderStep: step,
        recommended: Math.max(rec, 500), // Floor at $500
        midLabel: `$${mid.toLocaleString()}`,
      };
    }
    // Static defaults when no file is loaded
    return {
      sliderMax: 500000,
      sliderStep: 1000,
      recommended: 0,
      midLabel: '$250,000',
    };
  }, [totalPopulation]);

  return (
    <div className="card mb-6">
      <div className="flex items-center gap-2 mb-4">
        <label
          htmlFor={inputId}
          className="text-content-primary font-sans font-medium"
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
              Balances below this dollar amount are classified as below
              materiality threshold and won&apos;t trigger high-priority
              alerts. This helps reduce alert fatigue on large trial balances.
            </p>
            <div className="absolute top-full left-1/2 -translate-x-1/2 border-8 border-transparent border-t-obsidian-500"></div>
          </div>
        </div>
      </div>

      <div className="flex flex-col sm:flex-row items-center gap-4">
        {/* Numerical Input */}
        <div className="flex items-center gap-2">
          <span className="text-content-secondary">$</span>
          <input
            id={inputId}
            type="number"
            min="0"
            step={sliderStep}
            value={value}
            onChange={(e) => onChange(Math.max(0, Number(e.target.value)))}
            aria-describedby={descriptionId}
            className="w-32 px-3 py-2 bg-surface-card border border-theme rounded-lg text-content-primary text-right font-mono focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
          />
        </div>

        {/* Slider */}
        <div className="flex-1 w-full">
          <div className="relative">
            <input
              type="range"
              min="0"
              max={sliderMax}
              step={sliderStep}
              value={Math.min(value, sliderMax)}
              onChange={(e) => onChange(Number(e.target.value))}
              aria-label={`Materiality threshold slider, current value $${value.toLocaleString()}`}
              className="w-full h-2 bg-surface-card-secondary rounded-lg appearance-none cursor-pointer accent-sage-500"
            />
            {/* Recommended materiality marker */}
            {recommended > 0 && (
              <div
                className="absolute top-full mt-0.5 -translate-x-1/2 pointer-events-none"
                style={{ left: `${(recommended / sliderMax) * 100}%` }}
              >
                <div className="w-0.5 h-2 bg-sage-500 mx-auto" />
                <span className="text-sage-600 text-[10px] font-sans whitespace-nowrap">
                  Rec: ${recommended.toLocaleString()}
                </span>
              </div>
            )}
          </div>
          <div className={`flex justify-between text-xs text-content-tertiary font-sans ${recommended > 0 ? 'mt-5' : 'mt-1'}`}>
            <span>$0</span>
            <span>{midLabel}</span>
            <span>${sliderMax.toLocaleString()}</span>
          </div>
        </div>
      </div>

      <p
        id={descriptionId}
        className="text-content-tertiary text-sm font-sans mt-3"
      >
        Current: Balances under{' '}
        <span className="text-content-primary font-mono">
          ${value.toLocaleString()}
        </span>{' '}
        will be classified as below materiality threshold
      </p>

      {/* Live update indicator when file is loaded */}
      {showLiveIndicator && (
        <div className="flex items-center gap-2 mt-3 text-xs font-sans">
          <div className="w-2 h-2 bg-sage-400 rounded-full animate-pulse"></div>
          <span className="text-sage-400">
            Live: Adjusting threshold will automatically recalculate
          </span>
          {filename && <span className="text-content-tertiary">({filename})</span>}
        </div>
      )}
    </div>
  );
}

export default MaterialityControl;
