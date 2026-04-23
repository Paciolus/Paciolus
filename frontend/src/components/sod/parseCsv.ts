/**
 * Minimal CSV parser for the SoD dual-upload flow — Sprint 689b.
 *
 * Handles: header row, quoted fields, escaped quotes, CRLF/LF.
 * Does NOT handle: mid-field newlines inside quotes (a deliberate tradeoff —
 * IAM exports don't contain these; full RFC 4180 parsing is overkill here).
 */

import type { SODRolePermission, SODUserAssignment } from '@/types/sod'

const MAX_USER_ROWS = 10_000
const MAX_ROLE_ROWS = 2_000

export class CsvParseError extends Error {}

export interface UsersCsvResult {
  assignments: SODUserAssignment[]
  rowCount: number
}

export interface RolesCsvResult {
  permissions: SODRolePermission[]
  rowCount: number
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

function splitMultivalue(cell: string): string[] {
  if (!cell) return []
  return cell
    .split(/[|;]/)
    .map(v => v.trim())
    .filter(v => v.length > 0)
}

export function parseUsersCsv(text: string): UsersCsvResult {
  const rows = splitRows(text)
  if (rows.length === 0) {
    throw new CsvParseError('Users CSV is empty.')
  }

  const header = splitCsvLine(rows[0] ?? '')
  const userIdCol = findColumn(header, ['user_id', 'userid', 'user id', 'id'])
  const userNameCol = findColumn(header, ['user_name', 'username', 'user name', 'name'])
  const rolesCol = findColumn(header, ['role_codes', 'roles', 'role_code', 'role'])

  if (userIdCol === -1 || userNameCol === -1 || rolesCol === -1) {
    throw new CsvParseError(
      'Users CSV header must include columns: user_id, user_name, role_codes.'
    )
  }

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_USER_ROWS) {
    throw new CsvParseError(`Users CSV exceeds ${MAX_USER_ROWS}-row cap (got ${dataRows.length}).`)
  }

  const assignments: SODUserAssignment[] = []
  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const userId = fields[userIdCol] || ''
    const userName = fields[userNameCol] || ''
    const roles = splitMultivalue(fields[rolesCol] || '')
    if (!userId || !userName) {
      throw new CsvParseError(`Users CSV row ${i + 2}: user_id and user_name are required.`)
    }
    assignments.push({ user_id: userId, user_name: userName, role_codes: roles })
  }

  return { assignments, rowCount: assignments.length }
}

export function parseRolesCsv(text: string): RolesCsvResult {
  const rows = splitRows(text)
  if (rows.length === 0) {
    throw new CsvParseError('Roles CSV is empty.')
  }

  const header = splitCsvLine(rows[0] ?? '')
  const roleCol = findColumn(header, ['role_code', 'role', 'rolecode'])
  const permsCol = findColumn(header, ['permissions', 'perms', 'permission'])

  if (roleCol === -1 || permsCol === -1) {
    throw new CsvParseError(
      'Roles CSV header must include columns: role_code, permissions.'
    )
  }

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_ROLE_ROWS) {
    throw new CsvParseError(`Roles CSV exceeds ${MAX_ROLE_ROWS}-row cap (got ${dataRows.length}).`)
  }

  const permissions: SODRolePermission[] = []
  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const role = fields[roleCol] || ''
    const perms = splitMultivalue(fields[permsCol] || '')
    if (!role) {
      throw new CsvParseError(`Roles CSV row ${i + 2}: role_code is required.`)
    }
    permissions.push({ role_code: role, permissions: perms })
  }

  return { permissions, rowCount: permissions.length }
}

export async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}.`))
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.readAsText(file)
  })
}
