'use client';

import { useState } from 'react';
import { motion } from 'framer-motion';
import type { Client } from '@/types/client';
import type { Engagement, EngagementStatus, MaterialityCascade } from '@/types/engagement';
import { CONTAINER_VARIANTS } from '@/utils/themeUtils';
import { EngagementCard } from './EngagementCard';

interface EngagementListProps {
  engagements: Engagement[];
  clients: Client[];
  materialityMap: Record<number, MaterialityCascade>;
  toolRunCountMap: Record<number, number>;
  selectedId: number | null;
  isLoading: boolean;
  onSelect: (engagement: Engagement) => void;
  onFilterClient: (clientId?: number) => void;
  onFilterStatus: (status?: string) => void;
}

type StatusTab = 'all' | 'active' | 'archived';

export function EngagementList({
  engagements,
  clients,
  materialityMap,
  toolRunCountMap,
  selectedId,
  isLoading,
  onSelect,
  onFilterClient,
  onFilterStatus,
}: EngagementListProps) {
  const [activeTab, setActiveTab] = useState<StatusTab>('all');
  const [selectedClientId, setSelectedClientId] = useState<string>('');

  const handleTabChange = (tab: StatusTab) => {
    setActiveTab(tab);
    onFilterStatus(tab === 'all' ? undefined : tab);
  };

  const handleClientChange = (value: string) => {
    setSelectedClientId(value);
    onFilterClient(value ? parseInt(value, 10) : undefined);
  };

  const clientNameMap = new Map(clients.map(c => [c.id, c.name]));

  const tabs: { key: StatusTab; label: string }[] = [
    { key: 'all', label: 'All' },
    { key: 'active', label: 'Active' },
    { key: 'archived', label: 'Archived' },
  ];

  return (
    <div>
      {/* Filters row */}
      <div className="flex flex-col sm:flex-row sm:items-center gap-4 mb-6">
        {/* Status tabs */}
        <div className="flex gap-1 bg-surface-card-secondary rounded-lg p-1">
          {tabs.map(tab => (
            <button
              key={tab.key}
              onClick={() => handleTabChange(tab.key)}
              className={`
                px-4 py-1.5 rounded-md text-sm font-sans transition-all duration-200
                ${activeTab === tab.key
                  ? 'bg-surface-card text-content-primary shadow-sm'
                  : 'text-content-tertiary hover:text-content-secondary'
                }
              `}
            >
              {tab.label}
            </button>
          ))}
        </div>

        {/* Client filter dropdown */}
        <select
          value={selectedClientId}
          onChange={(e) => handleClientChange(e.target.value)}
          className="px-3 py-2 bg-surface-input border border-theme rounded-lg text-sm font-sans text-content-secondary outline-none focus:border-sage-500/50 transition-colors appearance-none cursor-pointer"
        >
          <option value="">All Clients</option>
          {clients.map(client => (
            <option key={client.id} value={client.id.toString()}>
              {client.name}
            </option>
          ))}
        </select>
      </div>

      {/* Loading skeleton */}
      {isLoading && engagements.length === 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {[1, 2, 3, 4].map(i => (
            <div key={i} className="bg-surface-card rounded-xl border border-theme p-5 animate-pulse">
              <div className="flex items-start justify-between gap-3 mb-3">
                <div className="h-5 w-2/3 bg-oatmeal-200 rounded" />
                <div className="h-5 w-16 bg-oatmeal-200 rounded-full" />
              </div>
              <div className="h-4 w-3/4 bg-oatmeal-200 rounded mb-3" />
              <div className="h-4 w-1/2 bg-oatmeal-200 rounded" />
            </div>
          ))}
        </div>
      )}

      {/* Empty state */}
      {!isLoading && engagements.length === 0 && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-center py-16"
        >
          <div className="w-24 h-24 mx-auto mb-6 rounded-2xl bg-surface-card-secondary border border-theme flex items-center justify-center">
            <svg className="w-12 h-12 text-content-tertiary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
          </div>
          <h2 className="text-2xl font-serif font-semibold text-content-primary mb-2">
            No Workspaces Yet
          </h2>
          <p className="text-content-secondary font-sans mb-4 max-w-md mx-auto">
            Create your first diagnostic workspace to organize tool runs and track materiality thresholds.
          </p>
        </motion.div>
      )}

      {/* Engagement grid */}
      {engagements.length > 0 && (
        <motion.div
          variants={CONTAINER_VARIANTS.fast}
          initial="hidden"
          animate="visible"
          className="grid grid-cols-1 md:grid-cols-2 gap-6"
        >
          {engagements.map((engagement, index) => (
            <EngagementCard
              key={engagement.id}
              engagement={engagement}
              index={index}
              clientName={clientNameMap.get(engagement.client_id)}
              materiality={materialityMap[engagement.id]}
              toolRunCount={toolRunCountMap[engagement.id] || 0}
              isSelected={selectedId === engagement.id}
              onClick={onSelect}
            />
          ))}
        </motion.div>
      )}
    </div>
  );
}
