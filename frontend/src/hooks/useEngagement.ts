/**
 * Paciolus useEngagement Hook
 * Sprint 98: Engagement Workspace
 *
 * CRUD hook for engagement management, following useClients pattern.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Engagement data fetched from API, stored in React state only
 * - No financial data — metadata only
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiGet, apiPost, apiPut, apiDelete, isAuthError } from '@/utils';
import type {
  Engagement,
  EngagementCreateInput,
  EngagementUpdateInput,
  EngagementListResponse,
  ToolRun,
  MaterialityCascade,
} from '@/types/engagement';

interface UseEngagementOptions {
  /** Auto-fetch engagements on mount (default: true) */
  autoFetch?: boolean;
  /** Page size for pagination (default: 50) */
  pageSize?: number;
}

export interface UseEngagementReturn {
  engagements: Engagement[];
  totalCount: number;
  page: number;
  isLoading: boolean;
  error: string | null;
  fetchEngagements: (clientId?: number, status?: string, page?: number) => Promise<void>;
  createEngagement: (data: EngagementCreateInput) => Promise<Engagement | null>;
  updateEngagement: (id: number, data: EngagementUpdateInput) => Promise<Engagement | null>;
  archiveEngagement: (id: number) => Promise<boolean>;
  getEngagement: (id: number) => Promise<Engagement | null>;
  getMateriality: (id: number) => Promise<MaterialityCascade | null>;
  getToolRuns: (id: number) => Promise<ToolRun[]>;
  refresh: () => Promise<void>;
}

export function useEngagement(options: UseEngagementOptions = {}): UseEngagementReturn {
  const { autoFetch = true, pageSize = 50 } = options;
  const { token, isAuthenticated } = useAuth();

  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchEngagements = useCallback(async (
    clientId?: number,
    status?: string,
    newPage: number = 1,
  ) => {
    if (!isAuthenticated || !token) {
      setEngagements([]);
      setTotalCount(0);
      return;
    }

    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams({
      page: newPage.toString(),
      page_size: pageSize.toString(),
    });

    if (clientId) {
      params.append('client_id', clientId.toString());
    }
    if (status) {
      params.append('status', status);
    }

    const { data, error: apiError, ok, status: httpStatus } = await apiGet<EngagementListResponse>(
      `/engagements?${params}`,
      token,
      { skipCache: true },
    );

    if (!ok) {
      if (isAuthError(httpStatus)) {
        setError('Session expired. Please log in again.');
        setEngagements([]);
      } else {
        setError(apiError || 'Failed to fetch workspaces');
      }
      setIsLoading(false);
      return;
    }

    if (data) {
      setEngagements(data.engagements);
      setTotalCount(data.total_count);
      setPage(data.page);
    }

    setIsLoading(false);
  }, [isAuthenticated, token, pageSize]);

  const createEngagement = useCallback(async (
    data: EngagementCreateInput,
  ): Promise<Engagement | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setIsLoading(true);
    setError(null);

    const { data: newEngagement, error: apiError, ok } = await apiPost<Engagement>(
      '/engagements',
      token,
      data,
    );

    if (!ok || !newEngagement) {
      setError(apiError || 'Failed to create workspace');
      setIsLoading(false);
      return null;
    }

    setEngagements(prev => [newEngagement, ...prev]);
    setTotalCount(prev => prev + 1);
    setIsLoading(false);

    return newEngagement;
  }, [isAuthenticated, token]);

  const updateEngagement = useCallback(async (
    id: number,
    data: EngagementUpdateInput,
  ): Promise<Engagement | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setIsLoading(true);
    setError(null);

    const { data: updated, error: apiError, ok } = await apiPut<Engagement>(
      `/engagements/${id}`,
      token,
      data,
    );

    if (!ok || !updated) {
      setError(apiError || 'Failed to update workspace');
      setIsLoading(false);
      return null;
    }

    setEngagements(prev => prev.map(e => e.id === id ? updated : e));
    setIsLoading(false);

    return updated;
  }, [isAuthenticated, token]);

  const archiveEngagement = useCallback(async (id: number): Promise<boolean> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return false;
    }

    setIsLoading(true);
    setError(null);

    const { error: apiError, ok } = await apiDelete(`/engagements/${id}`, token);

    if (!ok) {
      setError(apiError || 'Failed to archive workspace');
      setIsLoading(false);
      return false;
    }

    setEngagements(prev => prev.map(e =>
      e.id === id ? { ...e, status: 'archived' as const } : e
    ));
    setIsLoading(false);

    return true;
  }, [isAuthenticated, token]);

  const getEngagement = useCallback(async (id: number): Promise<Engagement | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    const { data, ok } = await apiGet<Engagement>(`/engagements/${id}`, token);

    if (!ok || !data) {
      return null;
    }

    return data;
  }, [isAuthenticated, token]);

  const getMateriality = useCallback(async (id: number): Promise<MaterialityCascade | null> => {
    if (!isAuthenticated || !token) {
      return null;
    }

    const { data, ok } = await apiGet<MaterialityCascade>(
      `/engagements/${id}/materiality`,
      token,
    );

    if (!ok || !data) {
      return null;
    }

    return data;
  }, [isAuthenticated, token]);

  const getToolRuns = useCallback(async (id: number): Promise<ToolRun[]> => {
    if (!isAuthenticated || !token) {
      return [];
    }

    const { data, ok } = await apiGet<ToolRun[]>(
      `/engagements/${id}/tool-runs`,
      token,
      { skipCache: true },
    );

    if (!ok || !data) {
      return [];
    }

    return data;
  }, [isAuthenticated, token]);

  const refresh = useCallback(async () => {
    await fetchEngagements(undefined, undefined, page);
  }, [fetchEngagements, page]);

  // Auto-fetch on mount and auth changes
  useEffect(() => {
    if (autoFetch && isAuthenticated) {
      fetchEngagements();
    } else if (!isAuthenticated) {
      setEngagements([]);
      setTotalCount(0);
      setError(null);
    }
  }, [autoFetch, isAuthenticated, fetchEngagements]);

  return {
    engagements,
    totalCount,
    page,
    isLoading,
    error,
    fetchEngagements,
    createEngagement,
    updateEngagement,
    archiveEngagement,
    getEngagement,
    getMateriality,
    getToolRuns,
    refresh,
  };
}
