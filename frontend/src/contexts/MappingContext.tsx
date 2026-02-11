'use client';

/**
 * Paciolus Mapping Context
 * Provides state management for account type mappings
 *
 * Zero-Storage Compliance:
 * - Uses sessionStorage (ephemeral, cleared on tab close)
 * - Export to user's local machine as JSON file
 * - Never persisted on server
 *
 * See: logs/dev-log.md for IP documentation
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import {
  AccountType,
  AccountMapping,
  MappingConfig,
  MAPPING_STORAGE_KEY
} from '@/types/mapping';

interface MappingContextValue {
  // State
  mappings: Map<string, AccountMapping>;
  manualMappingCount: number;

  // Actions
  setAccountType: (accountName: string, type: AccountType, detectedType?: AccountType | null) => void;
  clearMapping: (accountName: string) => void;
  clearAllMappings: () => void;
  initializeFromAudit: (abnormalBalances: Array<{ account: string; category?: string; confidence?: number }>) => void;

  // Persistence (Zero-Storage: sessionStorage + file export)
  exportConfig: () => MappingConfig;
  importConfig: (config: MappingConfig) => void;
  downloadConfig: () => void;
  getOverridesForApi: () => Record<string, string>;
}

const MappingContext = createContext<MappingContextValue | null>(null);

export function useMappings() {
  const context = useContext(MappingContext);
  if (!context) {
    throw new Error('useMappings must be used within a MappingProvider');
  }
  return context;
}

interface MappingProviderProps {
  children: React.ReactNode;
}

export function MappingProvider({ children }: MappingProviderProps) {
  const [mappings, setMappings] = useState<Map<string, AccountMapping>>(new Map());

  // Load from sessionStorage on mount
  useEffect(() => {
    try {
      const stored = sessionStorage.getItem(MAPPING_STORAGE_KEY);
      if (stored) {
        const parsed = JSON.parse(stored) as Record<string, AccountMapping>;
        setMappings(new Map(Object.entries(parsed)));
      }
    } catch {
      // Silently ignore invalid stored data
    }
  }, []);

  // Persist to sessionStorage when mappings change
  useEffect(() => {
    if (mappings.size > 0) {
      const obj = Object.fromEntries(mappings);
      sessionStorage.setItem(MAPPING_STORAGE_KEY, JSON.stringify(obj));
    } else {
      sessionStorage.removeItem(MAPPING_STORAGE_KEY);
    }
  }, [mappings]);

  // Count manual mappings
  const manualMappingCount = Array.from(mappings.values()).filter(m => m.isManual).length;

  // Set account type (manual override)
  const setAccountType = useCallback((
    accountName: string,
    type: AccountType,
    detectedType?: AccountType | null
  ) => {
    setMappings(prev => {
      const newMap = new Map(prev);
      const existing = prev.get(accountName);
      newMap.set(accountName, {
        accountName,
        detectedType: detectedType ?? existing?.detectedType ?? null,
        overrideType: type,
        confidence: 1.0,
        isManual: true
      });
      return newMap;
    });
  }, []);

  // Clear a single mapping override
  const clearMapping = useCallback((accountName: string) => {
    setMappings(prev => {
      const newMap = new Map(prev);
      const existing = prev.get(accountName);
      if (existing) {
        // Reset to auto-detected
        newMap.set(accountName, {
          ...existing,
          overrideType: null,
          isManual: false
        });
      }
      return newMap;
    });
  }, []);

  // Clear all manual overrides
  const clearAllMappings = useCallback(() => {
    setMappings(prev => {
      const newMap = new Map();
      // Keep detected types, remove overrides
      prev.forEach((value, key) => {
        newMap.set(key, {
          ...value,
          overrideType: null,
          isManual: false
        });
      });
      return newMap;
    });
  }, []);

  // Initialize mappings from audit result
  const initializeFromAudit = useCallback((
    abnormalBalances: Array<{ account: string; category?: string; confidence?: number }>
  ) => {
    setMappings(prev => {
      const newMap = new Map(prev);
      abnormalBalances.forEach(ab => {
        const existing = prev.get(ab.account);
        // Only update if not manually overridden
        if (!existing?.isManual) {
          newMap.set(ab.account, {
            accountName: ab.account,
            detectedType: (ab.category as AccountType) ?? null,
            overrideType: existing?.overrideType ?? null,
            confidence: ab.confidence ?? 0,
            isManual: existing?.isManual ?? false
          });
        }
      });
      return newMap;
    });
  }, []);

  // Export configuration to JSON
  const exportConfig = useCallback((): MappingConfig => {
    const overrides: Record<string, AccountType> = {};
    mappings.forEach((value, key) => {
      if (value.isManual && value.overrideType) {
        overrides[key] = value.overrideType;
      }
    });
    return {
      version: '1.0',
      createdAt: new Date().toISOString(),
      mappings: overrides
    };
  }, [mappings]);

  // Import configuration from JSON
  const importConfig = useCallback((config: MappingConfig) => {
    if (!config.mappings) return;

    setMappings(prev => {
      const newMap = new Map(prev);
      Object.entries(config.mappings).forEach(([accountName, type]) => {
        const existing = prev.get(accountName);
        newMap.set(accountName, {
          accountName,
          detectedType: existing?.detectedType ?? null,
          overrideType: type as AccountType,
          confidence: 1.0,
          isManual: true
        });
      });
      return newMap;
    });
  }, []);

  // Download config as JSON file (user's local machine)
  const downloadConfig = useCallback(() => {
    const config = exportConfig();
    const blob = new Blob([JSON.stringify(config, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `paciolus-mappings-${new Date().toISOString().slice(0, 10)}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }, [exportConfig]);

  // Get overrides formatted for API call
  const getOverridesForApi = useCallback((): Record<string, string> => {
    const overrides: Record<string, string> = {};
    mappings.forEach((value, key) => {
      if (value.isManual && value.overrideType) {
        overrides[key] = value.overrideType;
      }
    });
    return overrides;
  }, [mappings]);

  const value: MappingContextValue = {
    mappings,
    manualMappingCount,
    setAccountType,
    clearMapping,
    clearAllMappings,
    initializeFromAudit,
    exportConfig,
    importConfig,
    downloadConfig,
    getOverridesForApi
  };

  return (
    <MappingContext.Provider value={value}>
      {children}
    </MappingContext.Provider>
  );
}
