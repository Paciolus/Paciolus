'use client';

import { useCallback } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useWorkspaceContext } from '@/contexts/WorkspaceContext';
import { INDUSTRY_LABELS, type Industry } from '@/types/client';
import type { Client } from '@/types/client';
import type { Engagement } from '@/types/engagement';
import { AXIS } from '@/utils/marketingMotion';

/**
 * ContextPane — Sprint 386: Phase LII
 *
 * Persistent left sidebar for the workspace shell.
 * - Collapsed: 56px icon-only rail (client initials)
 * - Expanded: 280px sidebar with client/engagement list
 *
 * Portfolio view: scrollable client list
 * Engagements view: engagements grouped/filtered by client
 *
 * prefers-reduced-motion: framer-motion respects it automatically
 */

function getInitials(name: string): string {
  return name
    .split(/\s+/)
    .map(w => w[0] ?? '')
    .slice(0, 2)
    .join('')
    .toUpperCase();
}

function getIndustryBadge(industry: Industry): string {
  return INDUSTRY_LABELS[industry] ?? industry;
}

interface ClientItemProps {
  client: Client;
  isActive: boolean;
  collapsed: boolean;
  onClick: () => void;
}

function ClientItem({ client, isActive, collapsed, onClick }: ClientItemProps) {
  const initials = getInitials(client.name);

  if (collapsed) {
    return (
      <button
        onClick={onClick}
        title={client.name}
        className={`
          w-10 h-10 rounded-lg flex items-center justify-center text-xs font-sans font-bold transition-all
          ${isActive
            ? 'bg-sage-100 text-sage-700 border-2 border-sage-400'
            : 'bg-surface-card-secondary text-content-secondary hover:bg-surface-card hover:text-content-primary border border-transparent'
          }
        `}
      >
        {initials}
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left px-3 py-2.5 rounded-lg transition-all flex items-center gap-3
        ${isActive
          ? 'bg-sage-50 border-l-[3px] border-l-sage-500 pl-[9px]'
          : 'hover:bg-surface-card-secondary border-l-[3px] border-l-transparent'
        }
      `}
    >
      <div className={`
        w-8 h-8 rounded-md flex items-center justify-center text-xs font-sans font-bold shrink-0
        ${isActive ? 'bg-sage-100 text-sage-700' : 'bg-surface-card-secondary text-content-secondary'}
      `}>
        {initials}
      </div>
      <div className="min-w-0 flex-1">
        <p className={`text-sm font-sans truncate ${isActive ? 'text-content-primary font-medium' : 'text-content-secondary'}`}>
          {client.name}
        </p>
        <p className="text-[10px] font-sans text-content-tertiary truncate">
          {getIndustryBadge(client.industry)}
        </p>
      </div>
    </button>
  );
}

interface EngagementItemProps {
  engagement: Engagement;
  clientName: string;
  isActive: boolean;
  collapsed: boolean;
  onClick: () => void;
}

function EngagementItem({ engagement, clientName, isActive, collapsed, onClick }: EngagementItemProps) {
  const period = `${new Date(engagement.period_start).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} – ${new Date(engagement.period_end).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}`;

  if (collapsed) {
    return (
      <button
        onClick={onClick}
        title={`${clientName} (${period})`}
        className={`
          w-10 h-10 rounded-lg flex items-center justify-center text-xs font-mono transition-all
          ${isActive
            ? 'bg-sage-100 text-sage-700 border-2 border-sage-400'
            : 'bg-surface-card-secondary text-content-secondary hover:bg-surface-card hover:text-content-primary border border-transparent'
          }
        `}
      >
        {engagement.status === 'active' ? 'A' : 'X'}
      </button>
    );
  }

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left px-3 py-2.5 rounded-lg transition-all
        ${isActive
          ? 'bg-sage-50 border-l-[3px] border-l-sage-500 pl-[9px]'
          : 'hover:bg-surface-card-secondary border-l-[3px] border-l-transparent'
        }
      `}
    >
      <p className={`text-sm font-sans truncate ${isActive ? 'text-content-primary font-medium' : 'text-content-secondary'}`}>
        {clientName}
      </p>
      <p className="text-[10px] font-mono text-content-tertiary">
        {period}
      </p>
      <span className={`
        inline-flex mt-1 items-center px-1.5 py-0.5 rounded text-[9px] font-sans
        ${engagement.status === 'active'
          ? 'bg-sage-50 text-sage-600 border border-sage-200'
          : 'bg-oatmeal-50 text-oatmeal-600 border border-oatmeal-200'
        }
      `}>
        {engagement.status === 'active' ? 'Active' : 'Archived'}
      </span>
    </button>
  );
}

