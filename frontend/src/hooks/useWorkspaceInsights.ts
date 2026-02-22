'use client';

import { useState, useEffect, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { apiGet } from '@/utils';
import type { FollowUpSummary, ToolRunTrend, TrendDirection } from '@/types/engagement';

/**
 * useWorkspaceInsights — Sprint 387: Phase LII
 *
 * Fetches engagement-scoped insight data when an active engagement changes:
 * - Follow-up summary (disposition breakdown)
 * - Tool run trends (score direction)
 * - Derives risk signals from high-severity unreviewed follow-ups + degrading trends
 *
 * Returns portfolio-level fallback when no engagement selected.
 *
 * ZERO-STORAGE: All data from API, stored in React state only.
 */

export type RiskLevel = 'high' | 'medium' | 'low';

export interface RiskSignal {
  level: RiskLevel;
  label: string;
  detail: string;
}

export interface ActivityEntry {
  id: number;
  action: string;
  timestamp: string;
  detail: string;
}

export interface ProofReadiness {
  toolsWithEvidence: number;
  totalTools: number;
  percentage: number;
  level: 'strong' | 'adequate' | 'limited' | 'insufficient';
}

export interface WorkspaceInsights {
  riskSignals: RiskSignal[];
  followUpSummary: FollowUpSummary | null;
  toolRunTrends: ToolRunTrend[];
  recentActivity: ActivityEntry[];
  toolsCovered: number;
  totalTools: number;
  proofReadiness: ProofReadiness;
  isLoading: boolean;
}

const TOTAL_TOOLS = 12;

function deriveRiskSignals(
  summary: FollowUpSummary | null,
  trends: ToolRunTrend[],
): RiskSignal[] {
  const signals: RiskSignal[] = [];

  // High-severity unreviewed follow-ups
  if (summary) {
    const notReviewed = summary.by_disposition?.['not_reviewed'] ?? 0;
    const highSeverity = summary.by_severity?.['high'] ?? 0;

    if (highSeverity > 0 && notReviewed > 0) {
      signals.push({
        level: 'high',
        label: 'Unreviewed critical items',
        detail: `${highSeverity} high-severity item${highSeverity !== 1 ? 's' : ''} pending review`,
      });
    }

    if (notReviewed > 3) {
      signals.push({
        level: 'medium',
        label: 'Pending follow-ups',
        detail: `${notReviewed} item${notReviewed !== 1 ? 's' : ''} not yet reviewed`,
      });
    }
  }

  // Degrading tool trends
  const degrading = trends.filter(t => t.direction === 'degrading');
  if (degrading.length > 0) {
    signals.push({
      level: 'high',
      label: 'Score degradation',
      detail: `${degrading.length} tool${degrading.length !== 1 ? 's' : ''} showing declining scores`,
    });
  }

  // Improving trends (positive signal)
  const improving = trends.filter(t => t.direction === 'improving');
  if (improving.length > 0) {
    signals.push({
      level: 'low',
      label: 'Improving trends',
      detail: `${improving.length} tool${improving.length !== 1 ? 's' : ''} showing score improvements`,
    });
  }

  // Sort: high first, then medium, then low
  const order: Record<RiskLevel, number> = { high: 0, medium: 1, low: 2 };
  signals.sort((a, b) => order[a.level] - order[b.level]);

  return signals;
}

export function useWorkspaceInsights(engagementId: number | null): WorkspaceInsights {
  const { token, isAuthenticated } = useAuth();

  const [followUpSummary, setFollowUpSummary] = useState<FollowUpSummary | null>(null);
  const [toolRunTrends, setToolRunTrends] = useState<ToolRunTrend[]>([]);
  const [recentActivity, setRecentActivity] = useState<ActivityEntry[]>([]);
  const [toolsCovered, setToolsCovered] = useState(0);
  const [isLoading, setIsLoading] = useState(false);

  const fetchInsights = useCallback(async () => {
    if (!isAuthenticated || !token || !engagementId) {
      setFollowUpSummary(null);
      setToolRunTrends([]);
      setRecentActivity([]);
      setToolsCovered(0);
      return;
    }

    setIsLoading(true);

    const [summaryRes, trendsRes, activityRes] = await Promise.all([
      apiGet<FollowUpSummary>(
        `/engagements/${engagementId}/follow-up-items/summary`,
        token,
        { skipCache: true },
      ),
      apiGet<ToolRunTrend[]>(
        `/engagements/${engagementId}/tool-run-trends`,
        token,
        { skipCache: true },
      ),
      apiGet<ActivityEntry[]>(
        `/activity/history?limit=5`,
        token,
        { skipCache: true },
      ),
    ]);

    if (summaryRes.ok && summaryRes.data) {
      setFollowUpSummary(summaryRes.data);
    }

    if (trendsRes.ok && trendsRes.data) {
      setToolRunTrends(trendsRes.data);
      setToolsCovered(trendsRes.data.length);
    }

    if (activityRes.ok && activityRes.data) {
      setRecentActivity(activityRes.data.slice(0, 5));
    }

    setIsLoading(false);
  }, [isAuthenticated, token, engagementId]);

  useEffect(() => {
    fetchInsights();
  }, [fetchInsights]);

  const riskSignals = deriveRiskSignals(followUpSummary, toolRunTrends);

  const proofReadiness = deriveProofReadiness(toolsCovered, TOTAL_TOOLS);

  return {
    riskSignals,
    followUpSummary,
    toolRunTrends,
    recentActivity,
    toolsCovered,
    totalTools: TOTAL_TOOLS,
    proofReadiness,
    isLoading,
  };
}

function deriveProofReadiness(covered: number, total: number): ProofReadiness {
  const percentage = total > 0 ? Math.round((covered / total) * 100) : 0;
  const ratio = total > 0 ? covered / total : 0;

  let level: ProofReadiness['level'];
  if (ratio >= 0.85) level = 'strong';
  else if (ratio >= 0.65) level = 'adequate';
  else if (ratio >= 0.40) level = 'limited';
  else level = 'insufficient';

  return { toolsWithEvidence: covered, totalTools: total, percentage, level };
}
