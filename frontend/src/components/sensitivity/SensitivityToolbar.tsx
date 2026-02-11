'use client';

import { useState, useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { formatCurrencyWhole, parseCurrency } from '@/utils';

/**
 * SensitivityToolbar - Control Surface for Diagnostic Sensitivity Parameters
 *
 * Design: "Control Surface" aesthetic - professional instrument panel
 * - Recessed panel with inner shadow (distinct from data cards)
 * - Obsidian-800 background with subtle border
 * - Sage accents for interactive controls
 * - Smooth display/edit mode transitions
 *
 * Tier 2 Form Validation:
 * - Sage Green border on focus
 * - Clay Red for validation errors
 *
 * Sprint 22: Live Sensitivity Tuning & UI Hardening
 * See: skills/theme-factory/themes/oat-and-obsidian.md
 */

export type DisplayMode = 'strict' | 'lenient';

interface SensitivityToolbarProps {
  threshold: number;
  displayMode: DisplayMode;
  onThresholdChange: (value: number) => void;
  onDisplayModeChange: (mode: DisplayMode) => void;
  disabled?: boolean;
  minThreshold?: number;
  maxThreshold?: number;
}

export function SensitivityToolbar({
  threshold,
  displayMode,
  onThresholdChange,
  onDisplayModeChange,
  disabled = false,
  minThreshold = 0,
  maxThreshold = 10000000,
}: SensitivityToolbarProps) {
  // Edit mode state
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState('');
  const [error, setError] = useState<string | null>(null);

  // Input ref for auto-focus
  const inputRef = useRef<HTMLInputElement>(null);

  // Enter edit mode
  const handleEditClick = useCallback(() => {
    if (disabled) return;
    setEditValue(threshold.toString());
    setError(null);
    setIsEditing(true);
  }, [disabled, threshold]);

  // Auto-focus input when entering edit mode
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  // Validate input
  const validate = useCallback((value: string): string | null => {
    const parsed = parseCurrency(value);

    if (parsed === null) {
      return 'Please enter a valid number';
    }

    if (parsed < minThreshold) {
      return `Minimum threshold is ${formatCurrencyWhole(minThreshold)}`;
    }

    if (parsed > maxThreshold) {
      return `Maximum threshold is ${formatCurrencyWhole(maxThreshold)}`;
    }

    return null;
  }, [minThreshold, maxThreshold]);

  // Handle apply
  const handleApply = useCallback(() => {
    const validationError = validate(editValue);

    if (validationError) {
      setError(validationError);
      return;
    }

    const parsed = parseCurrency(editValue);
    if (parsed !== null) {
      onThresholdChange(parsed);
      setIsEditing(false);
      setError(null);
    }
  }, [editValue, onThresholdChange, validate]);

  // Handle cancel
  const handleCancel = useCallback(() => {
    setIsEditing(false);
    setError(null);
    setEditValue('');
  }, []);

  // Handle input change
  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setEditValue(e.target.value);
    // Clear error on change
    if (error) setError(null);
  };

  // Handle key events
  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleApply();
    } else if (e.key === 'Escape') {
      e.preventDefault();
      handleCancel();
    }
  };

  // Toggle display mode
  const handleDisplayModeToggle = () => {
    if (disabled) return;
    onDisplayModeChange(displayMode === 'strict' ? 'lenient' : 'strict');
  };

  // Get input classes (Tier 2: Form Focus & Validation)
  const getInputClasses = (): string => {
    const baseClasses = 'w-32 px-3 py-2 bg-obsidian-900 rounded-lg text-oatmeal-100 font-mono text-sm transition-all duration-200 outline-none';

    if (error) {
      // Clay Red for errors
      return `${baseClasses} border-2 border-clay-500 focus:border-clay-400 focus:ring-2 focus:ring-clay-500/20`;
    }

    // Default - Sage Green border on focus
    return `${baseClasses} border-2 border-obsidian-600 focus:border-sage-500 focus:ring-2 focus:ring-sage-500/20`;
  };

  // Animation variants
  const containerVariants = {
    initial: { opacity: 0, y: -10 },
    animate: {
      opacity: 1,
      y: 0,
      transition: { duration: 0.3, ease: 'easeOut' as const }
    },
  };

  const editModeVariants = {
    hidden: {
      opacity: 0,
      scale: 0.95,
      transition: { duration: 0.15 }
    },
    visible: {
      opacity: 1,
      scale: 1,
      transition: { duration: 0.2, ease: 'easeOut' as const }
    },
  };

  const displayModeVariants = {
    hidden: {
      opacity: 0,
      transition: { duration: 0.15 }
    },
    visible: {
      opacity: 1,
      transition: { duration: 0.2, ease: 'easeOut' as const }
    },
  };

  return (
    <motion.div
      variants={containerVariants}
      initial="initial"
      animate="animate"
      className={`
        relative flex flex-wrap items-center gap-4 px-5 py-4
        bg-obsidian-800 rounded-xl
        border border-obsidian-600/60
        shadow-[inset_0_2px_4px_0_rgba(0,0,0,0.3)]
        ${disabled ? 'opacity-60 cursor-not-allowed' : ''}
      `}
      role="toolbar"
      aria-label="Sensitivity controls"
    >
      {/* Control Surface Label */}
      <div className="flex items-center gap-2 text-oatmeal-500">
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
            strokeWidth={1.5}
            d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
          />
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={1.5}
            d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
          />
        </svg>
        <span className="text-xs font-sans font-medium uppercase tracking-wider">
          Sensitivity
        </span>
      </div>

      {/* Divider */}
      <div className="hidden sm:block w-px h-6 bg-obsidian-600" aria-hidden="true" />

      {/* Threshold Section */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-sans text-oatmeal-400">
          Current Threshold:
        </span>

        <AnimatePresence mode="wait">
          {isEditing ? (
            <motion.div
              key="edit-mode"
              variants={editModeVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              className="flex items-center gap-2"
            >
              <div className="relative">
                <span className="absolute left-3 top-1/2 -translate-y-1/2 text-oatmeal-500 font-mono text-sm">
                  $
                </span>
                <input
                  ref={inputRef}
                  type="text"
                  value={editValue}
                  onChange={handleInputChange}
                  onKeyDown={handleKeyDown}
                  className={`${getInputClasses()} pl-7`}
                  placeholder="0"
                  aria-label="Threshold amount"
                  aria-invalid={!!error}
                  aria-describedby={error ? 'threshold-error' : undefined}
                />
              </div>

              {/* Apply Button */}
              <motion.button
                type="button"
                onClick={handleApply}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-3 py-2 bg-sage-500 hover:bg-sage-400 text-oatmeal-50 font-sans text-xs font-medium rounded-lg transition-colors"
              >
                Apply
              </motion.button>

              {/* Cancel Button */}
              <motion.button
                type="button"
                onClick={handleCancel}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                className="px-3 py-2 bg-obsidian-700 hover:bg-obsidian-600 text-oatmeal-300 font-sans text-xs font-medium rounded-lg border border-obsidian-500 transition-colors"
              >
                Cancel
              </motion.button>
            </motion.div>
          ) : (
            <motion.div
              key="display-mode"
              variants={displayModeVariants}
              initial="hidden"
              animate="visible"
              exit="hidden"
              className="flex items-center gap-2"
            >
              <span className="font-mono text-lg font-semibold text-oatmeal-100">
                {formatCurrencyWhole(threshold)}
              </span>

              {/* Edit Button */}
              <motion.button
                type="button"
                onClick={handleEditClick}
                disabled={disabled}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-1.5 text-sage-400 hover:text-sage-300 hover:bg-sage-500/10 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Edit threshold"
              >
                <svg
                  className="w-4 h-4"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M15.232 5.232l3.536 3.536m-2.036-5.036a2.5 2.5 0 113.536 3.536L6.5 21.036H3v-3.572L16.732 3.732z"
                  />
                </svg>
              </motion.button>
            </motion.div>
          )}
        </AnimatePresence>
      </div>

      {/* Error Message */}
      <AnimatePresence>
        {error && (
          <motion.div
            initial={{ opacity: 0, y: -5 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -5 }}
            id="threshold-error"
            role="alert"
            className="absolute -bottom-6 left-5 text-xs font-sans text-clay-400 flex items-center gap-1"
          >
            <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
              <path
                fillRule="evenodd"
                d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z"
                clipRule="evenodd"
              />
            </svg>
            {error}
          </motion.div>
        )}
      </AnimatePresence>

      {/* Spacer */}
      <div className="flex-1" />

      {/* Divider */}
      <div className="hidden md:block w-px h-6 bg-obsidian-600" aria-hidden="true" />

      {/* Display Mode Toggle */}
      <div className="flex items-center gap-3">
        <span className="text-sm font-sans text-oatmeal-400">
          Display:
        </span>

        <motion.button
          type="button"
          onClick={handleDisplayModeToggle}
          disabled={disabled}
          whileHover={{ scale: 1.02 }}
          whileTap={{ scale: 0.98 }}
          className={`
            relative flex items-center gap-2 px-4 py-2 rounded-lg
            font-sans text-sm font-medium
            border transition-all duration-200
            ${disabled ? 'cursor-not-allowed' : 'cursor-pointer'}
            ${displayMode === 'strict'
              ? 'bg-sage-500/20 border-sage-500/40 text-sage-300'
              : 'bg-oatmeal-500/10 border-oatmeal-500/30 text-oatmeal-300'
            }
          `}
          aria-pressed={displayMode === 'strict'}
          aria-label={`Display mode: ${displayMode}. Click to toggle.`}
        >
          {/* Mode Indicator Dot */}
          <span
            className={`
              w-2 h-2 rounded-full transition-colors duration-200
              ${displayMode === 'strict' ? 'bg-sage-400' : 'bg-oatmeal-400'}
            `}
            aria-hidden="true"
          />

          {/* Mode Label */}
          <span className="capitalize">
            {displayMode}
          </span>

          {/* Toggle Icon */}
          <svg
            className="w-3.5 h-3.5 text-oatmeal-500"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
            aria-hidden="true"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M8 9l4-4 4 4m0 6l-4 4-4-4"
            />
          </svg>
        </motion.button>
      </div>
    </motion.div>
  );
}

export default SensitivityToolbar;
