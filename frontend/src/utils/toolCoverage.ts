/**
 * Sprint 891 (CEO brief 16A, review ST-07): how many of the marketed tools an engagement has run.
 *
 * The workspace printed `{toolRuns.length}/18 tools` — every run, repeats and failures included,
 * against a hard-coded 18. This counts distinct marketed tools with at least one completed run,
 * against the catalog's count.
 */
import { MARKETING_AUDIT_TOOL_SLUGS } from '@/content/tool-catalog.generated'

export function completedMarketedToolCount(runs: ReadonlyArray<{ tool_name: string; status: string }>): number {
  const marketed = new Set(MARKETING_AUDIT_TOOL_SLUGS)
  return new Set(runs.filter(r => r.status === 'completed' && marketed.has(r.tool_name)).map(r => r.tool_name)).size
}
