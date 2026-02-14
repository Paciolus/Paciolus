'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useEffect,
  ReactNode,
} from 'react';
import { useSearchParams, useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useEngagement } from '@/hooks/useEngagement';
import type { Engagement, ToolRun, MaterialityCascade } from '@/types/engagement';

/**
 * EngagementContext — Sprint 98
 *
 * Manages the "active engagement" state for the engagements page.
 * Reads ?engagement=X from URL on mount, syncs to URL on change.
 *
 * Scoped to the engagements page only (not in global providers.tsx).
 * Tool page integration deferred to Sprint 100+.
 */

interface EngagementContextType {
  activeEngagement: Engagement | null;
  toolRuns: ToolRun[];
  materiality: MaterialityCascade | null;
  isLoading: boolean;
  toastMessage: string | null;
  selectEngagement: (id: number) => Promise<void>;
  clearEngagement: () => void;
  refreshToolRuns: () => Promise<void>;
  triggerLinkToast: (toolName: string) => void;
  dismissToast: () => void;
}

const EngagementContext = createContext<EngagementContextType | undefined>(undefined);

export function EngagementProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, token } = useAuth();
  const { getEngagement, getToolRuns, getMateriality } = useEngagement({ autoFetch: false });
  const searchParams = useSearchParams();
  const router = useRouter();
  const pathname = usePathname();

  const [activeEngagement, setActiveEngagement] = useState<Engagement | null>(null);
  const [toolRuns, setToolRuns] = useState<ToolRun[]>([]);
  const [materiality, setMateriality] = useState<MaterialityCascade | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [toastMessage, setToastMessage] = useState<string | null>(null);

  const triggerLinkToast = useCallback((toolName: string) => {
    if (!activeEngagement) return;
    setToastMessage(`${toolName} results linked to workspace`);
  }, [activeEngagement]);

  const dismissToast = useCallback(() => setToastMessage(null), []);

  const selectEngagement = useCallback(async (id: number) => {
    setIsLoading(true);

    const [engagement, runs, mat] = await Promise.all([
      getEngagement(id),
      getToolRuns(id),
      getMateriality(id),
    ]);

    if (engagement) {
      setActiveEngagement(engagement);
      setToolRuns(runs);
      setMateriality(mat);

      // Sync to URL
      const params = new URLSearchParams(searchParams.toString());
      params.set('engagement', id.toString());
      router.replace(`${pathname}?${params.toString()}`, { scroll: false });
    }

    setIsLoading(false);
  }, [getEngagement, getToolRuns, getMateriality, searchParams, router, pathname]);

  const clearEngagement = useCallback(() => {
    setActiveEngagement(null);
    setToolRuns([]);
    setMateriality(null);

    // Remove from URL
    const params = new URLSearchParams(searchParams.toString());
    params.delete('engagement');
    const qs = params.toString();
    router.replace(qs ? `${pathname}?${qs}` : pathname, { scroll: false });
  }, [searchParams, router, pathname]);

  const refreshToolRuns = useCallback(async () => {
    if (!activeEngagement) return;

    const runs = await getToolRuns(activeEngagement.id);
    setToolRuns(runs);
  }, [activeEngagement, getToolRuns]);

  // Read ?engagement=X from URL on mount
  useEffect(() => {
    if (!isAuthenticated || !token) return;

    const engagementId = searchParams.get('engagement');
    if (engagementId && !activeEngagement) {
      const id = parseInt(engagementId, 10);
      if (!isNaN(id)) {
        selectEngagement(id);
      }
    }
  }, [isAuthenticated, token]); // eslint-disable-line react-hooks/exhaustive-deps

  const contextValue: EngagementContextType = {
    activeEngagement,
    toolRuns,
    materiality,
    isLoading,
    toastMessage,
    selectEngagement,
    clearEngagement,
    refreshToolRuns,
    triggerLinkToast,
    dismissToast,
  };

  return (
    <EngagementContext.Provider value={contextValue}>
      {children}
    </EngagementContext.Provider>
  );
}

export function useEngagementContext() {
  const context = useContext(EngagementContext);
  if (context === undefined) {
    throw new Error('useEngagementContext must be used within an EngagementProvider');
  }
  return context;
}

/** Flattened engagement context for tool pages — Sprint 226 */
export type OptionalEngagementContext = EngagementContextType & {
  engagementId: number | null;
};

/**
 * Safe engagement context accessor — Sprint 103
 *
 * Returns null when no EngagementProvider is present (instead of throwing).
 * Critical for useAuditUpload backward compatibility — tools work standalone
 * when no engagement context wraps them.
 *
 * Sprint 226: Exposes `engagementId` directly to eliminate triple-chain
 * `engagement?.activeEngagement?.id` across consumer files.
 */
export function useOptionalEngagementContext(): OptionalEngagementContext | null {
  const context = useContext(EngagementContext);
  if (!context) return null;
  return {
    ...context,
    engagementId: context.activeEngagement?.id ?? null,
  };
}
