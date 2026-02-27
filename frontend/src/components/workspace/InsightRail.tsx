'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { useWorkspaceContext } from '@/contexts/WorkspaceContext';
import { InsightMicrocopy } from '@/components/workspace/InsightMicrocopy';
import { useWorkspaceInsights, type RiskLevel, type RiskSignal, type ProofReadiness } from '@/hooks/useWorkspaceInsights';
import { AXIS } from '@/utils/marketingMotion';
import { TIMING, EASE } from '@/utils/motionTokens';

/**
 * InsightRail — Sprint 387: Phase LII
 *
 * Adaptive right sidebar that shows contextual insights:
 * - Risk signals (derived from follow-up items + tool trends)
 * - Follow-up summary (disposition breakdown)
 * - Tool coverage meter (progress bar)
 * - Recent activity (last 5 entries)
 *
 * When no engagement selected: shows portfolio-level metrics.
 * Collapse/expand via Cmd+] or toggle button.
 */

const RISK_STYLES: Record<RiskLevel, { border: string; bg: string; dot: string }> = {
  high: { border: 'border-l-clay-500', bg: 'bg-clay-50/80', dot: 'bg-clay-500' },
  medium: { border: 'border-l-oatmeal-400', bg: 'bg-oatmeal-50/80', dot: 'bg-oatmeal-500' },
  low: { border: 'border-l-sage-400', bg: 'bg-sage-50/50', dot: 'bg-sage-500' },
};

function RiskSignalCard({ signal }: { signal: RiskSignal }) {
  const styles = RISK_STYLES[signal.level];
  return (
    <motion.div
      initial={{ opacity: 0, x: -2 }}
      animate={{ opacity: 1, x: 0 }}
      transition={{ duration: TIMING.settle, ease: EASE.emphasis }}
      className={`rounded-lg border-l-[3px] ${styles.border} ${styles.bg} px-3 py-2`}
    >
      <div className="flex items-center gap-2">
        <span className={`w-1.5 h-1.5 rounded-full ${styles.dot}`} />
        <span className="text-xs font-sans font-medium text-content-primary">
          {signal.label}
        </span>
      </div>
      <p className="text-[10px] font-sans text-content-secondary mt-0.5 pl-3.5">
        {signal.detail}
      </p>
    </motion.div>
  );
}

function ToolCoverageMeter({ covered, total }: { covered: number; total: number }) {
  const percentage = total > 0 ? Math.round((covered / total) * 100) : 0;
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider">
          Tool Coverage
        </span>
        <span className="text-[10px] font-mono text-content-secondary">
          {covered}/{total}
        </span>
      </div>
      <div className="h-2 bg-surface-card-secondary rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${percentage}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' as const }}
          className="h-full bg-sage-500 rounded-full"
        />
      </div>
      <p className="text-[10px] font-sans text-content-tertiary mt-1">
        {percentage}% of diagnostic tools executed
      </p>
    </div>
  );
}

const PROOF_LEVEL_STYLES: Record<ProofReadiness['level'], { bar: string; text: string; label: string }> = {
  strong: { bar: 'bg-sage-500', text: 'text-sage-700', label: 'Strong' },
  adequate: { bar: 'bg-sage-400', text: 'text-sage-600', label: 'Adequate' },
  limited: { bar: 'bg-oatmeal-500', text: 'text-oatmeal-700', label: 'Limited' },
  insufficient: { bar: 'bg-clay-500', text: 'text-clay-700', label: 'Insufficient' },
};

function ProofReadinessMeter({ readiness }: { readiness: ProofReadiness }) {
  const style = PROOF_LEVEL_STYLES[readiness.level];
  return (
    <div>
      <div className="flex items-center justify-between mb-1.5">
        <span className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider">
          Proof Readiness
        </span>
        <span className={`text-[10px] font-mono font-medium ${style.text}`}>
          {style.label}
        </span>
      </div>
      <div className="h-2 bg-surface-card-secondary rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${readiness.percentage}%` }}
          transition={{ duration: 0.6, ease: 'easeOut' as const }}
          className={`h-full ${style.bar} rounded-full`}
        />
      </div>
      <p className="text-[10px] font-sans text-content-tertiary mt-1">
        {readiness.toolsWithEvidence}/{readiness.totalTools} tools with evidence data
      </p>
    </div>
  );
}