export function ContextPane() {
  const router = useRouter();
  const {
    clients,
    engagements,
    activeClient,
    setActiveClient,
    activeEngagement,
    setActiveEngagement,
    currentView,
    contextPaneCollapsed,
    toggleContextPane,
  } = useWorkspaceContext();

  const clientNameMap = new Map(clients.map(c => [c.id, c.name]));

  const handleClientClick = useCallback((client: Client) => {
    if (activeClient?.id === client.id) {
      setActiveClient(null);
    } else {
      setActiveClient(client);
      // If on engagements view, filter by this client
      if (currentView === 'engagements') {
        router.replace(`/engagements?client=${client.id}`, { scroll: false });
      }
    }
  }, [activeClient, setActiveClient, currentView, router]);

  const handleEngagementClick = useCallback((engagement: Engagement) => {
    if (activeEngagement?.id === engagement.id) {
      setActiveEngagement(null);
    } else {
      setActiveEngagement(engagement);
      router.replace(`/engagements?engagement=${engagement.id}`, { scroll: false });
    }
  }, [activeEngagement, setActiveEngagement, router]);

  const filteredEngagements = activeClient
    ? engagements.filter(e => e.client_id === activeClient.id)
    : engagements;

  // Group engagements by client for display when no filter
  const engagementsByClient = !activeClient
    ? engagements.reduce<Record<number, Engagement[]>>((acc, e) => {
        const cid = e.client_id;
        if (!acc[cid]) acc[cid] = [];
        acc[cid]!.push(e);
        return acc;
      }, {})
    : null;

  const collapsedWidth = 56;
  const expandedWidth = 280;

  return (
    <motion.div
      animate={{ width: contextPaneCollapsed ? collapsedWidth : expandedWidth }}
      transition={{ type: 'spring' as const, stiffness: 300, damping: 30 }}
      className="h-full border-r border-theme bg-surface-page overflow-hidden flex flex-col"
    >
      {/* Header */}
      <div className="px-2 py-3 border-b border-theme flex items-center justify-between shrink-0">
        {!contextPaneCollapsed && (
          <span className="text-xs font-sans font-medium text-content-tertiary uppercase tracking-wider pl-1">
            {currentView === 'portfolio' ? 'Clients' : 'Workspaces'}
          </span>
        )}
        <button
          onClick={toggleContextPane}
          aria-label={contextPaneCollapsed ? 'Expand context pane' : 'Collapse context pane'}
          className="w-8 h-8 flex items-center justify-center rounded-md text-content-tertiary hover:text-content-primary hover:bg-surface-card-secondary transition-colors mx-auto"
        >
          <svg className={`w-4 h-4 transition-transform ${contextPaneCollapsed ? '' : 'rotate-180'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
        </button>
      </div>

      {/* Count badge */}
      {!contextPaneCollapsed && (
        <div className="px-3 py-2 shrink-0">
          <span className="text-[10px] font-mono text-content-tertiary">
            {currentView === 'portfolio'
              ? `${clients.length} client${clients.length !== 1 ? 's' : ''}`
              : `${filteredEngagements.length} workspace${filteredEngagements.length !== 1 ? 's' : ''}`
            }
          </span>
        </div>
      )}

      {/* Scrollable list */}
      <div className="flex-1 overflow-y-auto px-2 py-1">
        <AnimatePresence mode="wait">
          <motion.div
            key={currentView}
            {...AXIS.horizontal}
            className="space-y-1"
          >
            {currentView === 'portfolio' && clients.map(client => (
              <ClientItem
                key={client.id}
                client={client}
                isActive={activeClient?.id === client.id}
                collapsed={contextPaneCollapsed}
                onClick={() => handleClientClick(client)}
              />
            ))}

            {currentView === 'engagements' && activeClient && filteredEngagements.map(eng => (
              <EngagementItem
                key={eng.id}
                engagement={eng}
                clientName={clientNameMap.get(eng.client_id) ?? `Client #${eng.client_id}`}
                isActive={activeEngagement?.id === eng.id}
                collapsed={contextPaneCollapsed}
                onClick={() => handleEngagementClick(eng)}
              />
            ))}

            {currentView === 'engagements' && !activeClient && engagementsByClient && (
              Object.entries(engagementsByClient).map(([clientIdStr, engs]) => {
                const clientId = Number(clientIdStr);
                const name = clientNameMap.get(clientId) ?? `Client #${clientId}`;
                return (
                  <div key={clientId}>
                    {!contextPaneCollapsed && (
                      <p className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider px-1 pt-3 pb-1">
                        {name}
                      </p>
                    )}
                    {engs.map(eng => (
                      <EngagementItem
                        key={eng.id}
                        engagement={eng}
                        clientName={name}
                        isActive={activeEngagement?.id === eng.id}
                        collapsed={contextPaneCollapsed}
                        onClick={() => handleEngagementClick(eng)}
                      />
                    ))}
                  </div>
                );
              })
            )}

            {/* Empty states */}
            {currentView === 'portfolio' && clients.length === 0 && !contextPaneCollapsed && (
              <p className="text-xs font-sans text-content-tertiary text-center py-4">No clients yet</p>
            )}
            {currentView === 'engagements' && filteredEngagements.length === 0 && !contextPaneCollapsed && (
              <p className="text-xs font-sans text-content-tertiary text-center py-4">No workspaces</p>
            )}
          </motion.div>
        </AnimatePresence>
      </div>

      {/* Quick-action button (expanded only) */}
      <AnimatePresence>
        {!contextPaneCollapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="px-2 py-3 border-t border-theme shrink-0"
          >
            <button
              onClick={() => {
                if (currentView === 'portfolio') {
                  // Signal to open create client modal — the page handles this
                  // We dispatch a custom event since we don't want tight coupling
                  window.dispatchEvent(new CustomEvent('workspace:new-item'));
                } else {
                  window.dispatchEvent(new CustomEvent('workspace:new-item'));
                }
              }}
              className="w-full px-3 py-2 text-xs font-sans text-sage-600 hover:text-sage-700 bg-sage-50 hover:bg-sage-100 border border-sage-200 rounded-lg transition-colors flex items-center gap-2 justify-center"
            >
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              {currentView === 'portfolio' ? 'New Client' : 'New Workspace'}
            </button>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
