'use client';

import { useState, useCallback } from 'react';
import Link from 'next/link';
import { motion, AnimatePresence } from 'framer-motion';
import type { Client, ClientEngagementSummary } from '@/types/client';
import type { Engagement } from '@/types/engagement';
import { INDUSTRY_LABELS, formatFiscalYearEnd } from '@/types/client';
import { useAuthSession } from '@/contexts/AuthSessionContext';
import { apiGet } from '@/utils/apiClient';
import { fadeUp } from '@/lib/motion';

/**
 * ClientCard — Sprint 580: Unified Portfolio + Workspaces
 *
 * Enhanced from Sprint 17 "Premium Bound Ledger" design.
 * Now shows engagement summary and expandable workspace list,
 * replacing the separate Workspaces page.
 *
 * ZERO-STORAGE: Displays metadata only, no financial data.
 */

interface ClientCardProps {
  client: Client;
  index: number;
  engagementSummary?: ClientEngagementSummary | null;
  onEdit?: (client: Client) => void;
  onDelete?: (client: Client) => void;
  onCreateWorkspace?: (clientId: number) => void;
}

function getIndustryColors(industry: string): { bg: string; text: string; border: string } {
  const colors: Record<string, { bg: string; text: string; border: string }> = {
    technology: { bg: 'bg-sage-500/10', text: 'text-sage-400', border: 'border-sage-500/30' },
    healthcare: { bg: 'bg-sage-500/10', text: 'text-sage-400', border: 'border-sage-500/30' },
    financial_services: { bg: 'bg-oatmeal-500/10', text: 'text-content-primary', border: 'border-oatmeal-500/30' },
    manufacturing: { bg: 'bg-oatmeal-500/10', text: 'text-content-secondary', border: 'border-oatmeal-500/30' },
    retail: { bg: 'bg-clay-500/10', text: 'text-clay-400', border: 'border-clay-500/30' },
    professional_services: { bg: 'bg-sage-500/10', text: 'text-sage-400', border: 'border-sage-500/30' },
    real_estate: { bg: 'bg-oatmeal-500/10', text: 'text-content-primary', border: 'border-oatmeal-500/30' },
    construction: { bg: 'bg-clay-500/10', text: 'text-clay-400', border: 'border-clay-500/30' },
    hospitality: { bg: 'bg-sage-500/10', text: 'text-sage-400', border: 'border-sage-500/30' },
    nonprofit: { bg: 'bg-sage-500/10', text: 'text-sage-400', border: 'border-sage-500/30' },
    education: { bg: 'bg-oatmeal-500/10', text: 'text-content-primary', border: 'border-oatmeal-500/30' },
    other: { bg: 'bg-oatmeal-500/10', text: 'text-content-secondary', border: 'border-oatmeal-500/30' },
  };
  return colors[industry] ?? colors['other']!;
}

function getFiscalYearStatus(fiscalYearEnd: string): { label: string; color: string } {
  const [month = 0, day = 1] = fiscalYearEnd.split('-').map(Number);
  const now = new Date();
  const currentYear = now.getFullYear();
  const fyeDate = new Date(currentYear, month - 1, day);

  if (fyeDate < now) {
    fyeDate.setFullYear(currentYear + 1);
  }

  const daysUntil = Math.floor((fyeDate.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));

  if (daysUntil <= 30) {
    return { label: 'FYE Soon', color: 'text-clay-400' };
  } else if (daysUntil <= 90) {
    return { label: 'Q4', color: 'text-content-primary' };
  }
  return { label: formatFiscalYearEnd(fiscalYearEnd), color: 'text-content-tertiary' };
}

function formatPeriod(start: string, end: string): string {
  const s = new Date(start);
  const e = new Date(end);
  return `${s.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })} \u2013 ${e.toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}`;
}

interface EngagementListResponse {
  items: Engagement[];
  total_count: number;
  page: number;
  page_size: number;
}

