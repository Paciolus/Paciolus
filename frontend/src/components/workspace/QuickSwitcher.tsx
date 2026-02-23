'use client';

import { useState, useCallback, useEffect, useRef, useMemo } from 'react';
import { useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import { useWorkspaceContext } from '@/contexts/WorkspaceContext';
import { useFocusTrap } from '@/hooks/useFocusTrap';

/**
 * QuickSwitcher — Sprint 388: Phase LII
 *
 * Modal overlay with fuzzy search across clients, workspaces, and navigation.
 * Opened via Cmd+K. Arrow keys navigate, Enter selects, Escape closes.
 * useFocusTrap integration for WCAG compliance.
 */

interface SearchResult {
  id: string;
  type: 'client' | 'workspace' | 'navigation';
  label: string;
  detail?: string;
  action: () => void;
}

const NAVIGATION_ITEMS: { label: string; href: string; detail: string }[] = [
  { label: 'Home', href: '/', detail: 'Go to homepage' },
  { label: 'Client Portfolio', href: '/portfolio', detail: 'Manage clients' },
  { label: 'Diagnostic Workspace', href: '/engagements', detail: 'Manage workspaces' },
  { label: 'Tools', href: '/tools/trial-balance', detail: 'Open diagnostic tools' },
  { label: 'Settings', href: '/settings', detail: 'Account settings' },
];

function fuzzyMatch(query: string, text: string): boolean {
  const q = query.toLowerCase();
  const t = text.toLowerCase();
  if (t.includes(q)) return true;

  // Simple subsequence match
  let qi = 0;
  for (let ti = 0; ti < t.length && qi < q.length; ti++) {
    if (t[ti] === q[qi]) qi++;
  }
  return qi === q.length;
}

export function QuickSwitcher() {
  const router = useRouter();
  const {
    clients,
    engagements,
    quickSwitcherOpen,
    setQuickSwitcherOpen,
    setActiveClient,
    setActiveEngagement,
  } = useWorkspaceContext();

  const [query, setQuery] = useState('');
  const [selectedIndex, setSelectedIndex] = useState(0);
  const inputRef = useRef<HTMLInputElement>(null);
  const listRef = useRef<HTMLDivElement>(null);
  const containerRef = useFocusTrap(quickSwitcherOpen, () => setQuickSwitcherOpen(false));

  // Build and memoize search results to stabilize handleKeyDown deps
  const { clientResults, workspaceResults, navResults, allResults } = useMemo(() => {
    const nameMap = new Map(clients.map(c => [c.id, c.name]));
    const results: SearchResult[] = [];

    if (query.length === 0) {
      // Show recent / all when no query
      clients.slice(0, 5).forEach(c => {
        results.push({
          id: `client-${c.id}`,
          type: 'client',
          label: c.name,
          detail: c.industry,
          action: () => {
            setActiveClient(c);
            router.push('/portfolio');
          },
        });
      });

      engagements.filter(e => e.status === 'active').slice(0, 3).forEach(e => {
        results.push({
          id: `eng-${e.id}`,
          type: 'workspace',
          label: nameMap.get(e.client_id) ?? `Client #${e.client_id}`,
          detail: `${new Date(e.period_start).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} – ${new Date(e.period_end).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}`,
          action: () => {
            setActiveEngagement(e);
            router.push(`/engagements?engagement=${e.id}`);
          },
        });
      });

      NAVIGATION_ITEMS.forEach(nav => {
        results.push({
          id: `nav-${nav.href}`,
          type: 'navigation',
          label: nav.label,
          detail: nav.detail,
          action: () => router.push(nav.href),
        });
      });
    } else {
      // Filter by query
      clients.filter(c => fuzzyMatch(query, c.name) || fuzzyMatch(query, c.industry)).forEach(c => {
        results.push({
          id: `client-${c.id}`,
          type: 'client',
          label: c.name,
          detail: c.industry,
          action: () => {
            setActiveClient(c);
            router.push('/portfolio');
          },
        });
      });

      engagements.filter(e => {
        const name = nameMap.get(e.client_id) ?? '';
        return fuzzyMatch(query, name) || fuzzyMatch(query, e.status);
      }).forEach(e => {
        results.push({
          id: `eng-${e.id}`,
          type: 'workspace',
          label: nameMap.get(e.client_id) ?? `Client #${e.client_id}`,
          detail: `${new Date(e.period_start).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })} – ${new Date(e.period_end).toLocaleDateString('en-US', { month: 'short', year: '2-digit' })}`,
          action: () => {
            setActiveEngagement(e);
            router.push(`/engagements?engagement=${e.id}`);
          },
        });
      });

      NAVIGATION_ITEMS.filter(n => fuzzyMatch(query, n.label) || fuzzyMatch(query, n.detail)).forEach(nav => {
        results.push({
          id: `nav-${nav.href}`,
          type: 'navigation',
          label: nav.label,
          detail: nav.detail,
          action: () => router.push(nav.href),
        });
      });
    }

    const cr = results.filter(r => r.type === 'client');
    const wr = results.filter(r => r.type === 'workspace');
    const nr = results.filter(r => r.type === 'navigation');
    return { clientResults: cr, workspaceResults: wr, navResults: nr, allResults: [...cr, ...wr, ...nr] };
  }, [query, clients, engagements, setActiveClient, setActiveEngagement, router]);

  // Reset selection when query or results change
  useEffect(() => {
    setSelectedIndex(0);
  }, [query]);

  // Focus input on open
  useEffect(() => {
    if (quickSwitcherOpen) {
      setQuery('');
      setSelectedIndex(0);
      setTimeout(() => inputRef.current?.focus(), 50);
    }
  }, [quickSwitcherOpen]);

  const handleSelect = useCallback((result: SearchResult) => {
    setQuickSwitcherOpen(false);
    result.action();
  }, [setQuickSwitcherOpen]);

  const handleKeyDown = useCallback((e: React.KeyboardEvent) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setSelectedIndex(prev => Math.min(prev + 1, allResults.length - 1));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setSelectedIndex(prev => Math.max(prev - 1, 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      const selected = allResults[selectedIndex];
      if (selected) handleSelect(selected);
    }
  }, [allResults, selectedIndex, handleSelect]);

  // Scroll selected item into view
  useEffect(() => {
    if (!listRef.current) return;
    const items = listRef.current.querySelectorAll('[data-result-item]');
    const item = items[selectedIndex];
    if (item) {
      item.scrollIntoView({ block: 'nearest' });
    }
  }, [selectedIndex]);

  if (!quickSwitcherOpen) return null;

  const typeIcons: Record<string, string> = {
    client: 'C',
    workspace: 'W',
    navigation: '\u2192',
  };

  const typeLabels: Record<string, string> = {
    client: 'Clients',
    workspace: 'Workspaces',
    navigation: 'Navigation',
  };

  let flatIndex = -1;

  function renderGroup(items: SearchResult[], type: string) {
    if (items.length === 0) return null;
    return (
      <div>
        <p className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider px-3 pt-3 pb-1">
          {typeLabels[type]}
        </p>
        {items.map(result => {
          flatIndex++;
          const idx = flatIndex;
          const isSelected = idx === selectedIndex;
          return (
            <button
              key={result.id}
              data-result-item
              onClick={() => handleSelect(result)}
              onMouseEnter={() => setSelectedIndex(idx)}
              className={`
                w-full text-left px-3 py-2 flex items-center gap-3 transition-colors
                ${isSelected ? 'bg-sage-50 text-content-primary' : 'text-content-secondary hover:bg-surface-card-secondary'}
              `}
            >
              <span className="w-6 h-6 rounded-md bg-surface-card-secondary flex items-center justify-center text-[10px] font-mono text-content-tertiary shrink-0">
                {typeIcons[result.type]}
              </span>
              <div className="min-w-0 flex-1">
                <p className="text-sm font-sans truncate">{result.label}</p>
                {result.detail && (
                  <p className="text-[10px] font-sans text-content-tertiary truncate">{result.detail}</p>
                )}
              </div>
              {isSelected && (
                <kbd className="text-[9px] font-mono text-content-tertiary px-1 py-0.5 bg-surface-card-secondary rounded border border-theme">
                  Enter
                </kbd>
              )}
            </button>
          );
        })}
      </div>
    );
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-[60] flex items-start justify-center pt-[15vh]">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-obsidian-900/50 backdrop-blur-sm"
          onClick={() => setQuickSwitcherOpen(false)}
        />

        {/* Switcher panel */}
        <motion.div
          ref={containerRef}
          initial={{ opacity: 0, scale: 0.95, y: -10 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: -10 }}
          transition={{ duration: 0.15 }}
          className="relative w-full max-w-lg bg-surface-card rounded-xl border border-theme shadow-theme-elevated overflow-hidden"
          role="dialog"
          aria-label="Quick switcher"
          onKeyDown={handleKeyDown}
        >
          {/* Search input */}
          <div className="px-4 py-3 border-b border-theme flex items-center gap-3">
            <svg className="w-4 h-4 text-content-tertiary shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
            <input
              ref={inputRef}
              type="text"
              value={query}
              onChange={e => setQuery(e.target.value)}
              placeholder="Search clients, workspaces, or navigate..."
              className="flex-1 bg-transparent text-sm font-sans text-content-primary placeholder:text-content-tertiary outline-none"
            />
            <kbd className="text-[10px] font-mono text-content-tertiary px-1.5 py-0.5 bg-surface-card-secondary rounded border border-theme">
              Esc
            </kbd>
          </div>

          {/* Results */}
          <div ref={listRef} className="max-h-[50vh] overflow-y-auto">
            {allResults.length === 0 ? (
              <div className="px-4 py-8 text-center">
                <p className="text-sm font-sans text-content-tertiary">No results found</p>
                <p className="text-[10px] font-sans text-content-tertiary mt-1">Try a different search term</p>
              </div>
            ) : (
              <>
                {renderGroup(clientResults, 'client')}
                {renderGroup(workspaceResults, 'workspace')}
                {renderGroup(navResults, 'navigation')}
              </>
            )}
          </div>

          {/* Footer hints */}
          <div className="px-4 py-2 border-t border-theme bg-surface-card-secondary flex items-center gap-4">
            <span className="text-[9px] font-sans text-content-tertiary flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-surface-card rounded border border-theme text-[8px] font-mono">\u2191\u2193</kbd>
              Navigate
            </span>
            <span className="text-[9px] font-sans text-content-tertiary flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-surface-card rounded border border-theme text-[8px] font-mono">\u21B5</kbd>
              Select
            </span>
            <span className="text-[9px] font-sans text-content-tertiary flex items-center gap-1">
              <kbd className="px-1 py-0.5 bg-surface-card rounded border border-theme text-[8px] font-mono">Esc</kbd>
              Close
            </span>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  );
}
