/**
 * Dual-CSV parser for Form 1099 Preparation — Sprint 689e.
 *
 * Expected files:
 *   vendors.csv:  vendor_id, vendor_name, tin, entity_type, address_line_1, city, state, postal_code
 *   payments.csv: vendor_id, amount, payment_category, payment_method, payment_date, invoice_number
 */

import type {
  PaymentCategory1099,
  PaymentMethod1099,
  PaymentRequest,
  VendorEntity,
  VendorRequest,
} from '@/types/form1099'

const MAX_VENDORS = 5000
const MAX_PAYMENTS = 50_000

export class Form1099CsvParseError extends Error {}

const VALID_ENTITIES = new Set<VendorEntity>([
  'individual',
  'partnership',
  'llc',
  'corporation',
  's_corporation',
  'government',
  'tax_exempt',
  'unknown',
])

const VALID_METHODS = new Set<PaymentMethod1099>([
  'check',
  'ach',
  'wire',
  'cash',
  'credit_card',
  'paypal',
  'unknown',
])

const VALID_CATEGORIES = new Set<PaymentCategory1099>([
  'nonemployee_comp',
  'rents',
  'royalties',
  'medical',
  'legal',
  'interest',
  'other',
])

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

function nullable(raw: string | undefined): string | null {
  const trimmed = (raw ?? '').trim()
  return trimmed.length ? trimmed : null
}

export function parseVendorsCsv(text: string): VendorRequest[] {
  const rows = splitRows(text)
  if (rows.length === 0) throw new Form1099CsvParseError('Vendors CSV is empty.')

  const header = splitCsvLine(rows[0] ?? '')
  const idCol = findColumn(header, ['vendor_id', 'id'])
  const nameCol = findColumn(header, ['vendor_name', 'name'])
  const tinCol = findColumn(header, ['tin', 'ein', 'ssn'])
  const entityCol = findColumn(header, ['entity_type', 'type', 'vendor_type'])
  const addrCol = findColumn(header, ['address_line_1', 'address', 'street'])
  const cityCol = findColumn(header, ['city'])
  const stateCol = findColumn(header, ['state'])
  const zipCol = findColumn(header, ['postal_code', 'zip', 'zip_code'])

  if (idCol === -1 || nameCol === -1) {
    throw new Form1099CsvParseError('Vendors CSV header must include vendor_id and vendor_name.')
  }

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_VENDORS) {
    throw new Form1099CsvParseError(`Vendors CSV exceeds ${MAX_VENDORS}-row cap.`)
  }

  const vendors: VendorRequest[] = []
  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const vendor_id = (fields[idCol] || '').trim()
    const vendor_name = (fields[nameCol] || '').trim()
    if (!vendor_id || !vendor_name) {
      throw new Form1099CsvParseError(`Vendors row ${i + 2}: vendor_id and vendor_name are required.`)
    }
    const entityRaw = (entityCol !== -1 ? fields[entityCol] : 'unknown') || 'unknown'
    const entity_type: VendorEntity = VALID_ENTITIES.has(entityRaw.toLowerCase() as VendorEntity)
      ? (entityRaw.toLowerCase() as VendorEntity)
      : 'unknown'
    vendors.push({
      vendor_id,
      vendor_name,
      tin: tinCol !== -1 ? nullable(fields[tinCol]) : null,
      entity_type,
      address_line_1: addrCol !== -1 ? nullable(fields[addrCol]) : null,
      city: cityCol !== -1 ? nullable(fields[cityCol]) : null,
      state: stateCol !== -1 ? nullable(fields[stateCol]) : null,
      postal_code: zipCol !== -1 ? nullable(fields[zipCol]) : null,
    })
  }

  return vendors
}

export function parsePaymentsCsv(text: string): PaymentRequest[] {
  const rows = splitRows(text)
  if (rows.length === 0) throw new Form1099CsvParseError('Payments CSV is empty.')

  const header = splitCsvLine(rows[0] ?? '')
  const idCol = findColumn(header, ['vendor_id', 'vendor', 'id'])
  const amountCol = findColumn(header, ['amount'])
  const catCol = findColumn(header, ['payment_category', 'category'])
  const methodCol = findColumn(header, ['payment_method', 'method'])
  const dateCol = findColumn(header, ['payment_date', 'date'])
  const invoiceCol = findColumn(header, ['invoice_number', 'invoice'])

  if (idCol === -1 || amountCol === -1) {
    throw new Form1099CsvParseError('Payments CSV header must include vendor_id and amount.')
  }

  const dataRows = rows.slice(1)
  if (dataRows.length > MAX_PAYMENTS) {
    throw new Form1099CsvParseError(`Payments CSV exceeds ${MAX_PAYMENTS}-row cap.`)
  }

  const payments: PaymentRequest[] = []
  for (let i = 0; i < dataRows.length; i++) {
    const fields = splitCsvLine(dataRows[i] ?? '')
    const vendor_id = (fields[idCol] || '').trim()
    const amount = normalizeAmount(fields[amountCol] ?? '')
    if (!vendor_id) {
      throw new Form1099CsvParseError(`Payments row ${i + 2}: vendor_id is required.`)
    }
    const catRaw = (catCol !== -1 ? fields[catCol] : 'nonemployee_comp') || 'nonemployee_comp'
    const methodRaw = (methodCol !== -1 ? fields[methodCol] : 'check') || 'check'
    const payment_category: PaymentCategory1099 = VALID_CATEGORIES.has(catRaw.toLowerCase() as PaymentCategory1099)
      ? (catRaw.toLowerCase() as PaymentCategory1099)
      : 'other'
    const payment_method: PaymentMethod1099 = VALID_METHODS.has(methodRaw.toLowerCase() as PaymentMethod1099)
      ? (methodRaw.toLowerCase() as PaymentMethod1099)
      : 'unknown'
    payments.push({
      vendor_id,
      amount,
      payment_category,
      payment_method,
      payment_date: dateCol !== -1 ? nullable(fields[dateCol]) : null,
      invoice_number: invoiceCol !== -1 ? nullable(fields[invoiceCol]) : null,
    })
  }

  return payments
}

export async function readFileAsText(file: File): Promise<string> {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error(`Failed to read ${file.name}.`))
    reader.onload = () => resolve(String(reader.result ?? ''))
    reader.readAsText(file)
  })
}
