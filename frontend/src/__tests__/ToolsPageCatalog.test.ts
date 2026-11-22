/**
 * Sprint 893 (16A follow-up): the tools page's table agrees with the generated catalog and
 * the ledger. Its test counts are derived (testCountFor); this checks that no row types a
 * count in again, and that each row the catalog knows has the catalog's href and category.
 */
import fs from 'fs'
import path from 'path'
import { TOOL_CATALOG } from '@/content/tool-catalog.generated'

const SRC = fs.readFileSync(path.join(__dirname, '../app/tools/page.tsx'), 'utf8')
const ROWS = [...SRC.matchAll(/\{ key: '([a-z_0-9]+)', label: '[^']+', href: '([^']+)'.*?category: '([^']+)'(.*?)\}/g)]

describe('tools page table', () => {
  it('has rows', () => {
    expect(ROWS.length).toBeGreaterThanOrEqual(18)
  })

  it('types no test count by hand', () => {
    const literal = ROWS.filter(r => /testCount: \d/.test(r[4] ?? '')).map(r => r[1])
    expect(literal).toEqual([])
  })

  it('matches the catalog href and category for every tool the catalog lists', () => {
    const mismatches: string[] = []
    for (const [, key, href, category] of ROWS) {
      const tool = TOOL_CATALOG.find(t => t.slug === key)
      if (!tool) continue
      if (tool.href !== href) mismatches.push(`${key}: href ${href} vs ${tool.href}`)
      if (tool.category !== category) mismatches.push(`${key}: category ${category} vs ${tool.category}`)
    }
    expect(mismatches).toEqual([])
  })
})
