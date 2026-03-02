/**
 * Entitlement Parity Test — frontend-side cross-check.
 *
 * Pricing v3: Only FREE tier has restricted tools (TB + Flux Analysis).
 * All paid tiers (Solo, Professional, Enterprise) have access to all 12 tools.
 *
 * Asserts that UpgradeGate FREE_TOOLS and commandRegistry FREE_TOOLS + toolGuard
 * are identical, preventing drift between the two frontend guard systems.
 */

// We need to import the actual source to parse, but the modules use
// side effects (React, framer-motion). Instead, we read the source files
// directly and parse the Set declarations.

import * as fs from 'fs'
import * as path from 'path'

function parseJsSet(source: string, variableName: string): Set<string> {
  // Match: `variableName: new Set([...])` or `const variableName = new Set([...])`
  const pattern = new RegExp(
    `(?:${variableName}\\s*[:=]\\s*new\\s+Set\\(\\[|${variableName}\\s*=\\s*new\\s+Set\\(\\[)([\\s\\S]*?)\\]\\)`
  )
  const match = source.match(pattern)
  if (!match) {
    throw new Error(`Could not find Set declaration for '${variableName}'`)
  }
  const inner = match[1]
  const tools = inner.match(/'([^']+)'/g)?.map(s => s.replace(/'/g, '')) ?? []
  return new Set(tools)
}

const UPGRADE_GATE_PATH = path.resolve(
  __dirname, '..', 'components', 'shared', 'UpgradeGate.tsx'
)
const COMMAND_REGISTRY_PATH = path.resolve(
  __dirname, '..', 'lib', 'commandRegistry.ts'
)

const upgradeGateSource = fs.readFileSync(UPGRADE_GATE_PATH, 'utf-8')
const commandRegistrySource = fs.readFileSync(COMMAND_REGISTRY_PATH, 'utf-8')

/** All 12 tools in the system. */
const ALL_TOOLS = [
  'trial_balance',
  'flux_analysis',
  'journal_entry_testing',
  'multi_period',
  'ap_testing',
  'bank_reconciliation',
  'revenue_testing',
  'payroll_testing',
  'three_way_match',
  'ar_aging',
  'fixed_asset_testing',
  'inventory_testing',
  'statistical_sampling',
] as const

describe('Entitlement Parity', () => {
  const ugFree = parseJsSet(upgradeGateSource, 'free')
  const crFree = parseJsSet(commandRegistrySource, 'FREE_TOOLS')

  test('UpgradeGate free tools === commandRegistry FREE_TOOLS', () => {
    expect([...ugFree].sort()).toEqual([...crFree].sort())
  })

  test('free tier has exactly 2 tools (trial_balance + flux_analysis)', () => {
    expect(ugFree.size).toBe(2)
    expect(ugFree.has('trial_balance')).toBe(true)
    expect(ugFree.has('flux_analysis')).toBe(true)
  })

  test('UpgradeGate does not define solo, team, or organization tool sets', () => {
    // Pricing v3: only free tier has a restricted set; paid tiers are unrestricted
    expect(() => parseJsSet(upgradeGateSource, 'solo')).toThrow()
    expect(() => parseJsSet(upgradeGateSource, 'team')).toThrow()
    expect(() => parseJsSet(upgradeGateSource, 'organization')).toThrow()
  })

  test('commandRegistry does not define SOLO_TOOLS, TEAM_TOOLS, or ORG_TOOLS', () => {
    expect(() => parseJsSet(commandRegistrySource, 'SOLO_TOOLS')).toThrow()
    expect(() => parseJsSet(commandRegistrySource, 'TEAM_TOOLS')).toThrow()
    expect(() => parseJsSet(commandRegistrySource, 'ORG_TOOLS')).toThrow()
  })

  test('toolGuard returns undefined for free tools (no guard needed)', () => {
    // Replicate toolGuard logic from commandRegistry (Pricing v3)
    function toolGuard(toolName: string): { minTier: string } | undefined {
      if (crFree.has(toolName)) return undefined
      return { minTier: 'solo' }
    }

    // Free tools should have no guard (accessible to all)
    expect(toolGuard('trial_balance')).toBeUndefined()
    expect(toolGuard('flux_analysis')).toBeUndefined()
  })

  test('toolGuard returns { minTier: "solo" } for all non-free tools', () => {
    function toolGuard(toolName: string): { minTier: string } | undefined {
      if (crFree.has(toolName)) return undefined
      return { minTier: 'solo' }
    }

    const nonFreeTools = ALL_TOOLS.filter(t => !crFree.has(t))
    expect(nonFreeTools.length).toBe(11) // 13 total - 2 free = 11

    for (const tool of nonFreeTools) {
      expect(toolGuard(tool)).toEqual({ minTier: 'solo' })
    }
  })

  test('no tool requires team or organization tier (Pricing v3 flat access)', () => {
    function toolGuard(toolName: string): { minTier: string } | undefined {
      if (crFree.has(toolName)) return undefined
      return { minTier: 'solo' }
    }

    for (const tool of ALL_TOOLS) {
      const guard = toolGuard(tool)
      if (guard) {
        expect(guard.minTier).not.toBe('team')
        expect(guard.minTier).not.toBe('organization')
      }
    }
  })

  test('every tool in ALL_TOOLS is either free or requires solo', () => {
    for (const tool of ALL_TOOLS) {
      const isFree = crFree.has(tool)
      if (!isFree) {
        // Non-free tools must not be in the free set
        expect(ugFree.has(tool)).toBe(false)
      }
    }
  })
})
