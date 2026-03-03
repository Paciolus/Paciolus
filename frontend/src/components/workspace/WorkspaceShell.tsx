'use client';

import { type ReactNode } from 'react';
import { WorkspaceFooter } from './WorkspaceFooter';

/**
 * WorkspaceShell
 * CommandBar removed — toolbar now at AuthenticatedShell level.
 *
 * 3-panel container: ContextPane | Main Content | InsightRail + Footer.
 */

interface WorkspaceShellProps {
  children: ReactNode;
  contextPane?: ReactNode;
  insightRail?: ReactNode;
}

export function WorkspaceShell({ children, contextPane, insightRail }: WorkspaceShellProps) {
  return (
    <div className="min-h-screen bg-surface-page flex flex-col">
      {/* Main grid area */}
      <div className="flex-1 flex">
        {/* Context Pane (left sidebar) */}
        {contextPane && (
          <aside
            aria-label="Context pane"
            className="hidden lg:block shrink-0"
          >
            {contextPane}
          </aside>
        )}

        {/* Main content area */}
        <main className="flex-1 min-w-0 overflow-y-auto">
          {children}
        </main>

        {/* Insight Rail (right sidebar) */}
        {insightRail && (
          <aside
            aria-label="Insight rail"
            className="hidden xl:block shrink-0"
          >
            {insightRail}
          </aside>
        )}
      </div>

      <WorkspaceFooter />
    </div>
  );
}
