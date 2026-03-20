'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  useMemo,
  type ReactNode,
} from 'react';
import { useClients } from '@/hooks/useClients';
import { useEngagement, type UseEngagementReturn } from '@/hooks/useEngagement';
import type { Client, ClientCreateInput, ClientUpdateInput, IndustryOption } from '@/types/client';
import type { Engagement, EngagementCreateInput, ToolRun, MaterialityCascade, ConvergenceResponse, ToolRunTrend } from '@/types/engagement';

/**
 * WorkspaceContext — Split into three granular contexts
 *
 * WorkspaceDataContext      — client/engagement data, loading, errors, mutations
 * WorkspaceSelectionContext — active client/engagement selection
 * WorkspaceLayoutContext    — view mode, pane collapse, quick switcher
 *
 * Nested: Data (outermost) → Selection → Layout (innermost).
 * Backward-compatible useWorkspaceContext() merges all three.
 *
 * ZERO-STORAGE: All state is React context + API. No new persistence.
 */

export type WorkspaceView = 'portfolio' | 'engagements';

// =============================================================================
// Sub-context types
// =============================================================================

export interface WorkspaceDataContextType {
  clients: Client[];
  clientsLoading: boolean;
  clientsTotalCount: number;
  clientsError: string | null;
  industries: IndustryOption[];
  createClient: (data: ClientCreateInput) => Promise<Client | null>;
  updateClient: (id: number, data: ClientUpdateInput) => Promise<Client | null>;
  deleteClient: (id: number) => Promise<boolean>;
  refreshClients: () => Promise<void>;

  engagements: Engagement[];
  engagementsLoading: boolean;
  engagementsError: string | null;
  fetchEngagements: UseEngagementReturn['fetchEngagements'];
  createEngagement: (data: EngagementCreateInput) => Promise<Engagement | null>;
  archiveEngagement: (id: number) => Promise<boolean>;
  refreshEngagements: () => Promise<void>;
  getToolRuns: (id: number) => Promise<ToolRun[]>;
  getMateriality: (id: number) => Promise<MaterialityCascade | null>;
  getConvergence: (id: number) => Promise<ConvergenceResponse | null>;
  getToolRunTrends: (id: number) => Promise<ToolRunTrend[]>;
  downloadConvergenceCsv: (id: number) => Promise<void>;
}

export interface WorkspaceSelectionContextType {
  activeClient: Client | null;
  setActiveClient: (client: Client | null) => void;
  activeEngagement: Engagement | null;
  setActiveEngagement: (engagement: Engagement | null) => void;
}

export interface WorkspaceLayoutContextType {
  currentView: WorkspaceView;
  setCurrentView: (view: WorkspaceView) => void;
  contextPaneCollapsed: boolean;
  toggleContextPane: () => void;
  insightRailCollapsed: boolean;
  toggleInsightRail: () => void;
  quickSwitcherOpen: boolean;
  setQuickSwitcherOpen: (open: boolean) => void;
}

// Combined type (backward compatibility)
interface WorkspaceContextType
  extends WorkspaceDataContextType,
    WorkspaceSelectionContextType,
    WorkspaceLayoutContextType {}

// =============================================================================
// Contexts
// =============================================================================

const WorkspaceDataContext = createContext<WorkspaceDataContextType | undefined>(undefined);
const WorkspaceSelectionContext = createContext<WorkspaceSelectionContextType | undefined>(undefined);
const WorkspaceLayoutContext = createContext<WorkspaceLayoutContextType | undefined>(undefined);

