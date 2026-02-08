'use client';

import { motion } from 'framer-motion';
import { createCardStaggerVariants } from '@/utils/themeUtils';
import { formatCurrency } from '@/utils/formatting';
import type { Engagement, MaterialityCascade } from '@/types/engagement';
import { ENGAGEMENT_STATUS_COLORS } from '@/types/engagement';

interface EngagementCardProps {
  engagement: Engagement;
  index: number;
  clientName?: string;
  materiality?: MaterialityCascade | null;
  toolRunCount?: number;
  isSelected?: boolean;
  onClick: (engagement: Engagement) => void;
}

function formatPeriod(dateStr: string): string {
  if (!dateStr) return '';
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
}

export function EngagementCard({
  engagement,
  index,
  clientName,
  materiality,
  toolRunCount = 0,
  isSelected = false,
  onClick,
}: EngagementCardProps) {
  const statusColors = ENGAGEMENT_STATUS_COLORS[engagement.status];
  const variants = createCardStaggerVariants(index);

  return (
    <motion.div
      variants={variants}
      initial="hidden"
      animate="visible"
      whileHover={{ y: -2 }}
      onClick={() => onClick(engagement)}
      className={`
        bg-obsidian-800/50 rounded-xl border cursor-pointer transition-all duration-200
        ${isSelected
          ? 'border-sage-500/50 ring-2 ring-sage-500/20'
          : 'border-obsidian-600/30 hover:border-obsidian-500/50'
        }
      `}
    >
      <div className="p-5">
        {/* Header: Client + Status */}
        <div className="flex items-start justify-between gap-3 mb-3">
          <div className="flex-1 min-w-0">
            <h3 className="font-serif font-semibold text-oatmeal-100 truncate">
              {clientName || `Client #${engagement.client_id}`}
            </h3>
          </div>
          <span className={`
            inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-sans font-medium
            ${statusColors.bg} ${statusColors.text} border ${statusColors.border}
          `}>
            {engagement.status === 'active' ? 'Active' : 'Archived'}
          </span>
        </div>

        {/* Period dates */}
        <div className="flex items-center gap-2 mb-3">
          <svg className="w-4 h-4 text-oatmeal-500 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
          </svg>
          <span className="text-sm font-mono text-oatmeal-400">
            {formatPeriod(engagement.period_start)} &ndash; {formatPeriod(engagement.period_end)}
          </span>
        </div>

        {/* Materiality summary */}
        {materiality && (
          <div className="flex items-center gap-4 mb-3 text-xs font-mono text-oatmeal-400">
            <span>Overall: {formatCurrency(materiality.overall_materiality)}</span>
            <span>PM: {formatCurrency(materiality.performance_materiality)}</span>
            <span>Trivial: {formatCurrency(materiality.trivial_threshold)}</span>
          </div>
        )}

        {/* Footer: Tool runs */}
        <div className="pt-3 border-t border-obsidian-600/30">
          <span className="text-xs font-sans text-oatmeal-500">
            {toolRunCount === 0
              ? 'No tools run yet'
              : `${toolRunCount} tool run${toolRunCount === 1 ? '' : 's'}`}
          </span>
        </div>
      </div>
    </motion.div>
  );
}
