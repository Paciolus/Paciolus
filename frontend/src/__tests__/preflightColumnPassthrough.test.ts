/**
 * Sprint 309: Pre-Flight Column Passthrough Tests
 *
 * Tests the column mapping extraction logic used by useTrialBalanceAudit
 * to pass pre-flight detected columns directly to TB audit.
 */
import type { PreFlightColumnQuality } from '@/types/preflight'
import type { ColumnMapping } from '@/components/mapping'

// ─── Extraction logic (mirrors hook implementation) ──────────────────────────

function extractPreflightMapping(
  columns: PreFlightColumnQuality[] | undefined
): ColumnMapping | null {
  if (!columns) return null

  const account = columns.find(c => c.role === 'account' && c.status === 'found' && c.confidence >= 0.8)
  const debit = columns.find(c => c.role === 'debit' && c.status === 'found' && c.confidence >= 0.8)
  const credit = columns.find(c => c.role === 'credit' && c.status === 'found' && c.confidence >= 0.8)

  if (account?.detected_name && debit?.detected_name && credit?.detected_name) {
    return {
      account_column: account.detected_name,
      debit_column: debit.detected_name,
      credit_column: credit.detected_name,
    }
  }

  return null
}

// ─── Tests ────────────────────────────────────────────────────────────────────

describe('Pre-Flight Column Passthrough', () => {
  it('extracts mapping when all 3 columns found with high confidence', () => {
    const columns: PreFlightColumnQuality[] = [
      { role: 'account', detected_name: 'Account Name', confidence: 0.95, status: 'found' },
      { role: 'debit', detected_name: 'Debit', confidence: 0.9, status: 'found' },
      { role: 'credit', detected_name: 'Credit', confidence: 0.85, status: 'found' },
    ]

    const mapping = extractPreflightMapping(columns)
    expect(mapping).toEqual({
      account_column: 'Account Name',
      debit_column: 'Debit',
      credit_column: 'Credit',
    })
  })

  it('returns null when a column has low confidence (< 0.8)', () => {
    const columns: PreFlightColumnQuality[] = [
      { role: 'account', detected_name: 'Account Name', confidence: 0.95, status: 'found' },
      { role: 'debit', detected_name: 'Debit', confidence: 0.7, status: 'found' },
      { role: 'credit', detected_name: 'Credit', confidence: 0.85, status: 'found' },
    ]

    const mapping = extractPreflightMapping(columns)
    expect(mapping).toBeNull()
  })

  it('returns null when a column is missing', () => {
    const columns: PreFlightColumnQuality[] = [
      { role: 'account', detected_name: 'Account Name', confidence: 0.95, status: 'found' },
      { role: 'debit', detected_name: 'Debit', confidence: 0.9, status: 'found' },
      { role: 'credit', detected_name: null, confidence: 0.0, status: 'missing' },
    ]

    const mapping = extractPreflightMapping(columns)
    expect(mapping).toBeNull()
  })

  it('returns null when columns array is undefined', () => {
    const mapping = extractPreflightMapping(undefined)
    expect(mapping).toBeNull()
  })

  it('returns null when columns array is empty', () => {
    const mapping = extractPreflightMapping([])
    expect(mapping).toBeNull()
  })

  it('returns null when status is low_confidence even with high numeric confidence', () => {
    const columns: PreFlightColumnQuality[] = [
      { role: 'account', detected_name: 'Account Name', confidence: 0.95, status: 'found' },
      { role: 'debit', detected_name: 'Debit', confidence: 0.9, status: 'low_confidence' },
      { role: 'credit', detected_name: 'Credit', confidence: 0.85, status: 'found' },
    ]

    const mapping = extractPreflightMapping(columns)
    expect(mapping).toBeNull()
  })

  it('handles exact 0.8 confidence threshold (inclusive)', () => {
    const columns: PreFlightColumnQuality[] = [
      { role: 'account', detected_name: 'Account', confidence: 0.8, status: 'found' },
      { role: 'debit', detected_name: 'Dr', confidence: 0.8, status: 'found' },
      { role: 'credit', detected_name: 'Cr', confidence: 0.8, status: 'found' },
    ]

    const mapping = extractPreflightMapping(columns)
    expect(mapping).toEqual({
      account_column: 'Account',
      debit_column: 'Dr',
      credit_column: 'Cr',
    })
  })

  it('ignores extra columns not relevant to the 3 required roles', () => {
    const columns: PreFlightColumnQuality[] = [
      { role: 'account', detected_name: 'Account Name', confidence: 0.95, status: 'found' },
      { role: 'debit', detected_name: 'Debit', confidence: 0.9, status: 'found' },
      { role: 'credit', detected_name: 'Credit', confidence: 0.85, status: 'found' },
      { role: 'description', detected_name: 'Description', confidence: 0.6, status: 'low_confidence' },
    ]

    const mapping = extractPreflightMapping(columns)
    expect(mapping).not.toBeNull()
    expect(mapping?.account_column).toBe('Account Name')
  })
})
