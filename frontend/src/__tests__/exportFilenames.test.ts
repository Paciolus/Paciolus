/**
 * Sprint 649 — buildExportFilename contract tests.
 */

import { buildExportFilename } from '@/utils/exportFilenames'

const FIXED_DATE = new Date(2026, 3, 16) // 2026-04-16

describe('buildExportFilename', () => {
  it('builds tool + date when no client provided', () => {
    expect(buildExportFilename({ tool: 'TB_Diagnostic', date: FIXED_DATE })).toBe(
      'Paciolus_TB_Diagnostic_20260416.pdf',
    )
  })

  it('includes the client slug when provided', () => {
    expect(
      buildExportFilename({ tool: 'AP_Testing', client: 'Acme Corp', date: FIXED_DATE }),
    ).toBe('Paciolus_AP_Testing_Acme_Corp_20260416.pdf')
  })

  it('slugifies unsafe characters in tool and client', () => {
    expect(
      buildExportFilename({
        tool: 'AP Testing / Batch 1',
        client: 'Smith & Co., LLC',
        date: FIXED_DATE,
      }),
    ).toBe('Paciolus_AP_Testing_Batch_1_Smith_Co_LLC_20260416.pdf')
  })

  it('honors the extension argument (case-normalised)', () => {
    expect(buildExportFilename({ tool: 'Revenue', extension: 'CSV', date: FIXED_DATE })).toBe(
      'Paciolus_Revenue_20260416.csv',
    )
  })

  it('falls back to pdf when extension is blank', () => {
    expect(buildExportFilename({ tool: 'Revenue', extension: '', date: FIXED_DATE })).toBe(
      'Paciolus_Revenue_20260416.pdf',
    )
  })

  it('drops an empty client string rather than emitting a double underscore', () => {
    expect(buildExportFilename({ tool: 'Payroll', client: '   ', date: FIXED_DATE })).toBe(
      'Paciolus_Payroll_20260416.pdf',
    )
  })

  it('caps long client names at 40 chars', () => {
    const client = 'A'.repeat(100)
    const out = buildExportFilename({ tool: 'Tool', client, date: FIXED_DATE })
    // Between the leading "Paciolus_Tool_" and the trailing "_20260416.pdf",
    // exactly 40 A's — the 41st would push us over the cap.
    expect(out).toBe(`Paciolus_Tool_${'A'.repeat(40)}_20260416.pdf`)
  })

  it('uses "Unknown" tool slug as a defensive fallback', () => {
    expect(buildExportFilename({ tool: '', date: FIXED_DATE })).toBe(
      'Paciolus_Unknown_20260416.pdf',
    )
  })
})