function FollowUpBreakdown({ summary }: { summary: Record<string, number> }) {
  const dispositions: { key: string; label: string; color: string }[] = [
    { key: 'not_reviewed', label: 'Not Reviewed', color: 'text-clay-600' },
    { key: 'investigated_no_issue', label: 'No Issue', color: 'text-sage-600' },
    { key: 'investigated_adjustment_posted', label: 'Adjustment', color: 'text-oatmeal-600' },
    { key: 'investigated_further_review', label: 'Further Review', color: 'text-clay-600' },
    { key: 'immaterial', label: 'Immaterial', color: 'text-content-tertiary' },
  ];

  return (
    <div className="space-y-1.5">
      {dispositions.map(d => {
        const count = summary[d.key] ?? 0;
        if (count === 0) return null;
        return (
          <div key={d.key} className="flex items-center justify-between">
            <span className="text-[10px] font-sans text-content-secondary">{d.label}</span>
            <span className={`text-[10px] font-mono font-medium ${d.key === 'not_reviewed' && count > 0 ? 'text-clay-600' : d.color}`}>
              {count}
            </span>
          </div>
        );
      })}
    </div>
  );
}

function formatRelativeTime(timestamp: string): string {
  const now = Date.now();
  const then = new Date(timestamp).getTime();
  const diff = now - then;

  const minutes = Math.floor(diff / 60000);
  if (minutes < 1) return 'just now';
  if (minutes < 60) return `${minutes}m ago`;

  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;

  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;

  return new Date(timestamp).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

export function InsightRail() {
  const {
    clients,
    engagements,
    activeEngagement,
    insightRailCollapsed,
    toggleInsightRail,
  } = useWorkspaceContext();

  const {
    riskSignals,
    followUpSummary,
    toolRunTrends,
    toolsCovered,
    totalTools,
    proofReadiness,
    recentActivity,
    isLoading,
  } = useWorkspaceInsights(activeEngagement?.id ?? null);

  const collapsedWidth = 0;
  const expandedWidth = 280;

  const highCount = riskSignals.filter(s => s.level === 'high').length;
  const mediumCount = riskSignals.filter(s => s.level === 'medium').length;

  return (
    <motion.div
      animate={{ width: insightRailCollapsed ? collapsedWidth : expandedWidth }}
      transition={{ type: 'spring' as const, stiffness: 300, damping: 30 }}
      className="h-full border-l border-theme bg-surface-page overflow-hidden flex flex-col"
    >
      <AnimatePresence>
        {!insightRailCollapsed && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="flex flex-col h-full"
          >
            {/* Header */}
            <div className="px-3 py-3 border-b border-theme flex items-center justify-between shrink-0">
              <span className="text-xs font-sans font-medium text-content-tertiary uppercase tracking-wider">
                Insights
              </span>
              <button
                onClick={toggleInsightRail}
                aria-label="Collapse insight rail"
                className="w-7 h-7 flex items-center justify-center rounded-md text-content-tertiary hover:text-content-primary hover:bg-surface-card-secondary transition-colors"
              >
                <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </button>
            </div>

            {/* Scrollable content */}
            <div className="flex-1 overflow-y-auto px-3 py-3">
              <AnimatePresence mode="wait">
                <motion.div
                  key={activeEngagement?.id ?? 'portfolio'}
                  {...AXIS.vertical}
                  className="space-y-5"
                >
              {activeEngagement ? (
                <>
                  {/* Loading state */}
                  {isLoading && (
                    <div className="space-y-3">
                      {[1, 2, 3].map(i => (
                        <div key={i} className="h-14 bg-surface-card-secondary rounded-lg animate-pulse" />
                      ))}
                    </div>
                  )}

                  {/* Intelligence Briefing (feature-flag gated) */}
                  <InsightMicrocopy
                    riskSignals={riskSignals}
                    followUpSummary={followUpSummary}
                    toolRunTrends={toolRunTrends}
                    toolsCovered={toolsCovered}
                    totalTools={totalTools}
                    proofReadiness={proofReadiness}
                    isLoading={isLoading}
                  />

                  {/* Risk Signals */}
                  {!isLoading && riskSignals.length > 0 && (
                    <div>
                      <div className="flex items-center gap-2 mb-2">
                        <span className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider">
                          Risk Signals
                        </span>
                        {highCount > 0 && (
                          <span className="inline-flex items-center justify-center min-w-[16px] h-4 px-1 rounded-sm text-[9px] font-mono bg-clay-50 text-clay-700 border border-clay-200">
                            {highCount}
                          </span>
                        )}
                        {mediumCount > 0 && (
                          <span className="inline-flex items-center justify-center min-w-[16px] h-4 px-1 rounded-sm text-[9px] font-mono bg-oatmeal-100 text-oatmeal-700 border border-oatmeal-300">
                            {mediumCount}
                          </span>
                        )}
                      </div>
                      <div className="space-y-2">
                        {riskSignals.map((signal, i) => (
                          <RiskSignalCard key={i} signal={signal} />
                        ))}
                      </div>
                    </div>
                  )}

                  {!isLoading && riskSignals.length === 0 && (
                    <div className="text-center py-3">
                      <p className="text-[10px] font-sans text-content-tertiary">No active risk signals</p>
                    </div>
                  )}

                  {/* Follow-Up Summary */}
                  {!isLoading && followUpSummary && followUpSummary.total_count > 0 && (
                    <div>
                      <span className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider block mb-2">
                        Follow-Up Items
                      </span>
                      <FollowUpBreakdown summary={followUpSummary.by_disposition} />
                    </div>
                  )}

                  {/* Tool Coverage Meter */}
                  {!isLoading && (
                    <ToolCoverageMeter covered={toolsCovered} total={totalTools} />
                  )}

                  {/* Proof Readiness */}
                  {!isLoading && toolsCovered > 0 && (
                    <ProofReadinessMeter readiness={proofReadiness} />
                  )}

                  {/* Recent Activity */}
                  {!isLoading && recentActivity.length > 0 && (
                    <div>
                      <span className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider block mb-2">
                        Recent Activity
                      </span>
                      <div className="space-y-2">
                        {recentActivity.map(entry => (
                          <div key={entry.id} className="flex items-start gap-2">
                            <span className="w-1 h-1 rounded-full bg-content-tertiary mt-1.5 shrink-0" />
                            <div className="min-w-0">
                              <p className="text-[10px] font-sans text-content-secondary truncate">{entry.action}</p>
                              <p className="text-[9px] font-sans text-content-tertiary">{formatRelativeTime(entry.timestamp)}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </>
              ) : (
                /* Portfolio-level metrics when no engagement selected */
                <div className="space-y-4">
                  <div>
                    <span className="text-[10px] font-sans font-medium text-content-tertiary uppercase tracking-wider block mb-2">
                      Portfolio Overview
                    </span>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between px-3 py-2 bg-surface-card-secondary rounded-lg">
                        <span className="text-xs font-sans text-content-secondary">Total Clients</span>
                        <span className="text-sm font-mono font-medium text-content-primary">{clients.length}</span>
                      </div>
                      <div className="flex items-center justify-between px-3 py-2 bg-surface-card-secondary rounded-lg">
                        <span className="text-xs font-sans text-content-secondary">Active Workspaces</span>
                        <span className="text-sm font-mono font-medium text-content-primary">
                          {engagements.filter(e => e.status === 'active').length}
                        </span>
                      </div>
                      <div className="flex items-center justify-between px-3 py-2 bg-surface-card-secondary rounded-lg">
                        <span className="text-xs font-sans text-content-secondary">Archived</span>
                        <span className="text-sm font-mono font-medium text-content-tertiary">
                          {engagements.filter(e => e.status === 'archived').length}
                        </span>
                      </div>
                    </div>
                  </div>

                  <p className="text-[10px] font-sans text-content-tertiary text-center leading-relaxed">
                    Select a workspace to view diagnostic insights and risk signals.
                  </p>
                </div>
              )}
                </motion.div>
              </AnimatePresence>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.div>
  );
}
