/**
 * Sprint 729b — useUncorrectedMisstatements hook (ISA 450).
 *
 * Provides CRUD + the SUM-schedule aggregation endpoint.
 */

'use client';

import { useState, useCallback } from 'react';
import { useAuthSession } from '@/contexts/AuthSessionContext';
import type {
  UncorrectedMisstatement,
  UncorrectedMisstatementCreateInput,
  UncorrectedMisstatementUpdateInput,
  SumScheduleResponse,
} from '@/types/uncorrected-misstatements';
import { apiGet, apiPost, apiPatch, apiDelete } from '@/utils';

export interface UseUncorrectedMisstatementsReturn {
  items: UncorrectedMisstatement[];
  schedule: SumScheduleResponse | null;
  isLoading: boolean;
  error: string | null;
  fetchSchedule: (engagementId: number) => Promise<void>;
  createItem: (
    engagementId: number,
    data: UncorrectedMisstatementCreateInput,
  ) => Promise<UncorrectedMisstatement | null>;
  updateItem: (
    misstatementId: number,
    data: UncorrectedMisstatementUpdateInput,
  ) => Promise<UncorrectedMisstatement | null>;
  archiveItem: (misstatementId: number) => Promise<boolean>;
}

export function useUncorrectedMisstatements(): UseUncorrectedMisstatementsReturn {
  const { token, isAuthenticated } = useAuthSession();
  const [schedule, setSchedule] = useState<SumScheduleResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const fetchSchedule = useCallback(
    async (engagementId: number) => {
      if (!isAuthenticated || !token) {
        setSchedule(null);
        return;
      }
      setIsLoading(true);
      setError(null);
      const { data, error: apiError, ok } = await apiGet<SumScheduleResponse>(
        `/engagements/${engagementId}/sum-schedule`,
        token,
        { skipCache: true },
      );
      if (!ok) {
        setError(apiError || 'Failed to load SUM schedule');
        setSchedule(null);
      } else if (data) {
        setSchedule(data);
      }
      setIsLoading(false);
    },
    [token, isAuthenticated],
  );

  const createItem = useCallback(
    async (
      engagementId: number,
      data: UncorrectedMisstatementCreateInput,
    ): Promise<UncorrectedMisstatement | null> => {
      if (!token) return null;
      const { data: created, error: apiError, ok } = await apiPost<UncorrectedMisstatement>(
        `/engagements/${engagementId}/uncorrected-misstatements`,
        token,
        data,
      );
      if (!ok) {
        setError(apiError || 'Failed to create misstatement');
        return null;
      }
      // Re-fetch the schedule so aggregates and bucket update
      await fetchSchedule(engagementId);
      return created ?? null;
    },
    [token, fetchSchedule],
  );

  const updateItem = useCallback(
    async (
      misstatementId: number,
      data: UncorrectedMisstatementUpdateInput,
    ): Promise<UncorrectedMisstatement | null> => {
      if (!token) return null;
      const { data: updated, error: apiError, ok } = await apiPatch<UncorrectedMisstatement>(
        `/uncorrected-misstatements/${misstatementId}`,
        token,
        data,
      );
      if (!ok) {
        setError(apiError || 'Failed to update misstatement');
        return null;
      }
      // Re-fetch schedule to refresh aggregates/bucket
      if (schedule) {
        await fetchSchedule(schedule.engagement_id);
      }
      return updated ?? null;
    },
    [token, schedule, fetchSchedule],
  );

  const archiveItem = useCallback(
    async (misstatementId: number): Promise<boolean> => {
      if (!token) return false;
      const { ok, error: apiError } = await apiDelete(
        `/uncorrected-misstatements/${misstatementId}`,
        token,
      );
      if (!ok) {
        setError(apiError || 'Failed to delete misstatement');
        return false;
      }
      if (schedule) {
        await fetchSchedule(schedule.engagement_id);
      }
      return true;
    },
    [token, schedule, fetchSchedule],
  );

  const items = schedule?.items ?? [];

  return {
    items,
    schedule,
    isLoading,
    error,
    fetchSchedule,
    createItem,
    updateItem,
    archiveItem,
  };
}
