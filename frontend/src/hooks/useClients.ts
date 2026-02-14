/**
 * Paciolus useClients Hook
 * Sprint 16: Client Core Infrastructure
 * Phase 1 Refactor: Using shared API client utilities
 *
 * React hook for fetching and managing the client list.
 *
 * ZERO-STORAGE COMPLIANCE:
 * - Client data is fetched from API and stored in React state (memory only)
 * - No client data is persisted to localStorage or sessionStorage
 * - Client list is re-fetched on authentication state changes
 */

'use client';

import { useState, useCallback, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiGet, apiPost, apiPut, apiDelete, isAuthError } from '@/utils';
import type {
  Client,
  ClientCreateInput,
  ClientUpdateInput,
  ClientListResponse,
  IndustryOption,
} from '@/types/client';

interface UseClientsOptions {
  /** Auto-fetch clients on mount (default: true) */
  autoFetch?: boolean;
  /** Page size for pagination (default: 50) */
  pageSize?: number;
}

interface UseClientsReturn {
  /** List of clients */
  clients: Client[];
  /** Total count of clients (for pagination) */
  totalCount: number;
  /** Current page number */
  page: number;
  /** Loading state */
  isLoading: boolean;
  /** Error message if any */
  error: string | null;
  /** Industry options for dropdowns */
  industries: IndustryOption[];
  /** Fetch clients (with optional search) */
  fetchClients: (search?: string, page?: number) => Promise<void>;
  /** Create a new client */
  createClient: (data: ClientCreateInput) => Promise<Client | null>;
  /** Update an existing client */
  updateClient: (id: number, data: ClientUpdateInput) => Promise<Client | null>;
  /** Delete a client */
  deleteClient: (id: number) => Promise<boolean>;
  /** Get a single client by ID */
  getClient: (id: number) => Promise<Client | null>;
  /** Refresh the client list */
  refresh: () => Promise<void>;
}

/**
 * Hook for managing client data.
 *
 * Usage:
 * ```tsx
 * const { clients, isLoading, createClient, refresh } = useClients();
 *
 * // Create a new client
 * const newClient = await createClient({
 *   name: 'Acme Corp',
 *   industry: 'technology',
 *   fiscal_year_end: '12-31'
 * });
 *
 * // Search clients
 * await fetchClients('acme');
 * ```
 */
export function useClients(options: UseClientsOptions = {}): UseClientsReturn {
  const { autoFetch = true, pageSize = 50 } = options;
  const { token, isAuthenticated } = useAuth();

  // State
  const [clients, setClients] = useState<Client[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [page, setPage] = useState(1);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [industries, setIndustries] = useState<IndustryOption[]>([]);

  /**
   * Fetch industry options from API.
   */
  const fetchIndustries = useCallback(async () => {
    const { data, ok } = await apiGet<IndustryOption[]>('/clients/industries', null);

    if (ok && data) {
      setIndustries(data);
    } else {
      // Use default industries as fallback
      setIndustries([
        { value: 'technology', label: 'Technology' },
        { value: 'healthcare', label: 'Healthcare' },
        { value: 'financial_services', label: 'Financial Services' },
        { value: 'manufacturing', label: 'Manufacturing' },
        { value: 'retail', label: 'Retail' },
        { value: 'professional_services', label: 'Professional Services' },
        { value: 'real_estate', label: 'Real Estate' },
        { value: 'construction', label: 'Construction' },
        { value: 'hospitality', label: 'Hospitality' },
        { value: 'nonprofit', label: 'Nonprofit' },
        { value: 'education', label: 'Education' },
        { value: 'other', label: 'Other' },
      ]);
    }
  }, []);

  /**
   * Fetch clients from API.
   */
  const fetchClients = useCallback(async (search?: string, newPage: number = 1) => {
    if (!isAuthenticated || !token) {
      setClients([]);
      setTotalCount(0);
      return;
    }

    setIsLoading(true);
    setError(null);

    const params = new URLSearchParams({
      page: newPage.toString(),
      page_size: pageSize.toString(),
    });

    if (search) {
      params.append('search', search);
    }

    const { data, error: apiError, ok, status } = await apiGet<ClientListResponse>(
      `/clients?${params}`,
      token
    );

    if (!ok) {
      if (isAuthError(status)) {
        setError('Session expired. Please log in again.');
        setClients([]);
      } else {
        setError(apiError || 'Failed to fetch clients');
      }
      setIsLoading(false);
      return;
    }

    if (data) {
      setClients(data.clients);
      setTotalCount(data.total_count);
      setPage(data.page);
    }

    setIsLoading(false);
  }, [isAuthenticated, token, pageSize]);

  /**
   * Create a new client.
   */
  const createClient = useCallback(async (data: ClientCreateInput): Promise<Client | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setIsLoading(true);
    setError(null);

    const { data: newClient, error: apiError, ok } = await apiPost<Client>(
      '/clients',
      token,
      data
    );

    if (!ok || !newClient) {
      setError(apiError || 'Failed to create client');
      setIsLoading(false);
      return null;
    }

    // Add to local state
    setClients(prev => [newClient, ...prev]);
    setTotalCount(prev => prev + 1);
    setIsLoading(false);

    return newClient;
  }, [isAuthenticated, token]);

  /**
   * Update an existing client.
   */
  const updateClient = useCallback(async (id: number, data: ClientUpdateInput): Promise<Client | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    setIsLoading(true);
    setError(null);

    const { data: updatedClient, error: apiError, ok } = await apiPut<Client>(
      `/clients/${id}`,
      token,
      data
    );

    if (!ok || !updatedClient) {
      setError(apiError || 'Failed to update client');
      setIsLoading(false);
      return null;
    }

    // Update in local state
    setClients(prev => prev.map(c => c.id === id ? updatedClient : c));
    setIsLoading(false);

    return updatedClient;
  }, [isAuthenticated, token]);

  /**
   * Delete a client.
   */
  const deleteClient = useCallback(async (id: number): Promise<boolean> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return false;
    }

    setIsLoading(true);
    setError(null);

    const { error: apiError, ok } = await apiDelete(`/clients/${id}`, token);

    if (!ok) {
      setError(apiError || 'Failed to delete client');
      setIsLoading(false);
      return false;
    }

    // Remove from local state
    setClients(prev => prev.filter(c => c.id !== id));
    setTotalCount(prev => prev - 1);
    setIsLoading(false);

    return true;
  }, [isAuthenticated, token]);

  /**
   * Get a single client by ID.
   */
  const getClient = useCallback(async (id: number): Promise<Client | null> => {
    if (!isAuthenticated || !token) {
      setError('Not authenticated');
      return null;
    }

    const { data, ok } = await apiGet<Client>(`/clients/${id}`, token);

    if (!ok || !data) {
      return null;
    }

    return data;
  }, [isAuthenticated, token]);

  /**
   * Refresh the client list.
   */
  const refresh = useCallback(async () => {
    await fetchClients(undefined, page);
  }, [fetchClients, page]);

  // Auto-fetch on mount and auth changes
  useEffect(() => {
    if (autoFetch && isAuthenticated) {
      fetchClients();
      fetchIndustries();
    } else if (!isAuthenticated) {
      // Clear state when logged out
      setClients([]);
      setTotalCount(0);
      setError(null);
    }
  }, [autoFetch, isAuthenticated, fetchClients, fetchIndustries]);

  return {
    clients,
    totalCount,
    page,
    isLoading,
    error,
    industries,
    fetchClients,
    createClient,
    updateClient,
    deleteClient,
    getClient,
    refresh,
  };
}
