/**
 * Sprint 728b — useAnalyticalExpectations hook tests.
 */
import { renderHook, act } from '@testing-library/react';
import { useAuthSession } from '@/contexts/AuthSessionContext';
import { useAnalyticalExpectations } from '@/hooks/useAnalyticalExpectations';

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

const mockExpectation = {
  id: 1,
  engagement_id: 10,
  procedure_target_type: 'account',
  procedure_target_label: 'Revenue',
  expected_value: 1000,
  expected_range_low: null,
  expected_range_high: null,
  precision_threshold_amount: 50,
  precision_threshold_percent: null,
  corroboration_basis_text: 'Prior period',
  corroboration_tags: ['prior_period'],
  cpa_notes: null,
  result_actual_value: null,
  result_variance_amount: null,
  result_status: 'not_evaluated',
  created_by: 1,
  created_at: '2026-04-26T00:00:00Z',
  updated_by: null,
  updated_at: '2026-04-26T00:00:00Z',
};

describe('useAnalyticalExpectations', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuthSession.mockReturnValue({ token: 'test-token', isAuthenticated: true });
    mockApiGet.mockResolvedValue({
      ok: true,
      data: { items: [mockExpectation], total_count: 1, page: 1, page_size: 20 },
    });
    mockApiPost.mockResolvedValue({ ok: true, data: mockExpectation });
    mockApiPatch.mockResolvedValue({
      ok: true,
      data: { ...mockExpectation, result_status: 'within_threshold', result_actual_value: 1010 },
    });
    mockApiDelete.mockResolvedValue({ ok: true });
  });

  it('initializes empty', () => {
    const { result } = renderHook(() => useAnalyticalExpectations());
    expect(result.current.items).toEqual([]);
    expect(result.current.totalCount).toBe(0);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('fetchItems calls apiGet without filters', async () => {
    const { result } = renderHook(() => useAnalyticalExpectations());
    await act(async () => {
      await result.current.fetchItems(10);
    });
    expect(mockApiGet).toHaveBeenCalledWith(
      '/engagements/10/analytical-expectations',
      'test-token',
      { skipCache: true },
    );
    expect(result.current.items).toEqual([mockExpectation]);
    expect(result.current.totalCount).toBe(1);
  });

  it('fetchItems passes status + target_type filters as query params', async () => {
    const { result } = renderHook(() => useAnalyticalExpectations());
    await act(async () => {
      await result.current.fetchItems(10, 'not_evaluated', 'account');
    });
    expect(mockApiGet).toHaveBeenCalledWith(
      '/engagements/10/analytical-expectations?result_status=not_evaluated&target_type=account',
      'test-token',
      { skipCache: true },
    );
  });

  it('fetchItems clears state when not authenticated', async () => {
    mockUseAuthSession.mockReturnValue({ token: null, isAuthenticated: false });
    const { result } = renderHook(() => useAnalyticalExpectations());
    await act(async () => {
      await result.current.fetchItems(10);
    });
    expect(result.current.items).toEqual([]);
    expect(mockApiGet).not.toHaveBeenCalled();
  });

  it('createItem POSTs and appends to items list', async () => {
    const { result } = renderHook(() => useAnalyticalExpectations());
    let created;
    await act(async () => {
      created = await result.current.createItem(10, {
        procedure_target_type: 'account',
        procedure_target_label: 'Revenue',
        expected_value: 1000,
        precision_threshold_amount: 50,
        corroboration_basis_text: 'Prior period',
        corroboration_tags: ['prior_period'],
      });
    });
    expect(mockApiPost).toHaveBeenCalledWith(
      '/engagements/10/analytical-expectations',
      'test-token',
      expect.objectContaining({ procedure_target_label: 'Revenue' }),
    );
    expect(created).toEqual(mockExpectation);
    expect(result.current.items).toContainEqual(mockExpectation);
    expect(result.current.totalCount).toBe(1);
  });

  it('createItem returns null and sets error on failure', async () => {
    mockApiPost.mockResolvedValueOnce({ ok: false, error: 'validation failed' });
    const { result } = renderHook(() => useAnalyticalExpectations());
    let created;
    await act(async () => {
      created = await result.current.createItem(10, {
        procedure_target_type: 'account',
        procedure_target_label: 'Revenue',
        expected_value: 1000,
        precision_threshold_amount: 50,
        corroboration_basis_text: 'X',
        corroboration_tags: ['prior_period'],
      });
    });
    expect(created).toBeNull();
    expect(result.current.error).toBe('validation failed');
  });

  it('updateItem PATCHes and replaces in items list', async () => {
    const { result } = renderHook(() => useAnalyticalExpectations());
    // seed
    await act(async () => {
      await result.current.fetchItems(10);
    });
    await act(async () => {
      await result.current.updateItem(1, { result_actual_value: 1010 });
    });
    expect(mockApiPatch).toHaveBeenCalledWith(
      '/analytical-expectations/1',
      'test-token',
      { result_actual_value: 1010 },
    );
    expect(result.current.items[0].result_status).toBe('within_threshold');
    expect(result.current.items[0].result_actual_value).toBe(1010);
  });

  it('archiveItem DELETEs and removes from items list', async () => {
    const { result } = renderHook(() => useAnalyticalExpectations());
    await act(async () => {
      await result.current.fetchItems(10);
    });
    expect(result.current.items.length).toBe(1);
    let success;
    await act(async () => {
      success = await result.current.archiveItem(1);
    });
    expect(mockApiDelete).toHaveBeenCalledWith(
      '/analytical-expectations/1',
      'test-token',
    );
    expect(success).toBe(true);
    expect(result.current.items).toEqual([]);
    expect(result.current.totalCount).toBe(0);
  });

  it('archiveItem returns false on failure', async () => {
    mockApiDelete.mockResolvedValueOnce({ ok: false, error: 'forbidden' });
    const { result } = renderHook(() => useAnalyticalExpectations());
    let success;
    await act(async () => {
      success = await result.current.archiveItem(1);
    });
    expect(success).toBe(false);
    expect(result.current.error).toBe('forbidden');
  });

  it('returns null from create/update when no token', async () => {
    mockUseAuthSession.mockReturnValue({ token: null, isAuthenticated: false });
    const { result } = renderHook(() => useAnalyticalExpectations());
    let created;
    let updated;
    await act(async () => {
      created = await result.current.createItem(10, {
        procedure_target_type: 'account',
        procedure_target_label: 'X',
        expected_value: 1,
        precision_threshold_amount: 1,
        corroboration_basis_text: 'X',
        corroboration_tags: ['prior_period'],
      });
      updated = await result.current.updateItem(1, { cpa_notes: 'x' });
    });
    expect(created).toBeNull();
    expect(updated).toBeNull();
    expect(mockApiPost).not.toHaveBeenCalled();
    expect(mockApiPatch).not.toHaveBeenCalled();
  });
});
