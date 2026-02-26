"use client";

import React, { createContext, useContext, useState, ReactNode } from 'react';
import type {
  DiagnosticResult,
  DiagnosticContextType,
} from '@/types/diagnostic';

// Re-export types for convenience (backwards compatibility)
export { RiskLevel, RiskBand } from '@/types/diagnostic';
export type {
  FluxItem,
  FluxSummary,
  ReconScore,
  ReconStats,
  DiagnosticResult,
} from '@/types/diagnostic';

const DiagnosticContext = createContext<DiagnosticContextType | undefined>(undefined);

export function DiagnosticProvider({ children }: { children: ReactNode }): React.ReactElement {
  const [result, setResultState] = useState<DiagnosticResult | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  // Use sessionStorage to persist across refreshes if needed,
  // but for "Zero-Data" strictly ephemeral (memory only) is safer.
  // We'll stick to React State (memory) to be strictly aligned with "No Storage".
  // Note: Tab refresh will clear data, which is acceptable/desired for security.

  const setResult = (data: DiagnosticResult | null) => {
    setResultState(data);
  };

  const clearResult = () => {
    setResultState(null);
  };

  return (
    <DiagnosticContext.Provider value={{ result, setResult, clearResult, isLoading, setIsLoading }}>
      {children}
    </DiagnosticContext.Provider>
  );
}

export function useDiagnostic(): DiagnosticContextType {
  const context = useContext(DiagnosticContext);
  if (context === undefined) {
    throw new Error('useDiagnostic must be used within a DiagnosticProvider');
  }
  return context;
}
