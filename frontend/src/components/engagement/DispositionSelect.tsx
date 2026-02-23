'use client';

import type { FollowUpDisposition } from '@/types/engagement';
import { DISPOSITION_LABELS } from '@/types/engagement';
import { getSelectClasses } from '@/utils/themeUtils';

interface DispositionSelectProps {
  value: FollowUpDisposition;
  onChange: (disposition: FollowUpDisposition) => void;
  disabled?: boolean;
  id?: string;
}

const DISPOSITION_OPTIONS: FollowUpDisposition[] = [
  'not_reviewed',
  'investigated_no_issue',
  'investigated_adjustment_posted',
  'investigated_further_review',
  'immaterial',
];

export function DispositionSelect({ value, onChange, disabled = false, id }: DispositionSelectProps) {
  return (
    <select
      id={id}
      value={value}
      onChange={(e) => onChange(e.target.value as FollowUpDisposition)}
      disabled={disabled}
      className={`${getSelectClasses(disabled)} !py-1.5 !px-2.5 !text-xs !rounded-lg`}
    >
      {DISPOSITION_OPTIONS.map((disp) => (
        <option key={disp} value={disp}>
          {DISPOSITION_LABELS[disp]}
        </option>
      ))}
    </select>
  );
}
