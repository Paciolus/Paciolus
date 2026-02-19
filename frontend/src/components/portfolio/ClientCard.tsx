'use client';

import { motion } from 'framer-motion';
import Link from 'next/link';
import type { Client } from '@/types/client';
import { INDUSTRY_LABELS, formatFiscalYearEnd } from '@/types/client';
import { createCardStaggerVariants } from '@/utils';

/**
 * ClientCard - Sprint 17 Portfolio Dashboard Component
 *
 * Design: "Premium Bound Ledger" aesthetic
 * - Cards resemble traditional accounting ledgers
 * - Oat & Obsidian palette with subtle texture
 * - Left spine accent mimicking book binding
 *
 * Tier 1 Animations:
 * - Staggered entrance via parent container
 * - Button micro-interactions (translateY on hover)
 *
 * ZERO-STORAGE: Displays metadata only, no financial data
 */

interface ClientCardProps {
  client: Client;
  index: number;
  lastAuditDate?: string | null;
  onEdit?: (client: Client) => void;
  onDelete?: (client: Client) => void;
}

/**
 * Get industry color classes based on industry type.
 * Uses semantic colors from Oat & Obsidian palette.
 */
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

/**
 * Format the last audit date for display.
 */
function formatLastAudit(dateString: string | null | undefined): string {
  if (!dateString) return 'Never audited';

  try {
    const date = new Date(dateString);
    const now = new Date();
    const diffDays = Math.floor((now.getTime() - date.getTime()) / (1000 * 60 * 60 * 24));

    if (diffDays === 0) return 'Today';
    if (diffDays === 1) return 'Yesterday';
    if (diffDays < 7) return `${diffDays} days ago`;
    if (diffDays < 30) return `${Math.floor(diffDays / 7)} weeks ago`;

    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' });
  } catch {
    return 'Unknown';
  }
}

/**
 * Get fiscal year status (upcoming, current, past).
 */
function getFiscalYearStatus(fiscalYearEnd: string): { label: string; color: string } {
  const [month = 0, day = 1] = fiscalYearEnd.split('-').map(Number);
  const now = new Date();
  const currentYear = now.getFullYear();
  const fyeDate = new Date(currentYear, month - 1, day);

  // If FYE has passed this year, next one is next year
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

export function ClientCard({ client, index, lastAuditDate, onEdit, onDelete }: ClientCardProps) {
  const industryColors = getIndustryColors(client.industry);
  const fyeStatus = getFiscalYearStatus(client.fiscal_year_end);

  // Staggered entrance animation (40ms delay per card)
  const cardVariants = createCardStaggerVariants(index, 40);

  // Button hover micro-interaction
  const buttonVariants = {
    rest: { y: 0 },
    hover: { y: -2 },
    tap: { y: 0, scale: 0.98 },
  };

  return (
    <motion.div
      variants={cardVariants}
      initial="hidden"
      animate="visible"
      className="group relative"
    >
      {/* Premium Bound Ledger Card */}
      <div className="relative bg-surface-card rounded-xl overflow-hidden border border-theme hover:border-theme transition-colors">
        {/* Left Spine (Book Binding Effect) */}
        <div className="absolute left-0 top-0 bottom-0 w-1.5 bg-gradient-to-b from-oatmeal-400 via-oatmeal-500 to-oatmeal-600" />

        {/* Subtle texture overlay */}
        <div className="absolute inset-0 bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-surface-card-secondary/30 via-transparent to-transparent pointer-events-none" />

        <div className="relative p-5 pl-6">
          {/* Header: Name + Industry Badge */}
          <div className="flex items-start justify-between gap-3 mb-4">
            <div className="min-w-0 flex-1">
              <h3 className="font-serif font-semibold text-lg text-content-primary truncate group-hover:text-content-primary transition-colors">
                {client.name}
              </h3>
              <p className="text-content-tertiary text-sm font-sans mt-0.5">
                Client since {new Date(client.created_at).toLocaleDateString('en-US', { month: 'short', year: 'numeric' })}
              </p>
            </div>

            {/* Industry Badge */}
            <span className={`inline-flex items-center px-2.5 py-1 rounded-full text-xs font-sans font-medium border ${industryColors.bg} ${industryColors.text} ${industryColors.border}`}>
              {INDUSTRY_LABELS[client.industry] || 'Other'}
            </span>
          </div>

          {/* Metadata Row */}
          <div className="flex items-center gap-4 text-sm font-sans mb-4">
            {/* Last Audit */}
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
              </svg>
              <span className="text-content-secondary">
                {formatLastAudit(lastAuditDate)}
              </span>
            </div>

            {/* Fiscal Year End Status */}
            <div className="flex items-center gap-1.5">
              <svg className="w-4 h-4 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <span className={fyeStatus.color}>
                {fyeStatus.label}
              </span>
            </div>
          </div>

          {/* Divider */}
          <div className="h-px bg-border-theme mb-4" />

          {/* Action Buttons */}
          <div className="flex items-center gap-2">
            {/* Open Audit Button - Primary CTA */}
            <Link href={`/?client=${client.id}`} className="flex-1">
              <motion.button
                variants={buttonVariants}
                initial="rest"
                whileHover="hover"
                whileTap="tap"
                className="w-full px-4 py-2.5 bg-sage-500/10 border border-sage-500/30 rounded-lg text-sage-400 text-sm font-sans font-medium hover:bg-sage-500/20 hover:border-sage-500/50 transition-colors"
              >
                Open Audit
              </motion.button>
            </Link>

            {/* Edit Button */}
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

            {/* Delete Button */}
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
        </div>
      </div>
    </motion.div>
  );
}

export default ClientCard;
