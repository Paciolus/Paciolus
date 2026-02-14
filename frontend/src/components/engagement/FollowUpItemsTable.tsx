'use client';

// NOTE: Decomposition candidate (428 LOC) — extract FollowUpItemRow, FollowUpFilters

import { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { DispositionSelect } from './DispositionSelect';
import { CommentThread } from './CommentThread';
import { StatusBadge } from '@/components/shared/StatusBadge';
import type {
  FollowUpItem,
  FollowUpDisposition,
  FollowUpItemUpdateInput,
} from '@/types/engagement';
import {
  SEVERITY_COLORS,
  DISPOSITION_COLORS,
  DISPOSITION_LABELS,
  TOOL_NAME_LABELS,
  ToolName,
} from '@/types/engagement';
import type { Severity } from '@/types/shared';

interface FollowUpItemsTableProps {
  items: FollowUpItem[];
  isLoading: boolean;
  onUpdateItem: (itemId: number, data: FollowUpItemUpdateInput) => Promise<FollowUpItem | null>;
  onDeleteItem: (itemId: number) => Promise<boolean>;
  currentUserId?: number | null;
}

type SortField = 'created_at' | 'severity' | 'disposition' | 'tool_source';
type SortDir = 'asc' | 'desc';

const SEVERITY_ORDER: Record<Severity, number> = { high: 0, medium: 1, low: 2 };
const ITEMS_PER_PAGE = 25;
const TOOL_SOURCE_COLORS = { bg: 'bg-oatmeal-100', text: 'text-content-secondary', border: 'border-theme' };

type AssignmentFilter = 'all' | 'my_items' | 'unassigned';

export function FollowUpItemsTable({
  items,
  isLoading,
  onUpdateItem,
  onDeleteItem,
  currentUserId,
}: FollowUpItemsTableProps) {
  const [expandedId, setExpandedId] = useState<number | null>(null);
  const [editingNotes, setEditingNotes] = useState<Record<number, string>>({});
  const [savingId, setSavingId] = useState<number | null>(null);

  // Filters
  const [filterSeverity, setFilterSeverity] = useState<string>('all');
  const [filterDisposition, setFilterDisposition] = useState<string>('all');
  const [filterToolSource, setFilterToolSource] = useState<string>('all');
  const [filterAssignment, setFilterAssignment] = useState<AssignmentFilter>('all');
  const [searchQuery, setSearchQuery] = useState('');

  // Sort
  const [sortField, setSortField] = useState<SortField>('created_at');
  const [sortDir, setSortDir] = useState<SortDir>('desc');

  // Pagination
  const [page, setPage] = useState(0);

  // Unique tool sources for filter dropdown
  const toolSources = useMemo(() => {
    const sources = new Set(items.map(i => i.tool_source));
    return Array.from(sources).sort();
  }, [items]);

  // Filtered and sorted items
  const filteredItems = useMemo(() => {
    let result = [...items];

    if (filterSeverity !== 'all') {
      result = result.filter(i => i.severity === filterSeverity);
    }
    if (filterDisposition !== 'all') {
      result = result.filter(i => i.disposition === filterDisposition);
    }
    if (filterToolSource !== 'all') {
      result = result.filter(i => i.tool_source === filterToolSource);
    }
    if (filterAssignment === 'my_items' && currentUserId) {
      result = result.filter(i => i.assigned_to === currentUserId);
    } else if (filterAssignment === 'unassigned') {
      result = result.filter(i => i.assigned_to === null);
    }
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase();
      result = result.filter(i =>
        i.description.toLowerCase().includes(q) ||
        (i.auditor_notes && i.auditor_notes.toLowerCase().includes(q))
      );
    }

    result.sort((a, b) => {
      let cmp = 0;
      switch (sortField) {
        case 'severity':
          cmp = (SEVERITY_ORDER[a.severity] ?? 2) - (SEVERITY_ORDER[b.severity] ?? 2);
          break;
        case 'disposition':
          cmp = a.disposition.localeCompare(b.disposition);
          break;
        case 'tool_source':
          cmp = a.tool_source.localeCompare(b.tool_source);
          break;
        case 'created_at':
        default:
          cmp = new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
          break;
      }
      return sortDir === 'asc' ? cmp : -cmp;
    });

    return result;
  }, [items, filterSeverity, filterDisposition, filterToolSource, filterAssignment, currentUserId, searchQuery, sortField, sortDir]);

  const pageCount = Math.ceil(filteredItems.length / ITEMS_PER_PAGE);
  const pagedItems = filteredItems.slice(page * ITEMS_PER_PAGE, (page + 1) * ITEMS_PER_PAGE);

  const toggleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDir('desc');
    }
  };

  const sortIndicator = (field: SortField) => {
    if (sortField !== field) return '';
    return sortDir === 'asc' ? ' \u25B2' : ' \u25BC';
  };

  const handleDispositionChange = async (itemId: number, disposition: FollowUpDisposition) => {
    setSavingId(itemId);
    await onUpdateItem(itemId, { disposition });
    setSavingId(null);
  };

  const handleSaveNotes = async (itemId: number) => {
    const notes = editingNotes[itemId];
    if (notes === undefined) return;
    setSavingId(itemId);
    await onUpdateItem(itemId, { auditor_notes: notes });
    setSavingId(null);
    setEditingNotes(prev => {
      const next = { ...prev };
      delete next[itemId];
      return next;
    });
  };

  const handleDelete = async (itemId: number) => {
    setSavingId(itemId);
    await onDeleteItem(itemId);
    setSavingId(null);
    if (expandedId === itemId) setExpandedId(null);
  };

  if (isLoading) {
    return (
      <div className="flex items-center gap-3 py-8">
        <div className="w-6 h-6 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
        <span className="text-content-secondary font-sans text-sm">Loading follow-up items...</span>
      </div>
    );
  }

  return (
    <div>
      {/* Filter bar */}
      <div className="flex flex-wrap gap-3 mb-4">
        <input
          type="text"
          placeholder="Search descriptions..."
          value={searchQuery}
          onChange={(e) => { setSearchQuery(e.target.value); setPage(0); }}
          className="px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-sm text-content-primary placeholder-content-tertiary font-sans focus:border-sage-500 focus:outline-none transition-colors w-48"
        />
        <select
          value={filterSeverity}
          onChange={(e) => { setFilterSeverity(e.target.value); setPage(0); }}
          className="px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-sm text-content-primary font-sans focus:border-sage-500 focus:outline-none transition-colors appearance-none cursor-pointer"
        >
          <option value="all">All Severities</option>
          <option value="high">High</option>
          <option value="medium">Medium</option>
          <option value="low">Low</option>
        </select>
        <select
          value={filterDisposition}
          onChange={(e) => { setFilterDisposition(e.target.value); setPage(0); }}
          className="px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-sm text-content-primary font-sans focus:border-sage-500 focus:outline-none transition-colors appearance-none cursor-pointer"
        >
          <option value="all">All Dispositions</option>
          <option value="not_reviewed">Not Reviewed</option>
          <option value="investigated_no_issue">No Issue</option>
          <option value="investigated_adjustment_posted">Adjustment Posted</option>
          <option value="investigated_further_review">Further Review</option>
          <option value="immaterial">Immaterial</option>
        </select>
        <select
          value={filterToolSource}
          onChange={(e) => { setFilterToolSource(e.target.value); setPage(0); }}
          className="px-3 py-1.5 bg-surface-input border border-theme rounded-lg text-sm text-content-primary font-sans focus:border-sage-500 focus:outline-none transition-colors appearance-none cursor-pointer"
        >
          <option value="all">All Tools</option>
          {toolSources.map(src => (
            <option key={src} value={src}>
              {TOOL_NAME_LABELS[src as ToolName] || src}
            </option>
          ))}
        </select>
        {/* Assignment preset filters */}
        <div className="flex items-center gap-1 ml-auto">
          {(['all', 'my_items', 'unassigned'] as const).map(preset => (
            <button
              key={preset}
              onClick={() => { setFilterAssignment(preset); setPage(0); }}
              className={`px-2.5 py-1 text-xs font-sans rounded-lg border transition-colors ${
                filterAssignment === preset
                  ? 'bg-sage-50 text-sage-700 border-sage-200'
                  : 'text-content-tertiary border-theme hover:border-oatmeal-300 hover:text-content-secondary'
              }`}
            >
              {preset === 'all' ? 'All' : preset === 'my_items' ? 'My Items' : 'Unassigned'}
            </button>
          ))}
        </div>
      </div>

      {/* Results count */}
      <p className="text-xs font-sans text-content-tertiary mb-3">
        {filteredItems.length} item{filteredItems.length === 1 ? '' : 's'}
        {filteredItems.length !== items.length && ` (filtered from ${items.length})`}
      </p>

      {/* Table */}
      {filteredItems.length === 0 ? (
        <div className="text-center py-12 bg-surface-card-secondary rounded-xl border border-theme">
          <svg className="w-12 h-12 mx-auto text-content-tertiary mb-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          <p className="text-content-tertiary font-sans text-sm">No follow-up items found</p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm font-sans">
            <thead>
              <tr className="border-b border-theme">
                <th
                  onClick={() => toggleSort('severity')}
                  className="text-left py-2 px-3 text-content-tertiary font-medium cursor-pointer hover:text-content-secondary transition-colors"
                >
                  Severity{sortIndicator('severity')}
                </th>
                <th className="text-left py-2 px-3 text-content-tertiary font-medium">Description</th>
                <th
                  onClick={() => toggleSort('tool_source')}
                  className="text-left py-2 px-3 text-content-tertiary font-medium cursor-pointer hover:text-content-secondary transition-colors"
                >
                  Source{sortIndicator('tool_source')}
                </th>
                <th
                  onClick={() => toggleSort('disposition')}
                  className="text-left py-2 px-3 text-content-tertiary font-medium cursor-pointer hover:text-content-secondary transition-colors"
                >
                  Disposition{sortIndicator('disposition')}
                </th>
                <th
                  onClick={() => toggleSort('created_at')}
                  className="text-left py-2 px-3 text-content-tertiary font-medium cursor-pointer hover:text-content-secondary transition-colors"
                >
                  Date{sortIndicator('created_at')}
                </th>
              </tr>
            </thead>
            <tbody>
              <AnimatePresence mode="popLayout">
                {pagedItems.map((item) => (
                  <motion.tr
                    key={item.id}
                    layout
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className={`
                      border-b border-theme-divider cursor-pointer transition-colors
                      ${expandedId === item.id ? 'bg-sage-50/30' : 'even:bg-oatmeal-50/50 hover:bg-sage-50/40'}
                    `}
                    onClick={() => setExpandedId(expandedId === item.id ? null : item.id)}
                  >
                    <td className="py-2.5 px-3">
                      <StatusBadge label={item.severity.charAt(0).toUpperCase() + item.severity.slice(1)} colors={SEVERITY_COLORS[item.severity]} />
                    </td>
                    <td className="py-2.5 px-3 text-content-secondary max-w-md">
                      <p className="truncate">{item.description}</p>
                      {/* Expanded detail */}
                      <AnimatePresence>
                        {expandedId === item.id && (
                          <motion.div
                            initial={{ height: 0, opacity: 0 }}
                            animate={{ height: 'auto', opacity: 1 }}
                            exit={{ height: 0, opacity: 0 }}
                            transition={{ duration: 0.2 }}
                            className="overflow-hidden"
                            onClick={(e) => e.stopPropagation()}
                          >
                            <div className="pt-3 pb-1 space-y-3">
                              <p className="text-content-secondary text-sm whitespace-pre-wrap">{item.description}</p>

                              {/* Auditor notes */}
                              <div>
                                <label className="block text-xs text-content-tertiary mb-1">Auditor Notes</label>
                                <textarea
                                  value={editingNotes[item.id] ?? item.auditor_notes ?? ''}
                                  onChange={(e) => setEditingNotes(prev => ({ ...prev, [item.id]: e.target.value }))}
                                  placeholder="Add investigation notes..."
                                  className="w-full px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm text-content-primary placeholder-content-tertiary font-sans focus:border-sage-500 focus:outline-none transition-colors resize-y min-h-[60px]"
                                  rows={2}
                                />
                                {editingNotes[item.id] !== undefined && editingNotes[item.id] !== (item.auditor_notes ?? '') && (
                                  <button
                                    onClick={() => handleSaveNotes(item.id)}
                                    disabled={savingId === item.id}
                                    className="mt-1.5 px-3 py-1 text-xs font-sans bg-sage-50 text-sage-700 border border-sage-200 rounded-lg hover:bg-sage-100 transition-colors disabled:opacity-50"
                                  >
                                    {savingId === item.id ? 'Saving...' : 'Save Notes'}
                                  </button>
                                )}
                              </div>

                              {/* Inline disposition */}
                              <div className="flex items-center gap-3">
                                <label className="text-xs text-content-tertiary">Disposition:</label>
                                <DispositionSelect
                                  value={item.disposition}
                                  onChange={(d) => handleDispositionChange(item.id, d)}
                                  disabled={savingId === item.id}
                                />
                              </div>

                              {/* Assignment */}
                              <div className="flex items-center gap-3">
                                <label className="text-xs text-content-tertiary">Assigned:</label>
                                {item.assigned_to ? (
                                  <div className="flex items-center gap-2">
                                    <span className="text-xs font-sans text-sage-600">
                                      {item.assigned_to === currentUserId ? 'You' : `User #${item.assigned_to}`}
                                    </span>
                                    <button
                                      onClick={() => onUpdateItem(item.id, { assigned_to: null })}
                                      disabled={savingId === item.id}
                                      className="text-xs font-sans text-content-tertiary hover:text-content-secondary transition-colors"
                                    >
                                      Unassign
                                    </button>
                                  </div>
                                ) : (
                                  <button
                                    onClick={() => currentUserId && onUpdateItem(item.id, { assigned_to: currentUserId })}
                                    disabled={savingId === item.id || !currentUserId}
                                    className="text-xs font-sans text-content-secondary hover:text-sage-600 transition-colors disabled:opacity-50"
                                  >
                                    Assign to me
                                  </button>
                                )}
                              </div>

                              {/* Comments */}
                              <CommentThread itemId={item.id} />

                              {/* Delete */}
                              <button
                                onClick={() => handleDelete(item.id)}
                                disabled={savingId === item.id}
                                className="text-xs font-sans text-clay-600 hover:text-clay-700 transition-colors disabled:opacity-50"
                              >
                                {savingId === item.id ? 'Deleting...' : 'Delete Item'}
                              </button>
                            </div>
                          </motion.div>
                        )}
                      </AnimatePresence>
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge label={TOOL_NAME_LABELS[item.tool_source as ToolName] || item.tool_source} colors={TOOL_SOURCE_COLORS} />
                    </td>
                    <td className="py-2.5 px-3">
                      <StatusBadge label={DISPOSITION_LABELS[item.disposition]} colors={DISPOSITION_COLORS[item.disposition]} />
                    </td>
                    <td className="py-2.5 px-3 text-content-tertiary font-mono text-xs whitespace-nowrap">
                      {new Date(item.created_at).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}
                    </td>
                  </motion.tr>
                ))}
              </AnimatePresence>
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {pageCount > 1 && (
        <div className="flex items-center justify-between mt-4 pt-3 border-t border-theme-divider">
          <button
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            className="px-3 py-1.5 text-xs font-sans text-content-secondary border border-theme rounded-lg hover:border-oatmeal-300 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Previous
          </button>
          <span className="text-xs font-sans text-content-tertiary">
            Page {page + 1} of {pageCount}
          </span>
          <button
            onClick={() => setPage(p => Math.min(pageCount - 1, p + 1))}
            disabled={page >= pageCount - 1}
            className="px-3 py-1.5 text-xs font-sans text-content-secondary border border-theme rounded-lg hover:border-oatmeal-300 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
}