export function ClientCard({ client, index, engagementSummary, onEdit, onDelete, onCreateWorkspace }: ClientCardProps) {
  const { token } = useAuthSession();
  const industryColors = getIndustryColors(client.industry);
  const fyeStatus = getFiscalYearStatus(client.fiscal_year_end);
  const [expanded, setExpanded] = useState(false);
  const [engagements, setEngagements] = useState<Engagement[]>([]);
  const [engagementsLoading, setEngagementsLoading] = useState(false);

  const buttonVariants = {
    rest: { y: 0 },
    hover: { y: -2 },
    tap: { y: 0, scale: 0.98 },
  } as const;

  // Lazy-load engagements when expanding
  const handleToggleExpand = useCallback(async () => {
    const willExpand = !expanded;
    setExpanded(willExpand);

    if (willExpand && engagements.length === 0 && token) {
      setEngagementsLoading(true);
      try {
        const { data, ok } = await apiGet<EngagementListResponse>(
          `/engagements?client_id=${client.id}&page_size=20`,
          token
        );
        if (ok && data) {
          setEngagements(data.items);
        }
      } catch {
        // Silently fail — summary data still visible
      } finally {
        setEngagementsLoading(false);
      }
    }
  }, [expanded, engagements.length, token, client.id]);

  // Workspace summary line
  const summaryParts: string[] = [];
  if (engagementSummary) {
    if (engagementSummary.active_count > 0) {
      summaryParts.push(`${engagementSummary.active_count} active workspace${engagementSummary.active_count === 1 ? '' : 's'}`);
    }
    if (engagementSummary.tool_run_count > 0) {
      summaryParts.push(`${engagementSummary.tool_run_count} tool run${engagementSummary.tool_run_count === 1 ? '' : 's'}`);
    }
  }
  const workspaceSummary = summaryParts.length > 0 ? summaryParts.join(' \u00B7 ') : 'No workspaces yet';

  return (
    <motion.div
      variants={fadeUp}
      initial="hidden"
      animate="visible"
      className="group relative"
    >
      <div className="relative bg-surface-card rounded-xl overflow-hidden border border-theme hover:border-oatmeal-300 hover:shadow-theme-card-hover transition-all duration-200">
        {/* Left Spine */}
        <div className="absolute left-0 top-0 bottom-0 w-2 bg-gradient-to-b from-oatmeal-400 via-oatmeal-500 to-oatmeal-600 group-hover:from-sage-400 group-hover:via-sage-500 group-hover:to-sage-600 transition-all duration-300" />

        {/* Texture overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-surface-card-secondary/30 via-transparent to-transparent pointer-events-none" />

        <div className="relative p-5 pl-6">
          {/* Header: Name + Industry Badge */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="min-w-0 flex-1">
              <h3 className="font-serif font-semibold text-lg text-content-primary truncate">
                {client.name}
              </h3>
              <p className="text-content-tertiary text-sm font-sans mt-0.5">
                Client since {new Date(client.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
              </p>
            </div>
            <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-sans font-medium border ${industryColors.bg} ${industryColors.text} ${industryColors.border}`}>
              {INDUSTRY_LABELS[client.industry] || 'Other'}
            </span>
          </div>

          {/* Metadata Row: Workspace Summary + FYE */}
          <div className="flex items-center gap-4 text-sm font-sans mb-4">
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6z" />
              </svg>
              <span className="text-content-secondary">{workspaceSummary}</span>
            </div>
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span className={fyeStatus.color}>{fyeStatus.label}</span>
            </div>
          </div>

          <div className="h-px bg-border-theme mb-4" />

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {/* Expand Workspaces toggle */}
            <motion.button
              variants={buttonVariants}
              initial="rest"
              whileHover="hover"
              whileTap="tap"
              onClick={handleToggleExpand}
              className="flex-1 px-4 py-2.5 bg-sage-500/10 border border-sage-500/30 rounded-lg text-sage-400 text-sm font-sans font-medium hover:bg-sage-500/20 hover:border-sage-500/50 transition-colors flex items-center justify-center gap-2"
            >
              <span>Workspaces</span>
              <svg
                className={`w-4 h-4 transition-transform duration-200 ${expanded ? 'rotate-180' : ''}`}
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </motion.button>

            {/* Edit */}
            {onEdit && (
              <motion.button
                variants={buttonVariants}
                initial="rest"
                whileHover="hover"
                whileTap="tap"
                onClick={() => onEdit(client)}
                className="p-2.5 bg-surface-card-secondary border border-theme rounded-lg text-content-secondary hover:bg-surface-card hover:text-content-primary transition-colors"
                aria-label="Edit client"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                </svg>
              </motion.button>
            )}

            {/* Delete */}
            {onDelete && (
              <motion.button
                variants={buttonVariants}
                initial="rest"
                whileHover="hover"
                whileTap="tap"
                onClick={() => onDelete(client)}
                className="p-2.5 bg-surface-card-secondary border border-theme rounded-lg text-content-secondary hover:bg-clay-500/10 hover:border-clay-500/30 hover:text-clay-400 transition-colors"
                aria-label="Delete client"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                </svg>
              </motion.button>
            )}
          </div>

          {/* Expandable Workspaces Section */}
          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                transition={{ duration: 0.2, ease: [0.16, 1, 0.3, 1] }}
                className="overflow-hidden"
              >
                <div className="pt-4 mt-4 border-t border-theme">
                  {engagementsLoading ? (
                    <div className="space-y-2">
                      {[1, 2].map(i => (
                        <div key={i} className="h-10 bg-oatmeal-200/50 rounded-lg animate-pulse" />
                      ))}
                    </div>
                  ) : engagements.length === 0 ? (
                    <p className="text-content-tertiary text-xs font-sans text-center py-2">
                      No workspaces created for this client yet.
                    </p>
                  ) : (
                    <div className="space-y-1.5">
                      {engagements.map(eng => (
                        <Link
                          key={eng.id}
                          href={`/portfolio/${client.id}/workspace/${eng.id}`}
                          className="flex items-center justify-between px-3 py-2 rounded-lg hover:bg-oatmeal-100/60 transition-colors group/row"
                        >
                          <div className="flex items-center gap-2 min-w-0">
                            <span className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${
                              eng.status === 'active' ? 'bg-sage-500' : 'bg-oatmeal-400'
                            }`} />
                            <span className="text-xs font-sans text-content-primary truncate">
                              {formatPeriod(eng.period_start, eng.period_end)}
                            </span>
                            <span className={`text-[10px] font-sans font-medium px-1.5 py-0.5 rounded-full border ${
                              eng.status === 'active'
                                ? 'bg-sage-50 text-sage-700 border-sage-200'
                                : 'bg-oatmeal-100 text-content-secondary border-oatmeal-300'
                            }`}>
                              {eng.status === 'active' ? 'Active' : 'Archived'}
                            </span>
                          </div>
                          <svg className="w-3.5 h-3.5 text-content-tertiary group-hover/row:text-sage-600 transition-colors flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                          </svg>
                        </Link>
                      ))}
                    </div>
                  )}

                  {/* New Workspace button */}
                  {onCreateWorkspace && (
                    <button
                      onClick={() => onCreateWorkspace(client.id)}
                      className="mt-2 w-full px-3 py-2 rounded-lg border border-dashed border-oatmeal-300 text-xs font-sans font-medium text-content-secondary hover:border-sage-400 hover:text-sage-600 hover:bg-sage-50/30 transition-colors flex items-center justify-center gap-1.5"
                    >
                      <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                      </svg>
                      New Workspace
                    </button>
                  )}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </motion.div>
  );
}

export default ClientCard;
