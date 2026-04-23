/**
 * Triple-CSV parser for W-2 / W-3 Reconciliation — Sprint 689d.
 *
 * Parses three separate CSVs: payroll YTD, draft W-2s, and
 * Form 941 quarterlies. Each is optional except payroll.
 */

import type {
  Form941QuarterRequest,
  HsaCoverage,
  RetirementPlanType,
  W2DraftRequest,
  W2EmployeePayrollRequest,
} from '@/types/w2Reconciliation'

const MAX_EMPLOYEES = 10_000
const MAX_QUARTERS = 4

export class W2CsvParseError extends Error {}

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
  return trimmed.replace(/[,$\s]/g, '')
}

export function parsePayrollCsv(text: string): W2EmployeePayrollRequest[] {
  const rows = splitRows(text)
  if (rows.length === 0) throw new W2CsvParseError('Payroll CSV is empty.')

  const header = splitCsvLine(rows[0] ?? '')
  const get = (names: string[]) => findColumn(header, names)

  const idCol = get(['employee_id', 'id'])
  const nameCol = get(['employee_name', 'name'])
  const ageCol = get(['age'])
  const fedWagesCol = get(['federal_wages', 'fed_wages'])
  const fedWhCol = get(['federal_withholding', 'fed_withholding'])
  const ssWagesCol = get(['ss_wages', 'social_security_wages'])
  const ssTaxCol = get(['ss_tax_withheld', 'social_security_tax'])
  const medWagesCol = get(['medicare_wages'])
  const medTaxCol = get(['medicare_tax_withheld', 'medicare_tax'])
  const hsaContribCol = get(['hsa_contributions', 'hsa'])
  const hsaCovCol = get(['hsa_coverage'])
  const r401kCol = get(['retirement_401k', '401k'])
  const rSimpleCol = get(['retirement_simple_ira', 'simple_ira'])
  const rPlanCol = get(['retirement_plan_type', 'plan_type'])

  const missing: string[] = []
  if (idCol === -1) missing.push('employee_id')
  if (nameCol === -1) missing.push('employee_name')
  if (missing.length) {
    throw new W2CsvParseError(`Payroll CSV header is missing: ${missing.join(', ')}.`)
  }

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_EMPLOYEES) {
    throw new W2CsvParseError(`Payroll CSV exceeds ${MAX_EMPLOYEES}-row cap (got ${dataRows.length}).`)
  }

  const employees: W2EmployeePayrollRequest[] = []
  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const employee_id = (fields[idCol] || '').trim()
    const employee_name = (fields[nameCol] || '').trim()
    if (!employee_id || !employee_name) {
      throw new W2CsvParseError(`Payroll row ${i + 2}: employee_id and employee_name are required.`)
    }
    const age = ageCol !== -1 ? Number.parseInt(fields[ageCol] || '', 10) : Number.NaN
    const hsaCoverageRaw = hsaCovCol !== -1 ? (fields[hsaCovCol] || '').toLowerCase().trim() : ''
    const hsaCoverage: HsaCoverage = hsaCoverageRaw === 'self_only' || hsaCoverageRaw === 'family' ? hsaCoverageRaw : 'none'
    const planRaw = rPlanCol !== -1 ? (fields[rPlanCol] || '').toLowerCase().trim() : ''
    const retirement_plan_type: RetirementPlanType | null =
      planRaw === '401k' || planRaw === 'simple_ira' ? planRaw : null

    employees.push({
      employee_id,
      employee_name,
      age: Number.isFinite(age) ? age : null,
      federal_wages: fedWagesCol !== -1 ? normalizeAmount(fields[fedWagesCol] ?? '') : '0',
      federal_withholding: fedWhCol !== -1 ? normalizeAmount(fields[fedWhCol] ?? '') : '0',
      ss_wages: ssWagesCol !== -1 ? normalizeAmount(fields[ssWagesCol] ?? '') : '0',
      ss_tax_withheld: ssTaxCol !== -1 ? normalizeAmount(fields[ssTaxCol] ?? '') : '0',
      medicare_wages: medWagesCol !== -1 ? normalizeAmount(fields[medWagesCol] ?? '') : '0',
      medicare_tax_withheld: medTaxCol !== -1 ? normalizeAmount(fields[medTaxCol] ?? '') : '0',
      hsa_contributions: hsaContribCol !== -1 ? normalizeAmount(fields[hsaContribCol] ?? '') : '0',
      hsa_coverage: hsaCoverage,
      retirement_401k: r401kCol !== -1 ? normalizeAmount(fields[r401kCol] ?? '') : '0',
      retirement_simple_ira: rSimpleCol !== -1 ? normalizeAmount(fields[rSimpleCol] ?? '') : '0',
      retirement_plan_type,
    })
  }

  return employees
}

