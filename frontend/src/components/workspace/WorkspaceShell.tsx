'use client';

import { type ReactNode } from 'react';
import { CommandBar } from './CommandBar';
import { WorkspaceFooter } from './WorkspaceFooter';

/**
 * WorkspaceShell — Sprint 385: Phase LII Foundation
 *
 * CSS Grid 3-panel container for the unified workspace.
 *
 * Layout:
 * ┌─────────────── CommandBar ──────────────┐
 * │                                          │
 * ├──────┬──────────────────────┬────────────┤
 * │ Ctx  │   Main Content       │  Insight   │
 * │ Pane │   (children)         │  Rail      │
 * │ stub │                      │  stub      │
 * ├──────┴──────────────────────┴────────────┤
 * │               Footer                     │
 * └──────────────────────────────────────────┘
 *
 * Sidebars are stubbed as empty <aside> in this sprint.
 * Content in Sprint 386 (ContextPane) and Sprint 387 (InsightRail).
 */

interface WorkspaceShellProps {
  children: ReactNode;
  contextPane?: ReactNode;
  insightRail?: ReactNode;
}

export function WorkspaceShell({ children, contextPane, insightRail }: WorkspaceShellProps) {
  return (
    <div className="min-h-screen bg-surface-page flex flex-col">
      <CommandBar />

      {/* Main grid area below CommandBar */}
      <div className="flex-1 flex pt-[57px]">
        {/* Context Pane (left sidebar stub) */}
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

        {/* Insight Rail (right sidebar stub) */}
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
