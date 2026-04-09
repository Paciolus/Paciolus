'use client';

/**
 * Engagements Redirect — Sprint 580
 *
 * Workspaces merged into Portfolio. This page redirects:
 * - /engagements?engagement=X → /portfolio (workspace detail accessed from portfolio)
 * - /engagements → /portfolio
 */

import { useEffect } from 'react';
import { useRouter } from 'next/navigation';

export default function EngagementsRedirect() {
  const router = useRouter();

  useEffect(() => {
    router.replace('/portfolio');
  }, [router]);

  return (
    <div className="flex items-center justify-center py-16">
      <div className="flex flex-col items-center gap-4">
        <div className="w-12 h-12 border-4 border-sage-500/30 border-t-sage-500 rounded-full animate-spin" />
        <p className="text-content-secondary font-sans">Redirecting to Portfolio...</p>
      </div>
    </div>
  );
}
