'use client';

/**
 * Workspace Route Group Layout — Sprint 385-388: Phase LII
 *
 * Wraps /portfolio and /engagements in a shared WorkspaceProvider +
 * WorkspaceShell. Route groups are URL-transparent: users still navigate
 * to /portfolio and /engagements as before.
 *
 * Auth redirect is handled here (lifted from individual pages).
 * IntelligenceCanvas (workspace variant) provides ambient background.
 * Keyboard shortcuts (Cmd+K, Cmd+[, Cmd+], etc.) registered here.
 */

import { useEffect, useMemo, type ReactNode } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { WorkspaceProvider, useWorkspaceContext, type WorkspaceView } from '@/contexts/WorkspaceContext';
import { WorkspaceShell, ContextPane, InsightRail } from '@/components/workspace';
import { IntelligenceCanvas } from '@/components/shared';
import { useKeyboardShortcuts, type ShortcutConfig } from '@/hooks/useKeyboardShortcuts';
import { useRegisterCommands } from '@/hooks/useRegisterCommands';
import type { PaletteCommand } from '@/types/commandPalette';

function WorkspaceLayoutInner({ children }: { children: ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const { isAuthenticated, isLoading: authLoading } = useAuth();
  const {
    clients,
    engagements,
    setCurrentView,
    toggleContextPane,
    toggleInsightRail,
    setActiveClient,
    setActiveEngagement,
  } = useWorkspaceContext();

  // Sync currentView from pathname
  useEffect(() => {
    const segment = pathname.split('/').pop() || '';
    const viewMap: Record<string, WorkspaceView> = {
      portfolio: 'portfolio',
      engagements: 'engagements',
    };
    const view = viewMap[segment];
    if (view) {
      setCurrentView(view);
    }
  }, [pathname, setCurrentView]);

  // Auth redirect (lifted from individual pages)
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push(`/login?redirect=${pathname}`);
    }
  }, [authLoading, isAuthenticated, router, pathname]);

  // Keyboard shortcuts (Cmd+K handled globally by CommandPaletteProvider — Sprint 396)
  const shortcuts = useMemo<ShortcutConfig[]>(() => [
    {
      key: '[',
      meta: true,
      action: () => toggleContextPane(),
      description: 'Toggle ContextPane',
    },
    {
      key: ']',
      meta: true,
      action: () => toggleInsightRail(),
      description: 'Toggle InsightRail',
    },
    {
      key: '1',
      meta: true,
      action: () => router.push('/portfolio'),
      description: 'Navigate to Portfolio',
    },
    {
      key: '2',
      meta: true,
      action: () => router.push('/engagements'),
      description: 'Navigate to Workspaces',
    },
  ], [toggleContextPane, toggleInsightRail, router]);

  useKeyboardShortcuts(shortcuts);

  // Register dynamic workspace commands for the command palette
  const workspaceCommands = useMemo<PaletteCommand[]>(() => {
    const cmds: PaletteCommand[] = [];

    clients.forEach(c => {
      cmds.push({
        id: `client-${c.id}`,
        label: c.name,
        detail: c.industry,
        category: 'workspace',
        keywords: [c.name, c.industry].filter(Boolean) as string[],
        action: () => {
          setActiveClient(c);
          router.push('/portfolio');
        },
        priority: 5,
      });
    });

    const clientNameMap = new Map(clients.map(c => [c.id, c.name]));
    engagements.filter(e => e.status === 'active').forEach(e => {
      const clientName = clientNameMap.get(e.client_id) ?? `Client #${e.client_id}`;
      cmds.push({
        id: `eng-${e.id}`,
        label: clientName,
        detail: `${new Date(e.period_start).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} \u2013 ${new Date(e.period_end).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}`,
        category: 'workspace',
        keywords: [clientName, 'engagement', 'workspace'],
        action: () => {
          setActiveEngagement(e);
          router.push(`/engagements?engagement=${e.id}`);
        },
        priority: 4,
      });
    });

    return cmds;
  }, [clients, engagements, setActiveClient, setActiveEngagement, router]);

  useRegisterCommands('workspace', workspaceCommands);

  // Auth loading state
  if (authLoading || !isAuthenticated) {
    return (
      <div className="min-h-screen bg-surface-page flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
          <p className="text-content-secondary font-sans">Loading workspace...</p>
        </div>
      </div>
    );
  }

  return (
    <>
      <IntelligenceCanvas variant="workspace" />
      <WorkspaceShell contextPane={<ContextPane />} insightRail={<InsightRail />}>
        {children}
      </WorkspaceShell>
    </>
  );
}

export default function WorkspaceLayout({ children }: { children: ReactNode }) {
  return (
    <WorkspaceProvider>
      <WorkspaceLayoutInner>
        {children}
      </WorkspaceLayoutInner>
    </WorkspaceProvider>
  );
}
