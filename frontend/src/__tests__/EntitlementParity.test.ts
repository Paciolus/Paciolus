/**
 * Entitlement Parity Test — frontend-side cross-check.
 *
 * Asserts that UpgradeGate TIER_TOOLS and commandRegistry tool sets
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

describe('Entitlement Parity', () => {
  const ugFree = parseJsSet(upgradeGateSource, 'free')
  const ugSolo = parseJsSet(upgradeGateSource, 'solo')
  const ugTeam = parseJsSet(upgradeGateSource, 'team')
  const ugProfessional = parseJsSet(upgradeGateSource, 'professional')

  const crFree = parseJsSet(commandRegistrySource, 'FREE_TOOLS')
  const crSolo = parseJsSet(commandRegistrySource, 'SOLO_TOOLS')
  const crTeam = parseJsSet(commandRegistrySource, 'TEAM_TOOLS')

  test('UpgradeGate solo === commandRegistry SOLO_TOOLS', () => {
    expect([...ugSolo].sort()).toEqual([...crSolo].sort())
  })

  test('UpgradeGate team === commandRegistry TEAM_TOOLS', () => {
    expect([...ugTeam].sort()).toEqual([...crTeam].sort())
  })

  test('UpgradeGate free === commandRegistry FREE_TOOLS', () => {
    expect([...ugFree].sort()).toEqual([...crFree].sort())
  })

  test('UpgradeGate professional === UpgradeGate solo (deprecated tier)', () => {
    expect([...ugProfessional].sort()).toEqual([...ugSolo].sort())
  })

  test('solo tools are a superset of free tools', () => {
    for (const tool of ugFree) {
      expect(ugSolo.has(tool)).toBe(true)
    }
  })

  test('team tools are a superset of solo tools', () => {
    for (const tool of ugSolo) {
      expect(ugTeam.has(tool)).toBe(true)
    }
  })

  test('solo has exactly 7 tools', () => {
    expect(ugSolo.size).toBe(7)
  })

  test('team has exactly 11 tools', () => {
    expect(ugTeam.size).toBe(11)
  })

  test('free has exactly 2 tools', () => {
    expect(ugFree.size).toBe(2)
  })

  test('toolGuard returns correct guard for each tool entry', () => {
    // Replicate toolGuard logic from commandRegistry (3-tier)
    function toolGuard(toolName: string): { minTier: string } | undefined {
      if (crFree.has(toolName)) return undefined
      if (crSolo.has(toolName) && !crFree.has(toolName)) return { minTier: 'solo' }
      if (crTeam.has(toolName) && !crSolo.has(toolName)) return { minTier: 'team' }
      return { minTier: 'organization' }
    }

    // Free tools should have no guard (accessible to all)
    expect(toolGuard('trial_balance')).toBeUndefined()
    expect(toolGuard('flux_analysis')).toBeUndefined()

    // Solo-only tools should require 'solo' tier
    expect(toolGuard('journal_entry_testing')).toEqual({ minTier: 'solo' })
    expect(toolGuard('multi_period')).toEqual({ minTier: 'solo' })
    expect(toolGuard('ap_testing')).toEqual({ minTier: 'solo' })

    // Team-only tools should require 'team' tier
    expect(toolGuard('bank_reconciliation')).toEqual({ minTier: 'team' })
    expect(toolGuard('revenue_testing')).toEqual({ minTier: 'team' })
    expect(toolGuard('payroll_testing')).toEqual({ minTier: 'team' })
    expect(toolGuard('three_way_match')).toEqual({ minTier: 'team' })

    // Organization-only tools should require 'organization' tier
    expect(toolGuard('ar_aging')).toEqual({ minTier: 'organization' })
    expect(toolGuard('fixed_asset_testing')).toEqual({ minTier: 'organization' })
    expect(toolGuard('inventory_testing')).toEqual({ minTier: 'organization' })
    expect(toolGuard('statistical_sampling')).toEqual({ minTier: 'organization' })
  })
})
