/**
 * Icon Registry — Sprint 384
 *
 * Merged registry combining legacy single-path icons with bespoke multi-element icons.
 */

import { LEGACY_PATHS } from './legacyPaths'
import type { BrandIconName, IconDefinition } from './types'

/** Bespoke icon definitions — extracted from inline SVGs across the codebase */
const BESPOKE_ICONS: Partial<Record<BrandIconName, IconDefinition>> = {
  'chevron-down': 'M19 9l-7 7-7-7',

  'checkmark': 'M5 13l4 4L19 7',

  'x-mark': 'M6 18L18 6M6 6l12 12',

  'file-plus': [
    {
      tag: 'path',
      attrs: {
        d: 'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',
      },
    },
    {
      tag: 'path',
      attrs: { d: 'M9 13h6m-3-3v6' },
    },
  ],

  'document-blank':
    'M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z',

  'spreadsheet':
    'M3 10h18M3 14h18m-9-4v8m-7 0h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v8a2 2 0 002 2z',

  'download-arrow':
    'M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4',
}

export const ICON_REGISTRY: Record<string, IconDefinition> = {
  ...LEGACY_PATHS,
  ...BESPOKE_ICONS,
} as Record<string, IconDefinition>

/** Check if an icon name exists in the registry */
export function hasIcon(name: string): name is BrandIconName {
  return name in ICON_REGISTRY
}
