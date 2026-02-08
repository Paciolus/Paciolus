'use client';

import { useState, useEffect, useCallback, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { motion } from 'framer-motion';
import Link from 'next/link';
import { useAuth } from '@/context/AuthContext';
import { useEngagement } from '@/hooks/useEngagement';
import { useClients } from '@/hooks/useClients';
import { useFollowUpItems } from '@/hooks/useFollowUpItems';
import { ProfileDropdown } from '@/components/auth';
import { EngagementList, CreateEngagementModal, ToolStatusGrid, FollowUpItemsTable, WorkpaperIndex } from '@/components/engagement';
import { formatCurrency } from '@/utils/formatting';
import { apiGet } from '@/utils';
import type { Engagement, ToolRun, MaterialityCascade, WorkpaperIndex as WorkpaperIndexType } from '@/types/engagement';

/**
 * Diagnostic Workspace Page — Sprint 98
 * Phase X: The Engagement Layer
 *
 * Guardrails:
 * - Non-dismissible disclaimer banner (Guardrail 5)
 * - "Diagnostic Workspace" terminology (Guardrail 4) — no audit language
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
  const { user, token, isAuthenticated, isLoading: authLoading, logout } = useAuth();
  const {
    engagements,
    isLoading: engagementsLoading,
    error,
    fetchEngagements,
    createEngagement,
    archiveEngagement,
    getToolRuns,
    getMateriality,
  } = useEngagement();
  const { clients } = useClients();
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

  // Materiality cache for list view
  const [materialityMap, setMaterialityMap] = useState<Record<number, MaterialityCascade>>({});
  const [toolRunCountMap, setToolRunCountMap] = useState<Record<number, number>>({});

  // Modal
  const [showCreateModal, setShowCreateModal] = useState(false);

  // Active detail tab
  const [activeTab, setActiveTab] = useState<'tools' | 'follow-up' | 'workpaper'>('tools');

  // Auth redirect
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/login?redirect=/engagements');
    }
  }, [authLoading, isAuthenticated, router]);

  // Load materiality + tool run counts for engagement list
  useEffect(() => {
    if (engagements.length === 0) return;

    const loadSummaries = async () => {
      const matMap: Record<number, MaterialityCascade> = {};
      const runMap: Record<number, number> = {};

      await Promise.all(
        engagements.map(async (eng) => {
          const [mat, runs] = await Promise.all([
            getMateriality(eng.id),
            getToolRuns(eng.id),
          ]);
          if (mat) matMap[eng.id] = mat;
          runMap[eng.id] = runs.length;
        })
      );

      setMaterialityMap(matMap);
      setToolRunCountMap(runMap);
    };

    loadSummaries();
  }, [engagements.length]); // eslint-disable-line react-hooks/exhaustive-deps

  // Read ?engagement=X from URL on mount
  useEffect(() => {
    if (!isAuthenticated || engagements.length === 0) return;

    const engagementId = searchParams.get('engagement');
    if (engagementId && !selectedEngagement) {
      const id = parseInt(engagementId, 10);
      const found = engagements.find(e => e.id === id);
      if (found) {
        handleSelectEngagement(found);
      }
    }
  }, [isAuthenticated, engagements.length]); // eslint-disable-line react-hooks/exhaustive-deps

  const handleSelectEngagement = useCallback(async (engagement: Engagement) => {
    setSelectionLoading(true);
    setSelectedEngagement(engagement);
    setActiveTab('tools');

    const [runs, mat] = await Promise.all([
      getToolRuns(engagement.id),
      getMateriality(engagement.id),
    ]);

    setSelectedToolRuns(runs);
    setSelectedMateriality(mat);
    setSelectionLoading(false);

    // Load follow-up items and workpaper index in background
    fetchFollowUpItems(engagement.id);
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
  }, [getToolRuns, getMateriality, fetchFollowUpItems, token, searchParams, router]);

  const handleDeselectEngagement = useCallback(() => {
    setSelectedEngagement(null);
    setSelectedToolRuns([]);
    setSelectedMateriality(null);
    setWorkpaperIndex(null);

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

  // Loading state
  if (authLoading || (!isAuthenticated && !authLoading)) {
    return (
      <div className="min-h-screen bg-gradient-obsidian flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
          <p className="text-oatmeal-400 font-sans">Loading workspace...</p>
        </div>
      </div>
    );
  }

  const clientNameMap = new Map(clients.map(c => [c.id, c.name]));

  return (
    <main className="min-h-screen bg-gradient-obsidian">
      {/* Navigation */}
      <nav className="fixed top-0 w-full bg-obsidian-900/80 backdrop-blur-md border-b border-obsidian-600/50 z-50">
        <div className="max-w-6xl mx-auto px-6 py-3 flex justify-between items-center">
          <Link href="/" className="flex items-center gap-3">
            <img
              src="/PaciolusLogo_DarkBG.png"
              alt="Paciolus"
              className="h-10 w-auto max-h-10 object-contain"
              style={{ imageRendering: 'crisp-edges' }}
            />
            <span className="text-xl font-bold font-serif text-oatmeal-200 tracking-tight">
              Paciolus
            </span>
          </Link>

          <div className="flex items-center gap-4">
            <Link
              href="/"
              className="text-sm text-oatmeal-400 hover:text-oatmeal-200 font-sans transition-colors hidden sm:block"
            >
              Home
            </Link>
            <span className="text-oatmeal-600 hidden sm:block">|</span>
            <Link
              href="/portfolio"
              className="text-sm text-oatmeal-400 hover:text-oatmeal-200 font-sans transition-colors hidden sm:block"
            >
              Client Portfolio
            </Link>
            <span className="text-oatmeal-600 hidden sm:block">|</span>
            <span className="text-sm text-sage-400 font-sans hidden sm:block border-b border-sage-400/50">
              Diagnostic Workspace
            </span>
            {user && <ProfileDropdown user={user} onLogout={logout} />}
          </div>
        </div>
      </nav>

      {/* Non-dismissible disclaimer banner (Guardrail 5) */}
      <div className="fixed top-[65px] w-full bg-oatmeal-500/10 border-b border-oatmeal-500/20 z-40">
        <div className="max-w-6xl mx-auto px-6 py-2">
          <p className="text-xs font-sans text-oatmeal-400 text-center leading-relaxed">
            {DISCLAIMER_TEXT}
          </p>
        </div>
      </div>

      {/* Main Content */}
      <div className="pt-32 pb-16 px-6">
        <div className="max-w-6xl mx-auto">
          {/* Page Header */}
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
            <div>
              <h1 className="text-3xl md:text-4xl font-serif font-bold text-oatmeal-100">
                Diagnostic Workspace
              </h1>
              <p className="text-oatmeal-400 font-sans mt-1">
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
              className="inline-flex items-center gap-2 px-5 py-3 bg-sage-500 hover:bg-sage-400 text-oatmeal-50 font-sans font-bold rounded-xl transition-colors shadow-lg shadow-sage-500/20"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
              </svg>
              New Workspace
            </motion.button>
          </div>

          {/* Error */}
          {error && (
            <div className="mb-6 p-4 bg-clay-500/10 border border-clay-500/30 rounded-xl">
              <p className="text-clay-400 font-sans text-sm">{error}</p>
            </div>
          )}

          {/* Two-panel layout when engagement selected */}
          {selectedEngagement ? (
            <div className="space-y-8">
              {/* Back button */}
              <button
                onClick={handleDeselectEngagement}
                className="inline-flex items-center gap-2 text-sm font-sans text-oatmeal-400 hover:text-oatmeal-200 transition-colors"
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
                className="bg-obsidian-800/50 rounded-xl border border-sage-500/20 p-6"
              >
                <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4 mb-6">
                  <div>
                    <h2 className="text-2xl font-serif font-semibold text-oatmeal-100">
                      {clientNameMap.get(selectedEngagement.client_id) || `Client #${selectedEngagement.client_id}`}
                    </h2>
                    <div className="flex items-center gap-3 mt-2">
                      <span className="text-sm font-mono text-oatmeal-400">
                        {new Date(selectedEngagement.period_start).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                        {' \u2013 '}
                        {new Date(selectedEngagement.period_end).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                      </span>
                      <span className={`
                        inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-sans
                        ${selectedEngagement.status === 'active'
                          ? 'bg-sage-500/15 text-sage-400 border border-sage-500/30'
                          : 'bg-oatmeal-500/15 text-oatmeal-400 border border-oatmeal-500/30'
                        }
                      `}>
                        {selectedEngagement.status === 'active' ? 'Active' : 'Archived'}
                      </span>
                    </div>
                  </div>

                  {selectedEngagement.status === 'active' && (
                    <button
                      onClick={handleArchiveEngagement}
                      className="inline-flex items-center gap-2 px-4 py-2 text-sm font-sans text-oatmeal-400 hover:text-clay-400 border border-obsidian-600/50 hover:border-clay-500/30 rounded-lg transition-colors"
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
                  <div className="grid grid-cols-3 gap-4 pt-4 border-t border-obsidian-600/30">
                    <div>
                      <p className="text-xs font-sans text-oatmeal-500 mb-1">Overall Materiality</p>
                      <p className="text-lg font-mono font-semibold text-oatmeal-200">
                        {formatCurrency(selectedMateriality.overall_materiality)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-sans text-oatmeal-500 mb-1">Performance Materiality</p>
                      <p className="text-lg font-mono font-semibold text-oatmeal-200">
                        {formatCurrency(selectedMateriality.performance_materiality)}
                      </p>
                    </div>
                    <div>
                      <p className="text-xs font-sans text-oatmeal-500 mb-1">Trivial Threshold</p>
                      <p className="text-lg font-mono font-semibold text-oatmeal-200">
                        {formatCurrency(selectedMateriality.trivial_threshold)}
                      </p>
                    </div>
                  </div>
                )}
              </motion.div>

              {/* Tab navigation */}
              <div className="flex gap-1 border-b border-obsidian-600/50">
                {(['tools', 'follow-up', 'workpaper'] as const).map((tab) => {
                  const labels = { tools: 'Diagnostic Status', 'follow-up': 'Follow-Up Items', workpaper: 'Workpaper Index' };
                  const isActive = activeTab === tab;
                  return (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className={`
                        px-4 py-2.5 text-sm font-sans transition-colors border-b-2 -mb-[1px]
                        ${isActive
                          ? 'text-sage-400 border-sage-500'
                          : 'text-oatmeal-500 border-transparent hover:text-oatmeal-300'}
                      `}
                    >
                      {labels[tab]}
                      {tab === 'follow-up' && followUpItems.length > 0 && (
                        <span className="ml-1.5 inline-flex items-center justify-center min-w-[18px] h-[18px] px-1 rounded-full text-[10px] font-mono bg-oatmeal-500/15 text-oatmeal-400">
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
                  <span className="text-oatmeal-400 font-sans text-sm">Loading diagnostic status...</span>
                </div>
              ) : (
                <>
                  {activeTab === 'tools' && (
                    <ToolStatusGrid toolRuns={selectedToolRuns} />
                  )}

                  {activeTab === 'follow-up' && (
                    <div>
                      {/* Non-dismissible disclaimer (Guardrail 5) */}
                      <div className="mb-4 p-3 bg-oatmeal-500/10 border border-oatmeal-500/20 rounded-xl">
                        <p className="text-xs font-sans text-oatmeal-400 leading-relaxed">
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
                      />
                    </div>
                  )}

                  {activeTab === 'workpaper' && workpaperIndex && (
                    <WorkpaperIndex index={workpaperIndex} />
                  )}
                  {activeTab === 'workpaper' && !workpaperIndex && (
                    <div className="text-center py-12 bg-obsidian-800/30 rounded-xl border border-obsidian-600/30">
                      <p className="text-oatmeal-500 font-sans text-sm">Loading workpaper index...</p>
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
      </div>

      {/* Create Modal */}
      <CreateEngagementModal
        isOpen={showCreateModal}
        onClose={() => setShowCreateModal(false)}
        onSubmit={handleCreateEngagement}
        clients={clients}
        isLoading={engagementsLoading}
      />

      {/* Footer */}
      <footer className="py-8 px-6 border-t border-obsidian-600/50">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
          <div className="text-oatmeal-500 text-sm font-sans">
            2025 Paciolus. Built for Financial Professionals.
          </div>
          <div className="text-oatmeal-500 text-sm font-sans">
            Zero-Storage Architecture. Your data stays yours.
          </div>
        </div>
      </footer>
    </main>
  );
}

/**
 * Engagements page wrapper.
 * useSearchParams() in a client component doesn't require <Suspense>
 * at the page level for Next.js 14+ when the component itself is 'use client'.
 * But we wrap for safety per Next.js best practices.
 */
export default function EngagementsPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-obsidian flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
          <p className="text-oatmeal-400 font-sans">Loading workspace...</p>
        </div>
      </div>
    }>
      <EngagementsPageContent />
    </Suspense>
  );
}