// =============================================================================
// Provider
// =============================================================================

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  // --- Data hooks (called once, shared across pages) ---
  const {
    clients,
    totalCount: clientsTotalCount,
    isLoading: clientsLoading,
    error: clientsError,
    industries,
    createClient,
    updateClient,
    deleteClient,
    refresh: refreshClients,
  } = useClients();

  const {
    engagements,
    isLoading: engagementsLoading,
    error: engagementsError,
    fetchEngagements,
    createEngagement,
    archiveEngagement,
    getToolRuns,
    getMateriality,
    getConvergence,
    getToolRunTrends,
    downloadConvergenceCsv,
    refresh: refreshEngagements,
  } = useEngagement();

  // --- Cross-page selection ---
  const [activeClient, setActiveClient] = useState<Client | null>(null);
  const [activeEngagement, setActiveEngagement] = useState<Engagement | null>(null);

  // --- Layout state ---
  const [currentView, setCurrentView] = useState<WorkspaceView>('portfolio');
  const [contextPaneCollapsed, setContextPaneCollapsed] = useState(true);
  const [insightRailCollapsed, setInsightRailCollapsed] = useState(true);
  const [quickSwitcherOpen, setQuickSwitcherOpen] = useState(false);

  const toggleContextPane = useCallback(() => {
    setContextPaneCollapsed(prev => !prev);
  }, []);

  const toggleInsightRail = useCallback(() => {
    setInsightRailCollapsed(prev => !prev);
  }, []);

  // --- Memoized context values ---
  const dataValue = useMemo<WorkspaceDataContextType>(() => ({
    clients, clientsLoading, clientsTotalCount, clientsError, industries,
    createClient, updateClient, deleteClient, refreshClients,
    engagements, engagementsLoading, engagementsError,
    fetchEngagements, createEngagement, archiveEngagement, refreshEngagements,
    getToolRuns, getMateriality, getConvergence, getToolRunTrends, downloadConvergenceCsv,
  }), [
    clients, clientsLoading, clientsTotalCount, clientsError, industries,
    createClient, updateClient, deleteClient, refreshClients,
    engagements, engagementsLoading, engagementsError,
    fetchEngagements, createEngagement, archiveEngagement, refreshEngagements,
    getToolRuns, getMateriality, getConvergence, getToolRunTrends, downloadConvergenceCsv,
  ]);

  const selectionValue = useMemo<WorkspaceSelectionContextType>(() => ({
    activeClient, setActiveClient, activeEngagement, setActiveEngagement,
  }), [activeClient, activeEngagement]);

  const layoutValue = useMemo<WorkspaceLayoutContextType>(() => ({
    currentView, setCurrentView,
    contextPaneCollapsed, toggleContextPane,
    insightRailCollapsed, toggleInsightRail,
    quickSwitcherOpen, setQuickSwitcherOpen,
  }), [currentView, contextPaneCollapsed, insightRailCollapsed, quickSwitcherOpen,
    toggleContextPane, toggleInsightRail]);

  return (
    <WorkspaceDataContext.Provider value={dataValue}>
      <WorkspaceSelectionContext.Provider value={selectionValue}>
        <WorkspaceLayoutContext.Provider value={layoutValue}>
          {children}
        </WorkspaceLayoutContext.Provider>
      </WorkspaceSelectionContext.Provider>
    </WorkspaceDataContext.Provider>
  );
}

// =============================================================================
// Granular hooks
// =============================================================================

export function useWorkspaceData(): WorkspaceDataContextType {
  const context = useContext(WorkspaceDataContext);
  if (context === undefined) {
    throw new Error('useWorkspaceData must be used within a WorkspaceProvider');
  }
  return context;
}

export function useWorkspaceSelection(): WorkspaceSelectionContextType {
  const context = useContext(WorkspaceSelectionContext);
  if (context === undefined) {
    throw new Error('useWorkspaceSelection must be used within a WorkspaceProvider');
  }
  return context;
}

export function useWorkspaceLayout(): WorkspaceLayoutContextType {
  const context = useContext(WorkspaceLayoutContext);
  if (context === undefined) {
    throw new Error('useWorkspaceLayout must be used within a WorkspaceProvider');
  }
  return context;
}

// =============================================================================
// Backward-compatible combined hook
// =============================================================================

export function useWorkspaceContext(): WorkspaceContextType {
  const data = useContext(WorkspaceDataContext);
  const selection = useContext(WorkspaceSelectionContext);
  const layout = useContext(WorkspaceLayoutContext);
  if (data === undefined || selection === undefined || layout === undefined) {
    throw new Error('useWorkspaceContext must be used within a WorkspaceProvider');
  }
  return { ...data, ...selection, ...layout };
}
