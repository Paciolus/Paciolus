'use client';

import { useEffect, useCallback } from 'react';

/**
 * useKeyboardShortcuts — Sprint 388: Phase LII
 *
 * Global keyboard shortcut listener for the workspace shell.
 * Cross-platform: checks event.metaKey (Mac) || event.ctrlKey (Win/Linux).
 * Only preventDefault for registered shortcuts.
 */

export interface ShortcutConfig {
  key: string;
  meta?: boolean;
  shift?: boolean;
  action: () => void;
  description: string;
  scope?: 'global' | 'portfolio' | 'engagements';
}

export function useKeyboardShortcuts(shortcuts: ShortcutConfig[]): void {
  const handleKeyDown = useCallback(
    (event: KeyboardEvent) => {
      // Don't intercept when typing in inputs
      const target = event.target as HTMLElement;
      if (
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.isContentEditable
      ) {
        return;
      }

      for (const shortcut of shortcuts) {
        const metaMatch = shortcut.meta
          ? (event.metaKey || event.ctrlKey)
          : !(event.metaKey || event.ctrlKey);
        const shiftMatch = shortcut.shift ? event.shiftKey : !event.shiftKey;
        const keyMatch = event.key.toLowerCase() === shortcut.key.toLowerCase();

        if (metaMatch && shiftMatch && keyMatch) {
          event.preventDefault();
          event.stopPropagation();
          shortcut.action();
          return;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
}
