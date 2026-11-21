/**
 * Sprint 891 (CEO brief 16A): the dashboard and the workspace count come from the tool registry.
 */
import { DASHBOARD_TOOLS } from '@/content/dashboard-tools'
import { MARKETING_AUDIT_TOOL_COUNT, MARKETING_AUDIT_TOOL_SLUGS } from '@/content/tool-catalog.generated'
import { completedMarketedToolCount } from '@/utils/toolCoverage'

it('the dashboard shows every marketed tool, including the six promoted ones', () => {
  const keys = new Set(DASHBOARD_TOOLS.map(t => t.key))
  for (const slug of MARKETING_AUDIT_TOOL_SLUGS) expect(keys.has(slug)).toBe(true)
  for (const slug of ['sod_checker', 'intercompany_elimination', 'w2_reconciliation', 'form_1099', 'book_to_tax', 'cash_flow_projector']) {
    expect(keys.has(slug)).toBe(true)
  }
  expect(MARKETING_AUDIT_TOOL_COUNT).toBe(18)
})

it('the workspace counts distinct completed marketed tools, not runs', () => {
  const runs = [
    { tool_name: 'ap_testing', status: 'completed' },
    { tool_name: 'ap_testing', status: 'completed' },
    { tool_name: 'ap_testing', status: 'completed' },
    { tool_name: 'journal_entry_testing', status: 'failed' },
    { tool_name: 'flux_analysis', status: 'completed' },
    { tool_name: 'book_to_tax', status: 'completed' },
  ]
  expect(completedMarketedToolCount(runs)).toBe(2)
  expect(completedMarketedToolCount([])).toBe(0)
})
