'use client';

/**
 * Workspace Detail Page — Sprint 580
 *
 * Extracted from engagements/page.tsx detail view.
 * Shows the 4-tab engagement detail: Status, Follow-Up, Workpapers, Convergence.
 * Accessed from Portfolio ClientCard → engagement row click.
 *
 * ZERO-STORAGE: Displays engagement metadata only, no financial data.
 */

import { useState, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { useParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { useAuthSession } from '@/contexts/AuthSessionContext';
import { useWorkspaceContext } from '@/contexts/WorkspaceContext';
import {
  ToolStatusGrid,
  FollowUpItemsTable,
  WorkpaperIndex,
  ConvergenceTable,
  AnalyticalExpectationsPanel,
} from '@/components/engagement';
import { useAnalyticalExpectations } from '@/hooks/useAnalyticalExpectations';
import { useFollowUpItems } from '@/hooks/useFollowUpItems';
import type { Engagement, ToolRun, MaterialityCascade, WorkpaperIndex as WorkpaperIndexType, ConvergenceResponse } from '@/types/engagement';
import { formatCurrency } from '@/utils/formatting';
import { apiDownload, downloadBlob , apiGet } from '@/utils';
import { fadeUp } from '@/lib/motion';

const DISCLAIMER_TEXT =
  'DIAGNOSTIC WORKSPACE \u2014 NOT AN AUDIT ENGAGEMENT. ' +
  'This workspace organizes data analytics procedures. It does not track audit ' +
  'procedures, assurance engagements, or compliance with ISA/PCAOB standards. ' +
  'The practitioner is solely responsible for all audit planning, execution, and conclusions.';

export default function WorkspaceDetailPage() {
  const params = useParams();
  const engagementId = Number(params.engagementId);
  const clientId = Number(params.clientId);

  const { user, token } = useAuthSession();
  const {
    clients,
    getToolRuns,
    getMateriality,
    getConvergence,
    downloadConvergenceCsv,
    archiveEngagement,
  } = useWorkspaceContext();

  const {
    items: followUpItems,
    isLoading: followUpLoading,
    fetchItems: fetchFollowUpItems,
    updateItem: updateFollowUpItem,
    deleteItem: deleteFollowUpItem,
  } = useFollowUpItems();

  const {
    items: expectations,
    isLoading: expectationsLoading,
    fetchItems: fetchExpectations,
    createItem: createExpectation,
    updateItem: updateExpectation,
    archiveItem: archiveExpectation,
  } = useAnalyticalExpectations();

  const [engagement, setEngagement] = useState<Engagement | null>(null);
  const [toolRuns, setToolRuns] = useState<ToolRun[]>([]);
  const [materiality, setMateriality] = useState<MaterialityCascade | null>(null);
  const [workpaperIndex, setWorkpaperIndex] = useState<WorkpaperIndexType | null>(null);
  const [convergenceData, setConvergenceData] = useState<ConvergenceResponse | null>(null);
  const [convergenceExporting, setConvergenceExporting] = useState(false);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<
    'tools' | 'follow-up' | 'workpaper' | 'convergence' | 'expectations'
  >('tools');

  // Load engagement data
  useEffect(() => {
    if (!token || !engagementId) return;

    setLoading(true);

    const load = async () => {
      try {
        // Fetch engagement detail
        const { data: eng } = await apiGet<Engagement>(
          `/engagements/${engagementId}`,
          token,
        );
        if (eng) setEngagement(eng);

        // Fetch tool runs + materiality in parallel
        const [runs, mat] = await Promise.all([
          getToolRuns(engagementId),
          getMateriality(engagementId),
        ]);
        setToolRuns(runs);
        setMateriality(mat);

        // Background: follow-ups, workpapers, convergence, expectations
        fetchFollowUpItems(engagementId);
        fetchExpectations(engagementId);
        getConvergence(engagementId).then(conv => { if (conv) setConvergenceData(conv); });
        apiGet<WorkpaperIndexType>(
          `/engagements/${engagementId}/workpaper-index`,
          token,
          { skipCache: true },
        ).then(({ data }) => { if (data) setWorkpaperIndex(data); });
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [token, engagementId]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleArchive = useCallback(async () => {
    if (!engagement) return;
    const success = await archiveEngagement(engagement.id);
    if (success) {
      setEngagement(prev => prev ? { ...prev, status: 'archived' as const } : null);
    }
  }, [engagement, archiveEngagement]);

  const clientName = clients.find(c => c.id === clientId)?.name || `Client #${clientId}`;

  if (loading) {
    return (
      <div className="flex items-center justify-center py-16">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
          <p className="text-content-secondary font-sans">Loading workspace...</p>
        </div>
      </div>
    );
  }

  if (!engagement) {
    return (
      <div className="max-w-6xl mx-auto px-6 pt-8">
        <p className="text-content-secondary font-sans">Workspace not found.</p>
        <Link href="/portfolio" className="text-sage-600 hover:text-sage-700 font-sans text-sm mt-2 inline-block">
          Back to Portfolio
        </Link>
      </div>
    );
  }

  return (
    <div className="pb-16 px-6">
      {/* Accent strip */}
      <div className="h-[2px] bg-gradient-to-r from-transparent via-sage-500/20 to-transparent -mx-6 mb-0" />

      {/* Disclaimer (Guardrail 5) */}
      <div className="bg-oatmeal-50 border-b border-oatmeal-200">
        <p className="text-[11px] font-sans text-content-secondary text-center py-1.5 px-4 leading-relaxed">
          {DISCLAIMER_TEXT}
        </p>
      </div>

      <div className="max-w-6xl mx-auto pt-6 space-y-8">
        {/* Back link */}
        <Link
          href="/portfolio"
          className="inline-flex items-center gap-2 text-sm font-sans text-content-secondary hover:text-content-primary transition-colors"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
          </svg>
          Back to Portfolio
        </Link>

        {/* Engagement header */}
        <motion.div
          variants={fadeUp}
          initial="hidden"
          animate="visible"
          className="bg-surface-card rounded-xl border border-sage-200 p-6 shadow-theme-card"
        >
          <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
            <div>
              <h2 className="text-2xl font-serif font-semibold text-content-primary">
                {clientName}
              </h2>
              <div className="flex items-center gap-3 mt-2">
                <span className="text-sm font-mono text-content-secondary">
                  {new Date(engagement.period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  {' \u2013 '}
                  {new Date(engagement.period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                </span>
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-sans ${
                  engagement.status === 'active'
                    ? 'bg-sage-50 text-sage-700 border border-sage-200'
                    : 'bg-oatmeal-100 text-oatmeal-700 border border-oatmeal-300'
                }`}>
                  {engagement.status === 'active' ? 'Active' : 'Archived'}
                </span>
                <span className="inline-flex items-center gap-1.5 text-xs font-mono text-content-secondary">
                  <svg className="w-3.5 h-3.5 text-sage-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                  </svg>
                  {toolRuns.length}/18 tools
                </span>
              </div>
            </div>

            {engagement.status === 'active' && (
              <button
                onClick={handleArchive}
                className="inline-flex items-center gap-2 px-4 py-2 text-sm font-sans text-content-secondary hover:text-clay-600 border border-theme hover:border-clay-200 rounded-lg transition-colors"
              >
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 8h14M5 8a2 2 0 110-4h14a2 2 0 110 4M5 8v10a2 2 0 002 2h10a2 2 0 002-2V8m-9 4h4" />
                </svg>
                Archive
              </button>
            )}
          </div>

          {/* Materiality cascade */}
          {materiality && (
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-theme-divider">
              <div>
                <p className="text-xs font-sans text-content-tertiary mb-1">Overall Materiality</p>
                <p className="text-lg font-mono font-semibold text-content-primary">
                  {formatCurrency(materiality.overall_materiality)}
                </p>
              </div>
              <div>
                <p className="text-xs font-sans text-content-tertiary mb-1">Performance Materiality</p>
                <p className="text-lg font-mono font-semibold text-content-primary">
                  {formatCurrency(materiality.performance_materiality)}
                </p>
              </div>
              <div>
                <p className="text-xs font-sans text-content-tertiary mb-1">Trivial Threshold</p>
                <p className="text-lg font-mono font-semibold text-content-primary">
                  {formatCurrency(materiality.trivial_threshold)}
                </p>
              </div>
            </div>
          )}
        </motion.div>

        {/* Tab navigation */}
        <div className="flex gap-1 border-b border-theme">
          {(['tools', 'follow-up', 'expectations', 'workpaper', 'convergence'] as const).map(tab => {
            const labels = {
              tools: 'Status',
              'follow-up': 'Follow-Up',
              expectations: 'Expectations',
              workpaper: 'Workpapers',
              convergence: 'Convergence',
            };
            const isActive = activeTab === tab;
            return (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2.5 text-sm font-sans transition-colors border-b-2 -mb-[1px] ${
                  isActive
                    ? 'text-sage-600 border-sage-500'
                    : 'text-content-tertiary border-transparent hover:text-content-secondary'
                }`}
              >
                {labels[tab]}
                {tab === 'follow-up' && followUpItems.length > 0 && (
                  <span className="ml-1.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-mono bg-oatmeal-100 text-oatmeal-700">
                    {followUpItems.length}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* Tab content */}
        {activeTab === 'tools' && (
          <ToolStatusGrid toolRuns={toolRuns} />
        )}

        {activeTab === 'follow-up' && (
          <div>
            <div className="mb-4 p-3 bg-oatmeal-100 border border-oatmeal-300 rounded-xl">
              <p className="text-xs font-sans text-oatmeal-700 leading-relaxed">
                <span className="font-semibold">Follow-Up Items Tracker &mdash; Data Anomalies Only.</span>{' '}
                This tracker documents data anomalies requiring investigation. Items listed
                here are NOT findings or control deficiencies until the practitioner completes
                additional procedures and reaches a conclusion.
              </p>
            </div>
            <FollowUpItemsTable
              items={followUpItems}
              isLoading={followUpLoading}
              onUpdateItem={updateFollowUpItem}
              onDeleteItem={deleteFollowUpItem}
              currentUserId={user?.id ?? null}
            />
          </div>
        )}

        {activeTab === 'expectations' && (
          <AnalyticalExpectationsPanel
            engagementId={engagementId}
            items={expectations}
            isLoading={expectationsLoading}
            onCreate={createExpectation}
            onUpdate={updateExpectation}
            onArchive={archiveExpectation}
            onDownload={async () => {
              if (!token) return;
              const { blob, filename, ok } = await apiDownload(
                `/engagements/${engagementId}/export/analytical-expectations`,
                token,
                { method: 'POST' },
              );
              if (ok && blob) {
                downloadBlob(blob, filename ?? 'analytical_expectations.pdf');
              }
            }}
          />
        )}

        {activeTab === 'workpaper' && workpaperIndex && (
          <WorkpaperIndex index={workpaperIndex} />
        )}
        {activeTab === 'workpaper' && !workpaperIndex && (
          <div className="text-center py-12 bg-surface-card-secondary rounded-xl border border-theme">
            <p className="text-content-tertiary font-sans text-sm">Loading workpaper index...</p>
          </div>
        )}

        {activeTab === 'convergence' && convergenceData && (
          <ConvergenceTable
            data={convergenceData}
            onExportCsv={async () => {
              setConvergenceExporting(true);
              await downloadConvergenceCsv(engagementId);
              setConvergenceExporting(false);
            }}
            isExporting={convergenceExporting}
          />
        )}
        {activeTab === 'convergence' && !convergenceData && (
          <div className="text-center py-12 bg-surface-card-secondary rounded-xl border border-theme">
            <p className="text-content-tertiary font-sans text-sm">Loading convergence index...</p>
          </div>
        )}
      </div>
    </div>
  );
}
