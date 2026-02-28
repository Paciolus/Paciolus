'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import type { ToolRun, ToolRunTrend, ToolName } from '@/types/engagement';
import { TOOL_NAME_LABELS, TOOL_SLUGS } from '@/types/engagement';
import { CONTAINER_VARIANTS, createCardStaggerVariants } from '@/utils/themeUtils';

interface ToolStatusGridProps {
  toolRuns: ToolRun[];
  trends?: ToolRunTrend[];
}

/** All tools in display order, derived from the canonical label map. */
const ALL_TOOLS = Object.keys(TOOL_NAME_LABELS) as ToolName[];

/** SVG icons for each tool. */
function ToolIcon({ tool }: { tool: ToolName }) {
  const iconClass = 'w-5 h-5';
  switch (tool) {
    case 'trial_balance':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      );
    case 'multi_period':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 12l3-3 3 3 4-4M8 21l4-4 4 4M3 4h18M4 4h16v12a1 1 0 01-1 1H5a1 1 0 01-1-1V4z" />
        </svg>
      );
    case 'journal_entry_testing':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
        </svg>
      );
    case 'ap_testing':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      );
    case 'bank_reconciliation':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
        </svg>
      );
    case 'payroll_testing':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      );
    case 'three_way_match':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    case 'revenue_testing':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
        </svg>
      );
    case 'ar_aging':
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      );
    default:
      return (
        <svg className={iconClass} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 17v-2m3 2v-4m3 4v-6m2 10H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      );
  }
}

/** Sprint 311: Trend direction arrow indicator. */
function TrendIndicator({ trend }: { trend: ToolRunTrend | undefined }) {
  if (!trend || trend.direction === null) return null;

  const config = {
    improving: { arrow: '\u2193', label: 'Improving', color: 'text-sage-600' },
    stable: { arrow: '\u2194', label: 'Stable', color: 'text-content-tertiary' },
    degrading: { arrow: '\u2191', label: 'Degrading', color: 'text-clay-600' },
  } as const;

  const { arrow, label, color } = config[trend.direction];

  return (
    <span
      className={`inline-flex items-center gap-0.5 text-xs font-mono ${color}`}
      title={`${label}${trend.score_delta !== null ? ` (${trend.score_delta > 0 ? '+' : ''}${trend.score_delta.toFixed(1)})` : ''}`}
    >
      {arrow}
    </span>
  );
}

function formatRunDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
}

export function ToolStatusGrid({ toolRuns, trends }: ToolStatusGridProps) {
  // Group runs by tool, keeping only the latest
  const latestByTool = new Map<ToolName, { run: ToolRun; count: number }>();

  for (const run of toolRuns) {
    const existing = latestByTool.get(run.tool_name);
    if (!existing) {
      latestByTool.set(run.tool_name, { run, count: 1 });
    } else {
      existing.count += 1;
      if (new Date(run.run_at) > new Date(existing.run.run_at)) {
        existing.run = run;
      }
    }
  }

  // Sprint 311: Build trend lookup by tool_name
  const trendByTool = new Map<string, ToolRunTrend>();
  if (trends) {
    for (const t of trends) {
      trendByTool.set(t.tool_name, t);
    }
  }

  return (
    <div>
      <h3 className="font-serif font-semibold text-content-primary mb-4">
        Diagnostic Status
      </h3>
      <motion.div
        variants={CONTAINER_VARIANTS.fast}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4"
      >
        {ALL_TOOLS.map((tool, index) => {
          const data = latestByTool.get(tool);
          const variants = createCardStaggerVariants(index);

          return (
            <motion.div key={tool} variants={variants}>
              <Link
                href={`/tools/${TOOL_SLUGS[tool]}`}
                className={`
                  group block p-4 rounded-xl border transition-all duration-200
                  ${data
                    ? 'bg-surface-card border-sage-200 hover:border-sage-300 shadow-theme-card hover:shadow-theme-card-hover hover:-translate-y-0.5'
                    : 'bg-surface-card-secondary border-theme hover:border-oatmeal-300 hover:shadow-theme-card hover:-translate-y-0.5'
                  }
                `}
              >
                {/* Tool header */}
                <div className="flex items-center gap-3 mb-3">
                  <div className={`
                    w-9 h-9 rounded-lg flex items-center justify-center transition-transform duration-200
                    group-hover:scale-110 group-hover:rotate-3
                    ${data ? 'bg-sage-50 text-sage-600' : 'bg-oatmeal-100 text-content-tertiary'}
                  `}>
                    <ToolIcon tool={tool} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h4 className="font-sans font-medium text-content-primary text-sm truncate">
                      {TOOL_NAME_LABELS[tool]}
                    </h4>
                  </div>
                </div>

                {/* Status */}
                {data ? (
                  <div className="space-y-1.5">
                    <div className="flex items-center gap-2">
                      <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-sans bg-sage-50 text-sage-700 border border-sage-200">
                        Completed
                      </span>
                      <span className="text-xs font-sans text-content-tertiary">
                        {data.count} run{data.count === 1 ? '' : 's'}
                      </span>
                    </div>
                    <p className="text-xs font-mono text-content-tertiary">
                      Last: {formatRunDate(data.run.run_at)}
                    </p>
                    {data.run.composite_score !== null && (
                      <p className="type-num-xs text-content-secondary flex items-center gap-1">
                        Score: {data.run.composite_score.toFixed(1)}
                        <TrendIndicator trend={trendByTool.get(tool)} />
                      </p>
                    )}
                  </div>
                ) : (
                  <div>
                    <span className="inline-flex items-center px-2 py-0.5 rounded-full text-xs font-sans bg-oatmeal-100 text-content-tertiary border border-theme">
                      Not Started
                    </span>
                  </div>
                )}
              </Link>
            </motion.div>
          );
        })}
      </motion.div>
    </div>
  );
}
