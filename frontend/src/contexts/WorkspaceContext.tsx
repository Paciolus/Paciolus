'use client';

import {
  createContext,
  useContext,
  useState,
  useCallback,
  type ReactNode,
} from 'react';
import { useClients } from '@/hooks/useClients';
import { useEngagement, type UseEngagementReturn } from '@/hooks/useEngagement';
import type { Client, ClientCreateInput, ClientUpdateInput, IndustryOption } from '@/types/client';
import type { Engagement, EngagementCreateInput, ToolRun, MaterialityCascade, ConvergenceResponse, ToolRunTrend } from '@/types/engagement';

/**
 * WorkspaceContext — Sprint 385: Phase LII Foundation
 *
 * Shared state provider for the Workspace Shell. Lifts useClients() and
 * useEngagement() to a single provider so both /portfolio and /engagements
 * pages share one data source without duplicate fetches.
 *
 * ZERO-STORAGE: All state is React context + API. No new persistence.
 */

export type WorkspaceView = 'portfolio' | 'engagements';

interface WorkspaceContextType {
  // Client data (from useClients)
  clients: Client[];
  clientsLoading: boolean;
  clientsTotalCount: number;
  clientsError: string | null;
  industries: IndustryOption[];
  createClient: (data: ClientCreateInput) => Promise<Client | null>;
  updateClient: (id: number, data: ClientUpdateInput) => Promise<Client | null>;
  deleteClient: (id: number) => Promise<boolean>;
  refreshClients: () => Promise<void>;

  // Engagement data (from useEngagement)
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

  // Cross-page persistent selection
  activeClient: Client | null;
  setActiveClient: (client: Client | null) => void;
  activeEngagement: Engagement | null;
  setActiveEngagement: (engagement: Engagement | null) => void;

  // Layout state
  currentView: WorkspaceView;
  setCurrentView: (view: WorkspaceView) => void;
  contextPaneCollapsed: boolean;
  toggleContextPane: () => void;
  insightRailCollapsed: boolean;
  toggleInsightRail: () => void;
  quickSwitcherOpen: boolean;
  setQuickSwitcherOpen: (open: boolean) => void;
}

const WorkspaceContext = createContext<WorkspaceContextType | undefined>(undefined);

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

  const value: WorkspaceContextType = {
    clients,
    clientsLoading,
    clientsTotalCount,
    clientsError,
    industries,
    createClient,
    updateClient,
    deleteClient,
    refreshClients,

    engagements,
    engagementsLoading,
    engagementsError,
    fetchEngagements,
    createEngagement,
    archiveEngagement,
    refreshEngagements,
    getToolRuns,
    getMateriality,
    getConvergence,
    getToolRunTrends,
    downloadConvergenceCsv,

    activeClient,
    setActiveClient,
    activeEngagement,
    setActiveEngagement,

    currentView,
    setCurrentView,
    contextPaneCollapsed,
    toggleContextPane,
    insightRailCollapsed,
    toggleInsightRail,
    quickSwitcherOpen,
    setQuickSwitcherOpen,
  };

  return (
    <WorkspaceContext.Provider value={value}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspaceContext(): WorkspaceContextType {
  const context = useContext(WorkspaceContext);
  if (context === undefined) {
    throw new Error('useWorkspaceContext must be used within a WorkspaceProvider');
  }
  return context;
}
