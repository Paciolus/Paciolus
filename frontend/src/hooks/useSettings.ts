/**
 * useSettings Hook
 * Sprint 21: Customization & Practice Settings
 * Phase 1 Refactor: Using shared API client utilities
 *
 * React hook for managing practice and client settings.
 */

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiGet, apiPost, apiPut, isAuthError } from '@/utils';
import type {
  PracticeSettings,
  ClientSettings,
  MaterialityFormula,
  MaterialityPreview,
  ResolvedMateriality,
} from '@/types/settings';

export interface UseSettingsReturn {
  practiceSettings: PracticeSettings | null;
  isLoading: boolean;
  error: string | null;
  fetchPracticeSettings: () => Promise<void>;
  updatePracticeSettings: (updates: Partial<PracticeSettings>) => Promise<boolean>;
  fetchClientSettings: (clientId: number) => Promise<ClientSettings | null>;
  updateClientSettings: (clientId: number, updates: Partial<ClientSettings>) => Promise<boolean>;
  previewMateriality: (formula: MaterialityFormula, totalRevenue?: number, totalAssets?: number, totalEquity?: number) => Promise<MaterialityPreview | null>;
  resolveMateriality: (clientId?: number, sessionThreshold?: number) => Promise<ResolvedMateriality | null>;
}

export function useSettings(): UseSettingsReturn {
  const { token, isAuthenticated } = useAuth();
  const [practiceSettings, setPracticeSettings] = useState<PracticeSettings | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch practice settings
  const fetchPracticeSettings = useCallback(async () => {
    if (!isAuthenticated || !token) return;

    setIsLoading(true);
    setError(null);

    const { data, ok, error: apiError, status } = await apiGet<PracticeSettings>(
      '/settings/practice',
      token
    );

    if (ok && data) {
      setPracticeSettings(data);
    } else if (status && isAuthError(status)) {
      setError('Session expired. Please log in again.');
    } else {
      setError(apiError || 'Failed to fetch settings');
    }

    setIsLoading(false);
  }, [isAuthenticated, token]);

  // Update practice settings
  const updatePracticeSettings = useCallback(async (
    updates: Partial<PracticeSettings>
  ): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    setIsLoading(true);
    setError(null);

    const { data, ok, error: apiError, status } = await apiPut<PracticeSettings>(
      '/settings/practice',
      token,
      updates as Record<string, unknown>
    );

    if (ok && data) {
      setPracticeSettings(data);
      setIsLoading(false);
      return true;
    }

    if (status && isAuthError(status)) {
      setError('Session expired. Please log in again.');
    } else {
      setError(apiError || 'Failed to update settings');
    }
    setIsLoading(false);
    return false;
  }, [isAuthenticated, token]);

  // Fetch client settings
  const fetchClientSettings = useCallback(async (
    clientId: number
  ): Promise<ClientSettings | null> => {
    if (!isAuthenticated || !token) return null;

    const { data, ok, error: apiError, status } = await apiGet<ClientSettings>(
      `/clients/${clientId}/settings`,
      token
    );

    if (ok && data) return data;
    if (status && isAuthError(status)) {
      setError('Session expired. Please log in again.');
    } else {
      setError(apiError || 'Failed to fetch client settings');
    }
    return null;
  }, [isAuthenticated, token]);

  // Update client settings
  const updateClientSettings = useCallback(async (
    clientId: number,
    updates: Partial<ClientSettings>
  ): Promise<boolean> => {
    if (!isAuthenticated || !token) return false;

    const { ok, error: apiError, status } = await apiPut(
      `/clients/${clientId}/settings`,
      token,
      updates as Record<string, unknown>
    );

    if (!ok) {
      if (status && isAuthError(status)) {
        setError('Session expired. Please log in again.');
      } else {
        setError(apiError || 'Failed to update client settings');
      }
    }
    return ok;
  }, [isAuthenticated, token]);

  // Preview materiality calculation
  const previewMateriality = useCallback(async (
    formula: MaterialityFormula,
    totalRevenue: number = 0,
    totalAssets: number = 0,
    totalEquity: number = 0
  ): Promise<MaterialityPreview | null> => {
    if (!isAuthenticated || !token) return null;

    const { data, ok, error: apiError, status } = await apiPost<MaterialityPreview>(
      '/settings/materiality/preview',
      token,
      {
        formula,
        total_revenue: totalRevenue,
        total_assets: totalAssets,
        total_equity: totalEquity,
      }
    );

    if (ok && data) return data;
    if (status && isAuthError(status)) {
      setError('Session expired. Please log in again.');
    } else {
      setError(apiError || 'Failed to preview materiality');
    }
    return null;
  }, [isAuthenticated, token]);

  // Resolve materiality for a client or practice
  const resolveMateriality = useCallback(async (
    clientId?: number,
    sessionThreshold?: number
  ): Promise<ResolvedMateriality | null> => {
    if (!isAuthenticated || !token) return null;

    const params = new URLSearchParams();
    if (clientId) params.set('client_id', clientId.toString());
    if (sessionThreshold !== undefined) params.set('session_threshold', sessionThreshold.toString());

    const { data, ok, error: apiError, status } = await apiGet<ResolvedMateriality>(
      `/settings/materiality/resolve?${params.toString()}`,
      token
    );

    if (ok && data) return data;
    if (status && isAuthError(status)) {
      setError('Session expired. Please log in again.');
    } else {
      setError(apiError || 'Failed to resolve materiality');
    }
    return null;
  }, [isAuthenticated, token]);

  // Fetch settings on mount
  useEffect(() => {
    if (isAuthenticated) {
      fetchPracticeSettings();
    }
  }, [isAuthenticated, fetchPracticeSettings]);

  return {
    practiceSettings,
    isLoading,
    error,
    fetchPracticeSettings,
    updatePracticeSettings,
    fetchClientSettings,
    updateClientSettings,
    previewMateriality,
    resolveMateriality,
  };
}
