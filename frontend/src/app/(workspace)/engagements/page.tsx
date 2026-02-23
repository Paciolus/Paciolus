'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import { EngagementList, CreateEngagementModal, ToolStatusGrid, FollowUpItemsTable, WorkpaperIndex, ConvergenceTable } from '@/components/engagement';
import { useFollowUpItems } from '@/hooks/useFollowUpItems';
import { useAuth } from '@/contexts/AuthContext';
import { useWorkspaceContext } from '@/contexts/WorkspaceContext';
import type { Engagement, ToolRun, MaterialityCascade, WorkpaperIndex as WorkpaperIndexType, ConvergenceResponse } from '@/types/engagement';
import { formatCurrency } from '@/utils/formatting';
import { apiGet } from '@/utils';

/**
 * Diagnostic Workspace Page — Sprint 385: Phase LII Refactor
 *
 * Refactored from standalone page to workspace shell consumer.
 * - Nav removed (replaced by CommandBar in WorkspaceShell)
 * - Footer removed (replaced by WorkspaceFooter in WorkspaceShell)
 * - Auth redirect removed (handled by (workspace)/layout.tsx)
 * - useClients()/useEngagement() replaced with useWorkspaceContext()
 * - Non-dismissible disclaimer banner preserved (Guardrail 5)
 * - All modals, grid rendering, and page-specific logic intact
 *
 * Guardrails:
 * - Non-dismissible disclaimer banner (Guardrail 5)
 * - "Diagnostic Workspace" terminology (Guardrail 4) -- no audit language
 * - Oat & Obsidian palette only
 *
 * ZERO-STORAGE: Displays engagement metadata only, no financial data.
 */

/** Disclaimer banner text (Guardrail 5: non-dismissible). */
const DISCLAIMER_TEXT =
  'DIAGNOSTIC WORKSPACE \u2014 NOT AN AUDIT ENGAGEMENT. ' +
  'This workspace organizes data analytics procedures. It does not track audit ' +
  'procedures, assurance engagements, or compliance with ISA/PCAOB standards. ' +
  'The practitioner is solely responsible for all audit planning, execution, and conclusions.';

function EngagementsPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { user, token } = useAuth();
  const {
    clients,
    engagements,
    engagementsLoading,
    engagementsError,
    fetchEngagements,
    createEngagement,
    archiveEngagement,
    getToolRuns,
    getMateriality,
    getConvergence,
    downloadConvergenceCsv,
  } = useWorkspaceContext();
  const {
    items: followUpItems,
    isLoading: followUpLoading,
    fetchItems: fetchFollowUpItems,
    updateItem: updateFollowUpItem,
    deleteItem: deleteFollowUpItem,
  } = useFollowUpItems();

  // Selected engagement state
  const [selectedEngagement, setSelectedEngagement] = useState<Engagement | null>(null);
  const [selectedToolRuns, setSelectedToolRuns] = useState<ToolRun[]>([]);
  const [selectedMateriality, setSelectedMateriality] = useState<MaterialityCascade | null>(null);
  const [selectionLoading, setSelectionLoading] = useState(false);

  // Workpaper index
  const [workpaperIndex, setWorkpaperIndex] = useState<WorkpaperIndexType | null>(null);

  // Convergence index (Sprint 288)
  const [convergenceData, setConvergenceData] = useState<ConvergenceResponse | null>(null);
  const [convergenceExporting, setConvergenceExporting] = useState(false);

  // Materiality + tool runs cache for list view (avoids N+1 re-fetch on selection)
  const [materialityMap, setMaterialityMap] = useState<Record<number, MaterialityCascade>>({});
  const [toolRunsMap, setToolRunsMap] = useState<Record<number, ToolRun[]>>({});
  const [toolRunCountMap, setToolRunCountMap] = useState<Record<number, number>>({});

  // Modal
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Active detail tab
  const [activeTab, setActiveTab] = useState<'tools' | 'follow-up' | 'workpaper' | 'convergence'>('tools');

  // Load materiality + tool run counts for engagement list
  useEffect(() => {
    if (engagements.length === 0) return;

    const loadSummaries = async () => {
      const matMap: Record<number, MaterialityCascade> = {};
      const runsMap: Record<number, ToolRun[]> = {};
      const runCountMap: Record<number, number> = {};

      await Promise.all(
        engagements.map(async (eng) => {
          const [mat, runs] = await Promise.all([
            getMateriality(eng.id),
            getToolRuns(eng.id),
          ]);
          if (mat) matMap[eng.id] = mat;
          runsMap[eng.id] = runs;
          runCountMap[eng.id] = runs.length;
        })
      );

      setMaterialityMap(matMap);
      setToolRunsMap(runsMap);
      setToolRunCountMap(runCountMap);
    };

    loadSummaries();
  }, [engagements.length]); // eslint-disable-line react-hooks/exhaustive-deps

  // Read ?engagement=X from URL on mount
  useEffect(() => {
    if (engagements.length === 0) return;

    const engagementId = searchParams.get('engagement');
    if (engagementId && !selectedEngagement) {
      const id = parseInt(engagementId, 10);
      const found = engagements.find(e => e.id === id);
      if (found) {
        handleSelectEngagement(found);
      }
    }
  }, [engagements.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSelectEngagement = useCallback(async (engagement: Engagement) => {
    setSelectionLoading(true);
    setSelectedEngagement(engagement);
    setActiveTab('tools');

    // Use cached data from list load if available, otherwise fetch
    const cachedRuns = toolRunsMap[engagement.id];
    const cachedMat = materialityMap[engagement.id];

    if (cachedRuns && cachedMat) {
      setSelectedToolRuns(cachedRuns);
      setSelectedMateriality(cachedMat);
      setSelectionLoading(false);
    } else {
      const [runs, mat] = await Promise.all([
        cachedRuns ? Promise.resolve(cachedRuns) : getToolRuns(engagement.id),
        cachedMat ? Promise.resolve(cachedMat) : getMateriality(engagement.id),
      ]);

      setSelectedToolRuns(runs);
      setSelectedMateriality(mat);
      setSelectionLoading(false);
    }

    // Load follow-up items, workpaper index, and convergence in background
    fetchFollowUpItems(engagement.id);
    getConvergence(engagement.id).then((conv) => {
      if (conv) setConvergenceData(conv);
    });
    if (token) {
      apiGet<WorkpaperIndexType>(
        `/engagements/${engagement.id}/workpaper-index`,
        token,
        { skipCache: true },
      ).then(({ data }) => {
        if (data) setWorkpaperIndex(data);
      });
    }

    // Sync to URL
    const params = new URLSearchParams(searchParams.toString());
    params.set('engagement', engagement.id.toString());
    router.replace(`/engagements?${params.toString()}`, { scroll: false });
  }, [toolRunsMap, materialityMap, getToolRuns, getMateriality, getConvergence, fetchFollowUpItems, token, searchParams, router]);

  const handleDeselectEngagement = useCallback(() => {
    setSelectedEngagement(null);
    setSelectedToolRuns([]);
    setSelectedMateriality(null);
    setWorkpaperIndex(null);
    setConvergenceData(null);

    const params = new URLSearchParams(searchParams.toString());
    params.delete('engagement');
    const qs = params.toString();
    router.replace(qs ? `/engagements?${qs}` : '/engagements', { scroll: false });
  }, [searchParams, router]);

  const handleCreateEngagement = async (data: Parameters<typeof createEngagement>[0]): Promise<boolean> => {
    const result = await createEngagement(data);
    return result !== null;
  };

  const handleArchiveEngagement = async () => {
    if (!selectedEngagement) return;
    const success = await archiveEngagement(selectedEngagement.id);
    if (success) {
      setSelectedEngagement(prev => prev ? { ...prev, status: 'archived' as const } : null);
    }
  };

  const handleFilterClient = (clientId?: number) => {
    fetchEngagements(clientId, undefined, 1);
    handleDeselectEngagement();
  };

  const handleFilterStatus = (status?: string) => {
    fetchEngagements(undefined, status, 1);
    handleDeselectEngagement();
  };

  const clientNameMap = new Map(clients.map(c => [c.id, c.name]));

  return (
    <div className="pb-16 px-6">
      {/* Non-dismissible disclaimer banner (Guardrail 5) */}
      <div className="bg-oatmeal-100 border-b border-oatmeal-300">
        <div className="max-w-6xl mx-auto px-6 py-2">
          <p className="text-xs font-sans text-oatmeal-700 text-center leading-relaxed">
            {DISCLAIMER_TEXT}
          </p>
        </div>
      </div>

      <div className="max-w-6xl mx-auto pt-6">
        {/* Page Header */}
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
          <div>
            <h1 className="text-3xl md:text-4xl font-serif font-bold text-content-primary">
              Diagnostic Workspace
            </h1>
            <p className="text-content-secondary font-sans mt-1">
              {engagements.length === 0
                ? 'Create your first workspace to get started'
                : `${engagements.length} workspace${engagements.length === 1 ? '' : 's'}`}
            </p>
          </div>

          <motion.button
            initial={{ y: 0 }}
            whileHover={{ y: -2 }}
            whileTap={{ y: 0, scale: 0.98 }}
            onClick={() => setShowCreateModal(true)}
            className="inline-flex items-center gap-2 px-5 py-3 bg-sage-600 hover:bg-sage-700 text-white font-sans font-bold rounded-xl transition-colors shadow-theme-card"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
            </svg>
            New Workspace
          </motion.button>
        </div>

        {/* Error */}
        {engagementsError && (
          <div className="mb-6 p-4 bg-theme-error-bg border border-theme-error-border border-l-4 border-l-clay-500 rounded-xl" role="alert">
            <p className="text-theme-error-text font-sans text-sm">{engagementsError}</p>
            <button
              onClick={() => fetchEngagements()}
              className="mt-2 px-4 py-2 bg-surface-card border border-oatmeal-300 rounded-lg text-content-primary font-sans text-sm hover:bg-surface-card-secondary transition-colors"
            >
              Try Again
            </button>
          </div>
        )}

        {/* Two-panel layout when engagement selected */}
        {selectedEngagement ? (
          <div className="space-y-8">
            {/* Back button */}
            <button
              onClick={handleDeselectEngagement}
              className="inline-flex items-center gap-2 text-sm font-sans text-content-secondary hover:text-content-primary transition-colors"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to all workspaces
            </button>

            {/* Selected engagement detail */}
            <motion.div
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              className="bg-surface-card rounded-xl border border-sage-200 p-6 shadow-theme-card"
            >
              <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
                <div>
                  <h2 className="text-2xl font-serif font-semibold text-content-primary">
                    {clientNameMap.get(selectedEngagement.client_id) || `Client #${selectedEngagement.client_id}`}
                  </h2>
                  <div className="flex items-center gap-3 mt-2">
                    <span className="text-sm font-mono text-content-secondary">
                      {new Date(selectedEngagement.period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      {' \u2013 '}
                      {new Date(selectedEngagement.period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                    </span>
                    <span className={`
                      inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-sans
                      ${selectedEngagement.status === 'active'
                        ? 'bg-sage-50 text-sage-700 border border-sage-200'
                        : 'bg-oatmeal-100 text-oatmeal-700 border border-oatmeal-300'
                      }
                    `}>
                      {selectedEngagement.status === 'active' ? 'Active' : 'Archived'}
                    </span>
                  </div>
                </div>

                {selectedEngagement.status === 'active' && (
                  <button
                    onClick={handleArchiveEngagement}
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
              {selectedMateriality && (
                <div className="grid grid-cols-3 gap-4 pt-4 border-t border-theme-divider">
                  <div>
                    <p className="text-xs font-sans text-content-tertiary mb-1">Overall Materiality</p>
                    <p className="text-lg font-mono font-semibold text-content-primary">
                      {formatCurrency(selectedMateriality.overall_materiality)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-sans text-content-tertiary mb-1">Performance Materiality</p>
                    <p className="text-lg font-mono font-semibold text-content-primary">
                      {formatCurrency(selectedMateriality.performance_materiality)}
                    </p>
                  </div>
                  <div>
                    <p className="text-xs font-sans text-content-tertiary mb-1">Trivial Threshold</p>
                    <p className="text-lg font-mono font-semibold text-content-primary">
                      {formatCurrency(selectedMateriality.trivial_threshold)}
                    </p>
                  </div>
                </div>
              )}
            </motion.div>

            {/* Tab navigation */}
            <div className="flex gap-1 border-b border-theme">
              {(['tools', 'follow-up', 'workpaper', 'convergence'] as const).map((tab) => {
                const labels = { tools: 'Diagnostic Status', 'follow-up': 'Follow-Up Items', workpaper: 'Workpaper Index', convergence: 'Convergence Index' };
                const isActive = activeTab === tab;
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`
                      px-4 py-2.5 text-sm font-sans transition-colors border-b-2 -mb-[1px]
                      ${isActive
                        ? 'text-sage-600 border-sage-500'
                        : 'text-content-tertiary border-transparent hover:text-content-secondary'}
                    `}
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
            {selectionLoading ? (
              <div className="flex items-center gap-3 py-8">
                <div className="w-6 h-6 border-2 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
                <span className="text-content-secondary font-sans text-sm">Loading diagnostic status...</span>
              </div>
            ) : (
              <>
                {activeTab === 'tools' && (
                  <ToolStatusGrid toolRuns={selectedToolRuns} />
                )}

                {activeTab === 'follow-up' && (
                  <div>
                    {/* Non-dismissible disclaimer (Guardrail 5) */}
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
                      if (!selectedEngagement) return;
                      setConvergenceExporting(true);
                      await downloadConvergenceCsv(selectedEngagement.id);
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
              </>
            )}
          </div>
        ) : (
          /* Engagement list */
          <EngagementList
            engagements={engagements}
            clients={clients}
            materialityMap={materialityMap}
            toolRunCountMap={toolRunCountMap}
            selectedId={null}
            isLoading={engagementsLoading}
            onSelect={handleSelectEngagement}
            onFilterClient={handleFilterClient}
            onFilterStatus={handleFilterStatus}
          />
        )}
      </div>

      {/* Create Modal */}
      <CreateEngagementModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateEngagement}
        clients={clients}
        isLoading={engagementsLoading}
      />
    </div>
  );
}

/**
 * Engagements page wrapper with Suspense.
 */
export default function EngagementsPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center py-16">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
          <p className="text-content-secondary font-sans">Loading workspace...</p>
        </div>
      </div>
    }>
      <EngagementsPageContent />
    </Suspense>
  );
}
