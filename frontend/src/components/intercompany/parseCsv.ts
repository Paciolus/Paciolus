/**
 * Long-format CSV parser for the Intercompany Elimination flow — Sprint 689c.
 *
 * Expected columns (case-insensitive, header required):
 *   entity_id, entity_name, account, debit, credit, counterparty_entity
 *
 * Client pivots rows → grouped entities → JSON payload matching
 * `IntercompanyEliminationRequest`. Rows sharing an entity_id are
 * merged; the first entity_name wins (a warning surfaces if a later
 * row disagrees).
 */

import type {
  IntercompanyEliminationRequest,
  IntercompanyEntityAccountRequest,
  IntercompanyEntityTBRequest,
} from '@/types/intercompany'

const MAX_ROWS = 250_000
const MAX_ENTITIES = 50
const MAX_ACCOUNTS_PER_ENTITY = 5000

export class IntercompanyCsvParseError extends Error {}

export interface IntercompanyCsvParseResult {
  entities: IntercompanyEntityTBRequest[]
  totalRows: number
  intercompanyRows: number
  warnings: string[]
}

function splitCsvLine(line: string): string[] {
  const fields: string[] = []
  let current = ''
  let inQuotes = false
  for (let i = 0; i < line.length; i++) {
    const ch = line[i]
    if (inQuotes) {
      if (ch === '"') {
        if (line[i + 1] === '"') {
          current += '"'
          i++
        } else {
          inQuotes = false
        }
      } else {
        current += ch
      }
    } else if (ch === ',') {
      fields.push(current)
      current = ''
    } else if (ch === '"' && current === '') {
      inQuotes = true
    } else {
      current += ch
    }
  }
  fields.push(current)
  return fields.map(f => f.trim())
}

function splitRows(text: string): string[] {
  return text
    .replace(/\r\n/g, '\n')
    .split('\n')
    .map(r => r.trim())
    .filter(r => r.length > 0)
}

function findColumn(header: string[], candidates: string[]): number {
  const lower = header.map(h => h.toLowerCase())
  for (const candidate of candidates) {
    const idx = lower.indexOf(candidate)
    if (idx !== -1) return idx
  }
  return -1
}

function normalizeAmount(raw: string): string {
  const trimmed = (raw ?? '').trim()
  if (!trimmed || trimmed === '-') return '0'
  // Strip thousand separators and currency markers; keep sign + decimal.
  return trimmed.replace(/[,$\s]/g, '')
}

function normalizeCounterparty(raw: string): string | null {
  const trimmed = (raw ?? '').trim()
  if (!trimmed) return null
  return trimmed
}

export function parseIntercompanyCsv(text: string): IntercompanyCsvParseResult {
  const rows = splitRows(text)
  if (rows.length === 0) {
    throw new IntercompanyCsvParseError('CSV is empty.')
  }

  const header = splitCsvLine(rows[0] ?? '')
  const entityIdCol = findColumn(header, ['entity_id', 'entity id', 'entityid', 'entity'])
  const entityNameCol = findColumn(header, ['entity_name', 'entity name', 'entityname', 'name'])
  const accountCol = findColumn(header, ['account', 'account_name', 'gl_account'])
  const debitCol = findColumn(header, ['debit', 'dr'])
  const creditCol = findColumn(header, ['credit', 'cr'])
  const counterpartyCol = findColumn(header, [
    'counterparty_entity',
    'counterparty',
    'counterparty entity',
    'counterparty_id',
  ])

  const required: Array<[string, number]> = [
    ['entity_id', entityIdCol],
    ['entity_name', entityNameCol],
    ['account', accountCol],
    ['debit', debitCol],
    ['credit', creditCol],
  ]
  const missing = required.filter(([, idx]) => idx === -1).map(([name]) => name)
  if (missing.length > 0) {
    throw new IntercompanyCsvParseError(
      `CSV header is missing required column(s): ${missing.join(', ')}. ` +
        'Expected: entity_id, entity_name, account, debit, credit, counterparty_entity.',
    )
  }

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_ROWS) {
    throw new IntercompanyCsvParseError(`CSV exceeds ${MAX_ROWS.toLocaleString()}-row cap (got ${dataRows.length}).`)
  }

  const byEntity = new Map<string, { name: string; accounts: IntercompanyEntityAccountRequest[] }>()
  const warnings: string[] = []
  let intercompanyRows = 0

  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const entityId = (fields[entityIdCol] || '').trim()
    const entityName = (fields[entityNameCol] || '').trim()
    const account = (fields[accountCol] || '').trim()
    const debit = normalizeAmount(fields[debitCol] ?? '')
    const credit = normalizeAmount(fields[creditCol] ?? '')
    const counterparty =
      counterpartyCol !== -1 ? normalizeCounterparty(fields[counterpartyCol] ?? '') : null

    if (!entityId) {
      throw new IntercompanyCsvParseError(`Row ${i + 2}: entity_id is required.`)
    }
    if (!entityName) {
      throw new IntercompanyCsvParseError(`Row ${i + 2}: entity_name is required.`)
    }
    if (!account) {
      throw new IntercompanyCsvParseError(`Row ${i + 2}: account is required.`)
    }

    let entry = byEntity.get(entityId)
    if (!entry) {
      entry = { name: entityName, accounts: [] }
      byEntity.set(entityId, entry)
    } else if (entry.name !== entityName) {
      if (!warnings.some(w => w.startsWith(`Entity ${entityId} appears under multiple names`))) {
        warnings.push(
          `Entity ${entityId} appears under multiple names ("${entry.name}" and "${entityName}"); the first name was used.`,
        )
      }
    }
    entry.accounts.push({ account, debit, credit, counterparty_entity: counterparty })
    if (counterparty) intercompanyRows++
  }

  if (byEntity.size < 2) {
    throw new IntercompanyCsvParseError(
      `Consolidation requires at least 2 entities; the CSV contains ${byEntity.size}.`,
    )
  }
  if (byEntity.size > MAX_ENTITIES) {
    throw new IntercompanyCsvParseError(
      `CSV exceeds the ${MAX_ENTITIES}-entity cap (got ${byEntity.size}).`,
    )
  }

  const entities: IntercompanyEntityTBRequest[] = []
  for (const [entity_id, { name, accounts }] of byEntity.entries()) {
    if (accounts.length > MAX_ACCOUNTS_PER_ENTITY) {
      throw new IntercompanyCsvParseError(
        `Entity "${entity_id}" exceeds the ${MAX_ACCOUNTS_PER_ENTITY}-account cap (got ${accounts.length}).`,
      )
    }
    entities.push({ entity_id, entity_name: name, accounts })
  }

  if (intercompanyRows === 0) {
    warnings.push(
      'No rows have a counterparty_entity value. The engine will report "no_reciprocal" mismatches for every intercompany account you intend to eliminate.',
    )
  }

  return {
    entities,
    totalRows: dataRows.length,
    intercompanyRows,
    warnings,
  }
}

export function buildRequest(
  entities: IntercompanyEntityTBRequest[],
  tolerance: string,
): IntercompanyEliminationRequest {
  return { entities, tolerance }
}

export async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}.`))
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.readAsText(file)
  })
}
