/**
 * Sprint 866: the "what each tool takes, does and gives" table on /sources.
 */
import { TOOL_IO } from '@/content/tool-io'
import { TOOL_LEDGER } from '@/content/tool-ledger'

describe('TOOL_IO', () => {
  it('has exactly one row per tool in the catalog', () => {
    expect(TOOL_IO.map(r => r.id).sort()).toEqual(TOOL_LEDGER.map(t => t.id).sort())
  })

  it('states the same test count as the catalog wherever it names one', () => {
    for (const tool of TOOL_LEDGER) {
      const row = TOOL_IO.find(r => r.id === tool.id)!
      const stated = /Runs (\d+) tests/.exec(row.does)
      if (tool.testCount) {
        expect(stated?.[1]).toBe(String(tool.testCount))
      } else {
        expect(stated).toBeNull()
      }
    }
  })
})
