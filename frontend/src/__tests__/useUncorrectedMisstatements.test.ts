/**
 * Sprint 729b — useUncorrectedMisstatements hook tests.
 */
import { renderHook, act } from '@testing-library/react';
import { useAuthSession } from '@/contexts/AuthSessionContext';
import { useUncorrectedMisstatements } from '@/hooks/useUncorrectedMisstatements';

const mockApiGet = jest.fn();
const mockApiPost = jest.fn();
const mockApiPatch = jest.fn();
const mockApiDelete = jest.fn();

jest.mock('@/contexts/AuthSessionContext', () => ({
  useAuthSession: jest.fn(() => ({ token: 'test-token', isAuthenticated: true })),
}));

jest.mock('@/utils', () => ({
  apiGet: (...args: unknown[]) => mockApiGet(...args),
  apiPost: (...args: unknown[]) => mockApiPost(...args),
  apiPatch: (...args: unknown[]) => mockApiPatch(...args),
  apiDelete: (...args: unknown[]) => mockApiDelete(...args),
}));

const mockUseAuthSession = useAuthSession as jest.Mock;

const mockMisstatement = {
  id: 1,
  engagement_id: 10,
  source_type: 'known_error',
  source_reference: 'Cutoff',
  description: 'Dec 31 revenue posted to January',
  accounts_affected: [{ account: 'Revenue', debit_credit: 'CR', amount: 10000 }],
  classification: 'factual',
  fs_impact_net_income: -10000,
  fs_impact_net_assets: -10000,
  cpa_disposition: 'not_yet_reviewed',
  cpa_notes: null,
  created_by: 1,
  created_at: '2026-04-26T00:00:00Z',
  updated_by: null,
  updated_at: '2026-04-26T00:00:00Z',
};

const mockSchedule = {
  engagement_id: 10,
  items: [mockMisstatement],
  subtotals: {
    factual_judgmental_net_income: -10000,
    factual_judgmental_net_assets: -10000,
    projected_net_income: 0,
    projected_net_assets: 0,
  },
  aggregate: { net_income: -10000, net_assets: -10000, driver: 10000 },
  materiality: { overall: 100000, performance: 75000, trivial: 5000 },
  bucket: 'immaterial',
  unreviewed_count: 1,
};

