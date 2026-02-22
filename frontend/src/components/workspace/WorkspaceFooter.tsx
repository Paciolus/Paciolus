/**
 * WorkspaceFooter — Sprint 385: Phase LII Foundation
 *
 * Shared footer extracted from portfolio and engagements pages.
 * Oat & Obsidian semantic tokens only.
 */

export function WorkspaceFooter() {
  return (
    <footer className="py-6 px-6 border-t border-theme">
      <div className="max-w-[1440px] mx-auto flex flex-col md:flex-row justify-between items-center gap-4">
        <div className="text-content-tertiary text-sm font-sans">
          2025 Paciolus. Built for Financial Professionals.
        </div>
        <div className="text-content-tertiary text-sm font-sans">
          Zero-Storage Architecture. Your data stays yours.
        </div>
      </div>
    </footer>
  );
}
