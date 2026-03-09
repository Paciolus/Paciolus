'use client';

import { useState } from 'react';

export interface EngagementMetadata {
  entityName: string;
  fiscalYearEnd: string;
  engagementPeriod: string;
  preparedBy: string;
  reviewedBy: string;
  reportStatus: 'Draft' | 'Final';
}

export const DEFAULT_ENGAGEMENT_METADATA: EngagementMetadata = {
  entityName: '',
  fiscalYearEnd: '',
  engagementPeriod: '',
  preparedBy: '',
  reviewedBy: '',
  reportStatus: 'Draft',
};

interface EngagementDetailsPanelProps {
  value: EngagementMetadata;
  onChange: (metadata: EngagementMetadata) => void;
}

/**
 * EngagementDetailsPanel — Optional collapsible section for engagement metadata.
 *
 * Sprint 525: Provides UI entry for cover page metadata fields (entity, FYE,
 * prepared by, reviewed by, report status). Values populate PDF report cover pages.
 */
export function EngagementDetailsPanel({ value, onChange }: EngagementDetailsPanelProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  const update = (field: keyof EngagementMetadata, val: string) => {
    onChange({ ...value, [field]: val });
  };

  return (
    <div className="card mb-6">
      <button
        type="button"
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between"
      >
        <span className="text-content-primary font-sans font-medium">
          Engagement Details
          <span className="text-content-tertiary font-normal ml-1">(Optional)</span>
        </span>
        <svg
          className={`w-4 h-4 text-content-tertiary transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {isExpanded && (
        <div className="mt-4 space-y-3">
          <p className="text-content-tertiary text-xs font-sans">
            These fields populate the PDF report cover page. Leave blank to omit.
          </p>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {/* Entity / Client Name */}
            <div>
              <label htmlFor="eng-entity-name" className="block text-xs font-sans font-medium text-content-secondary mb-1">
                Entity / Client Name
              </label>
              <input
                id="eng-entity-name"
                type="text"
                value={value.entityName}
                onChange={(e) => update('entityName', e.target.value)}
                placeholder="e.g., Acme Corporation"
                className="w-full px-3 py-1.5 bg-surface-card border border-theme rounded-lg text-sm text-content-primary font-sans placeholder:text-content-tertiary focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              />
            </div>

            {/* Fiscal Year End */}
            <div>
              <label htmlFor="eng-fiscal-year" className="block text-xs font-sans font-medium text-content-secondary mb-1">
                Fiscal Year End
              </label>
              <input
                id="eng-fiscal-year"
                type="text"
                value={value.fiscalYearEnd}
                onChange={(e) => update('fiscalYearEnd', e.target.value)}
                placeholder="e.g., December 31, 2025"
                className="w-full px-3 py-1.5 bg-surface-card border border-theme rounded-lg text-sm text-content-primary font-sans placeholder:text-content-tertiary focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              />
            </div>

            {/* Engagement Period */}
            <div>
              <label htmlFor="eng-period" className="block text-xs font-sans font-medium text-content-secondary mb-1">
                Engagement Period
              </label>
              <input
                id="eng-period"
                type="text"
                value={value.engagementPeriod}
                onChange={(e) => update('engagementPeriod', e.target.value)}
                placeholder="e.g., Year ended December 31, 2025"
                className="w-full px-3 py-1.5 bg-surface-card border border-theme rounded-lg text-sm text-content-primary font-sans placeholder:text-content-tertiary focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              />
            </div>

            {/* Report Status */}
            <div>
              <label htmlFor="eng-report-status" className="block text-xs font-sans font-medium text-content-secondary mb-1">
                Report Status
              </label>
              <select
                id="eng-report-status"
                value={value.reportStatus}
                onChange={(e) => update('reportStatus', e.target.value)}
                className="w-full px-3 py-1.5 bg-surface-card border border-theme rounded-lg text-sm text-content-primary font-sans focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              >
                <option value="Draft">Draft</option>
                <option value="Final">Final</option>
              </select>
            </div>

            {/* Engagement Practitioner (formerly Prepared By) */}
            <div>
              <label htmlFor="eng-practitioner" className="block text-xs font-sans font-medium text-content-secondary mb-1">
                Engagement Practitioner
              </label>
              <input
                id="eng-practitioner"
                type="text"
                value={value.preparedBy}
                onChange={(e) => update('preparedBy', e.target.value)}
                placeholder="e.g., Jane Smith, CPA"
                className="w-full px-3 py-1.5 bg-surface-card border border-theme rounded-lg text-sm text-content-primary font-sans placeholder:text-content-tertiary focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              />
            </div>

            {/* Engagement Reviewer (formerly Reviewed By) */}
            <div>
              <label htmlFor="eng-reviewer" className="block text-xs font-sans font-medium text-content-secondary mb-1">
                Engagement Reviewer
              </label>
              <input
                id="eng-reviewer"
                type="text"
                value={value.reviewedBy}
                onChange={(e) => update('reviewedBy', e.target.value)}
                placeholder="e.g., John Doe, CPA"
                className="w-full px-3 py-1.5 bg-surface-card border border-theme rounded-lg text-sm text-content-primary font-sans placeholder:text-content-tertiary focus:outline-hidden focus:ring-2 focus:ring-sage-500 focus:border-transparent"
              />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