describe('useUncorrectedMisstatements', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuthSession.mockReturnValue({ token: 'test-token', isAuthenticated: true });
    mockApiGet.mockResolvedValue({ ok: true, data: mockSchedule });
    mockApiPost.mockResolvedValue({ ok: true, data: mockMisstatement });
    mockApiPatch.mockResolvedValue({
      ok: true,
      data: { ...mockMisstatement, cpa_disposition: 'auditor_accepts_as_immaterial' },
    });
    mockApiDelete.mockResolvedValue({ ok: true });
  });

  it('initializes empty', () => {
    const { result } = renderHook(() => useUncorrectedMisstatements());
    expect(result.current.items).toEqual([]);
    expect(result.current.schedule).toBeNull();
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('fetchSchedule calls aggregation endpoint and populates items + schedule', async () => {
    const { result } = renderHook(() => useUncorrectedMisstatements());
    await act(async () => {
      await result.current.fetchSchedule(10);
    });
    expect(mockApiGet).toHaveBeenCalledWith(
      '/engagements/10/sum-schedule',
      'test-token',
      { skipCache: true },
    );
    expect(result.current.schedule).toEqual(mockSchedule);
    expect(result.current.items).toEqual([mockMisstatement]);
  });

  it('fetchSchedule clears state when not authenticated', async () => {
    mockUseAuthSession.mockReturnValue({ token: null, isAuthenticated: false });
    const { result } = renderHook(() => useUncorrectedMisstatements());
    await act(async () => {
      await result.current.fetchSchedule(10);
    });
    expect(result.current.schedule).toBeNull();
    expect(mockApiGet).not.toHaveBeenCalled();
  });

  it('fetchSchedule sets error on failure', async () => {
    mockApiGet.mockResolvedValueOnce({ ok: false, error: 'forbidden' });
    const { result } = renderHook(() => useUncorrectedMisstatements());
    await act(async () => {
      await result.current.fetchSchedule(10);
    });
    expect(result.current.schedule).toBeNull();
    expect(result.current.error).toBe('forbidden');
  });

  it('createItem POSTs and re-fetches the schedule', async () => {
    const { result } = renderHook(() => useUncorrectedMisstatements());
    let created;
    await act(async () => {
      created = await result.current.createItem(10, {
        source_type: 'known_error',
        source_reference: 'Cutoff',
        description: 'Cutoff',
        accounts_affected: [{ account: 'Revenue', debit_credit: 'CR', amount: 10000 }],
        classification: 'factual',
        fs_impact_net_income: -10000,
        fs_impact_net_assets: -10000,
      });
    });
    expect(mockApiPost).toHaveBeenCalledWith(
      '/engagements/10/uncorrected-misstatements',
      'test-token',
      expect.objectContaining({ source_type: 'known_error' }),
    );
    // Aggregation endpoint re-fetched after create so bucket/aggregate update
    expect(mockApiGet).toHaveBeenCalledWith(
      '/engagements/10/sum-schedule',
      'test-token',
      { skipCache: true },
    );
    expect(created).toEqual(mockMisstatement);
  });

  it('createItem returns null + sets error on failure', async () => {
    mockApiPost.mockResolvedValueOnce({ ok: false, error: 'validation failed' });
    const { result } = renderHook(() => useUncorrectedMisstatements());
    let created;
    await act(async () => {
      created = await result.current.createItem(10, {
        source_type: 'known_error',
        source_reference: 'X',
        description: 'X',
        accounts_affected: [{ account: 'X', debit_credit: 'DR', amount: 1 }],
        classification: 'factual',
        fs_impact_net_income: -1,
        fs_impact_net_assets: -1,
      });
    });
    expect(created).toBeNull();
    expect(result.current.error).toBe('validation failed');
  });

  it('updateItem PATCHes the item-scoped path and re-fetches schedule', async () => {
    const { result } = renderHook(() => useUncorrectedMisstatements());
    // Seed schedule so subsequent fetchSchedule has a known engagement id
    await act(async () => {
      await result.current.fetchSchedule(10);
    });
    await act(async () => {
      await result.current.updateItem(1, {
        cpa_disposition: 'auditor_accepts_as_immaterial',
      });
    });
    expect(mockApiPatch).toHaveBeenCalledWith(
      '/uncorrected-misstatements/1',
      'test-token',
      { cpa_disposition: 'auditor_accepts_as_immaterial' },
    );
    // After patch, fetchSchedule was called again to refresh the aggregate
    expect(mockApiGet).toHaveBeenCalledTimes(2);
  });

  it('archiveItem DELETEs and re-fetches schedule when one is loaded', async () => {
    const { result } = renderHook(() => useUncorrectedMisstatements());
    await act(async () => {
      await result.current.fetchSchedule(10);
    });
    let success;
    await act(async () => {
      success = await result.current.archiveItem(1);
    });
    expect(mockApiDelete).toHaveBeenCalledWith(
      '/uncorrected-misstatements/1',
      'test-token',
    );
    expect(success).toBe(true);
    // Re-fetch happens after delete
    expect(mockApiGet).toHaveBeenCalledTimes(2);
  });

  it('archiveItem returns false on failure', async () => {
    mockApiDelete.mockResolvedValueOnce({ ok: false, error: 'forbidden' });
    const { result } = renderHook(() => useUncorrectedMisstatements());
    let success;
    await act(async () => {
      success = await result.current.archiveItem(1);
    });
    expect(success).toBe(false);
    expect(result.current.error).toBe('forbidden');
  });

  it('returns null from mutations when no token', async () => {
    mockUseAuthSession.mockReturnValue({ token: null, isAuthenticated: false });
    const { result } = renderHook(() => useUncorrectedMisstatements());
    let created;
    let updated;
    let archived;
    await act(async () => {
      created = await result.current.createItem(10, {
        source_type: 'known_error',
        source_reference: 'X',
        description: 'X',
        accounts_affected: [{ account: 'X', debit_credit: 'DR', amount: 1 }],
        classification: 'factual',
        fs_impact_net_income: 0,
        fs_impact_net_assets: 0,
      });
      updated = await result.current.updateItem(1, { cpa_notes: 'x' });
      archived = await result.current.archiveItem(1);
    });
    expect(created).toBeNull();
    expect(updated).toBeNull();
    expect(archived).toBe(false);
    expect(mockApiPost).not.toHaveBeenCalled();
    expect(mockApiPatch).not.toHaveBeenCalled();
    expect(mockApiDelete).not.toHaveBeenCalled();
  });
});
