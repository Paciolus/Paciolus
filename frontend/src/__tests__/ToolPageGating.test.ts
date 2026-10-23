/**
 * Tool Page Gating — Sprint 814.
 *
 * Every catalog tool the Free tier cannot use must render inside an
 * `<UpgradeGate toolName="<ledger id>">`. AP Testing, Journal Entry Testing
 * and Multi-Period shipped without one: a Free user got the full upload UI,
 * uploaded a file, and only then hit the backend's 403.
 *
 * The page list comes from TOOL_LEDGER and the Free set from UpgradeGate's
 * own source, so a new tool is covered the moment it joins the catalog.
 */

import * as fs from 'fs'
import * as path from 'path'
import { TOOL_LEDGER } from '@/content/tool-ledger'

const SRC = path.resolve(__dirname, '..')

function freeTools(): Set<string> {
  const source = fs.readFileSync(path.join(SRC, 'components', 'shared', 'UpgradeGate.tsx'), 'utf-8')
  const match = source.match(/free:\s*new\s+Set\(\[([\s\S]*?)\]\)/)
  if (!match) throw new Error('Could not find the free-tier Set in UpgradeGate.tsx')
  return new Set(match[1]!.match(/'([^']+)'/g)?.map(s => s.replace(/'/g, '')) ?? [])
}

function gatedToolNames(href: string): string[] {
  const source = fs.readFileSync(path.join(SRC, 'app', ...href.split('/').filter(Boolean), 'page.tsx'), 'utf-8')
  return [...source.matchAll(/<UpgradeGate\s+toolName="([a-z0-9_]+)"/g)].map(m => m[1]!)
}

describe('Tool page gating', () => {
  const free = freeTools()
  const paid = TOOL_LEDGER.filter(entry => !free.has(entry.id))

  it('resolves the Free set and a non-trivial paid population', () => {
    expect(free.has('trial_balance')).toBe(true)
    expect(paid.length).toBeGreaterThanOrEqual(15)
  })

  it.each(paid.map(entry => [entry.href, entry.id]))(
    '%s is wrapped in <UpgradeGate toolName="%s">',
    (href, id) => {
      expect(gatedToolNames(href)).toContain(id)
    },
  )
})