export function parseW2DraftsCsv(text: string): W2DraftRequest[] {
  const rows = splitRows(text)
  if (rows.length === 0) return []

  const header = splitCsvLine(rows[0] ?? '')
  const get = (names: string[]) => findColumn(header, names)

  const idCol = get(['employee_id', 'id'])
  const b1Col = get(['box_1_federal_wages', 'box_1', 'box1'])
  const b2Col = get(['box_2_federal_withholding', 'box_2', 'box2'])
  const b3Col = get(['box_3_ss_wages', 'box_3', 'box3'])
  const b4Col = get(['box_4_ss_tax_withheld', 'box_4', 'box4'])
  const b5Col = get(['box_5_medicare_wages', 'box_5', 'box5'])
  const b6Col = get(['box_6_medicare_tax_withheld', 'box_6', 'box6'])
  const wCol = get(['box_12_code_w_hsa', 'box_12_w', 'code_w'])
  const dCol = get(['box_12_code_d_401k', 'box_12_d', 'code_d'])
  const sCol = get(['box_12_code_s_simple', 'box_12_s', 'code_s'])

  if (idCol === -1) throw new W2CsvParseError('W-2 draft CSV header must include employee_id.')

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_EMPLOYEES) {
    throw new W2CsvParseError(`W-2 draft CSV exceeds ${MAX_EMPLOYEES}-row cap.`)
  }

  const drafts: W2DraftRequest[] = []
  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const employee_id = (fields[idCol] || '').trim()
    if (!employee_id) {
      throw new W2CsvParseError(`W-2 draft row ${i + 2}: employee_id is required.`)
    }
    drafts.push({
      employee_id,
      box_1_federal_wages: b1Col !== -1 ? normalizeAmount(fields[b1Col] ?? '') : '0',
      box_2_federal_withholding: b2Col !== -1 ? normalizeAmount(fields[b2Col] ?? '') : '0',
      box_3_ss_wages: b3Col !== -1 ? normalizeAmount(fields[b3Col] ?? '') : '0',
      box_4_ss_tax_withheld: b4Col !== -1 ? normalizeAmount(fields[b4Col] ?? '') : '0',
      box_5_medicare_wages: b5Col !== -1 ? normalizeAmount(fields[b5Col] ?? '') : '0',
      box_6_medicare_tax_withheld: b6Col !== -1 ? normalizeAmount(fields[b6Col] ?? '') : '0',
      box_12_code_w_hsa: wCol !== -1 ? normalizeAmount(fields[wCol] ?? '') : '0',
      box_12_code_d_401k: dCol !== -1 ? normalizeAmount(fields[dCol] ?? '') : '0',
      box_12_code_s_simple: sCol !== -1 ? normalizeAmount(fields[sCol] ?? '') : '0',
    })
  }

  return drafts
}

export function parseForm941Csv(text: string): Form941QuarterRequest[] {
  const rows = splitRows(text)
  if (rows.length === 0) return []

  const header = splitCsvLine(rows[0] ?? '')
  const get = (names: string[]) => findColumn(header, names)

  const qCol = get(['quarter', 'q'])
  const fedWagesCol = get(['total_federal_wages', 'federal_wages'])
  const fedWhCol = get(['total_federal_withholding', 'federal_withholding'])
  const ssWagesCol = get(['total_ss_wages', 'ss_wages'])
  const medWagesCol = get(['total_medicare_wages', 'medicare_wages'])

  if (qCol === -1) throw new W2CsvParseError('Form 941 CSV must include a `quarter` column.')

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_QUARTERS) {
    throw new W2CsvParseError(`Form 941 CSV has more than ${MAX_QUARTERS} rows.`)
  }

  const quarters: Form941QuarterRequest[] = []
  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const quarter = Number.parseInt(fields[qCol] || '', 10)
    if (!Number.isFinite(quarter) || quarter < 1 || quarter > 4) {
      throw new W2CsvParseError(`Form 941 row ${i + 2}: quarter must be 1, 2, 3, or 4.`)
    }
    quarters.push({
      quarter,
      total_federal_wages: fedWagesCol !== -1 ? normalizeAmount(fields[fedWagesCol] ?? '') : '0',
      total_federal_withholding: fedWhCol !== -1 ? normalizeAmount(fields[fedWhCol] ?? '') : '0',
      total_ss_wages: ssWagesCol !== -1 ? normalizeAmount(fields[ssWagesCol] ?? '') : '0',
      total_medicare_wages: medWagesCol !== -1 ? normalizeAmount(fields[medWagesCol] ?? '') : '0',
    })
  }

  return quarters
}

export async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}.`))
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.readAsText(file)
  })
}
