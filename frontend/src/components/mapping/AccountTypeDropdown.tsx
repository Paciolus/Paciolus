'use client';

/**
 * Account Type Dropdown Component
 * Allows users to manually override the auto-detected account type
 *
 * Accessibility:
 * - Full keyboard navigation
 * - Screen reader labels
 * - No color-only indicators
 */

import React from 'react';
import { AccountType, ACCOUNT_TYPES, ACCOUNT_TYPE_LABELS } from '@/types/mapping';

interface AccountTypeDropdownProps {
  accountName: string;
  currentType: AccountType;
  isManual: boolean;
  onChange: (type: AccountType) => void;
  disabled?: boolean;
}

export function AccountTypeDropdown({
  accountName,
  currentType,
  isManual,
  onChange,
  disabled = false
}: AccountTypeDropdownProps) {
  return (
    <select
      value={currentType}
      onChange={(e) => onChange(e.target.value as AccountType)}
      disabled={disabled}
      aria-label={`Account type for ${accountName}. Currently ${ACCOUNT_TYPE_LABELS[currentType]}`}
      className={`
        px-2 py-1 text-xs rounded-md border font-sans
        focus:outline-none focus:ring-2 focus:ring-sage-500 focus:border-transparent
        transition-colors cursor-pointer
        ${isManual
          ? 'bg-sage-500/20 border-sage-500/40 text-sage-300'
          : 'bg-surface-card-secondary border-theme text-content-primary'
        }
        ${disabled ? 'opacity-50 cursor-not-allowed' : 'hover:border-theme'}
      `}
    >
      {ACCOUNT_TYPES.map(type => (
        <option key={type} value={type}>
          {ACCOUNT_TYPE_LABELS[type]}
        </option>
      ))}
    </select>
  );
}
