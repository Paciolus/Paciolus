/**
 * Unit tests for trialBalanceUpload — shared TB upload orchestration.
 *
 * Covers FormData construction and the TrialBalanceUploadOutcome mapping
 * (success, auth, email-not-verified, forbidden, transport, audit_error).
 */

jest.mock('@/utils/uploadTransport', () => ({
  uploadFetch: jest.fn(),
}))

import {
  buildTrialBalanceFormData,
  classifyTrialBalanceFailure,
  uploadTrialBalance,
} from '@/utils/trialBalanceUpload'
import { uploadFetch } from '@/utils/uploadTransport'

const mockUploadFetch = uploadFetch as jest.Mock

const makeFile = (name = 'tb.csv'): File =>
  new File(['account,debit,credit\n'], name, { type: 'text/csv' })

describe('buildTrialBalanceFormData', () => {
  it('includes file + threshold', () => {
    const fd = buildTrialBalanceFormData({ file: makeFile(), materialityThreshold: 500 })
    expect(fd.get('file')).toBeInstanceOf(File)
    expect(fd.get('materiality_threshold')).toBe('500')
  })

  it('omits overrides/mapping/sheets/engagement/preflight when unset', () => {
    const fd = buildTrialBalanceFormData({ file: makeFile(), materialityThreshold: 100 })
    expect(fd.get('account_type_overrides')).toBeNull()
    expect(fd.get('column_mapping')).toBeNull()
    expect(fd.get('selected_sheets')).toBeNull()
    expect(fd.get('engagement_id')).toBeNull()
    expect(fd.get('preflight_token')).toBeNull()
  })

  it('serializes all optional fields when provided', () => {
    const fd = buildTrialBalanceFormData({
      file: makeFile(),
      materialityThreshold: 750,
      accountTypeOverrides: { '1000': 'Asset' },
      columnMapping: { account: 'Account', debit: 'Debit', credit: 'Credit' } as unknown as import('@/components/mapping').ColumnMapping,
      selectedSheets: ['TB'],
      engagementId: 42,
      preflightToken: 'pf-xyz',
    })
    expect(JSON.parse(fd.get('account_type_overrides') as string)).toEqual({ '1000': 'Asset' })
    expect(JSON.parse(fd.get('column_mapping') as string)).toEqual({
      account: 'Account',
      debit: 'Debit',
      credit: 'Credit',
    })
    expect(JSON.parse(fd.get('selected_sheets') as string)).toEqual(['TB'])
    expect(fd.get('engagement_id')).toBe('42')
    expect(fd.get('preflight_token')).toBe('pf-xyz')
  })

  it('omits empty override map', () => {
    const fd = buildTrialBalanceFormData({
      file: makeFile(),
      materialityThreshold: 100,
      accountTypeOverrides: {},
    })
    expect(fd.get('account_type_overrides')).toBeNull()
  })

  it('omits empty selected_sheets array', () => {
    const fd = buildTrialBalanceFormData({
      file: makeFile(),
      materialityThreshold: 100,
      selectedSheets: [],
    })
    expect(fd.get('selected_sheets')).toBeNull()
  })
})

describe('classifyTrialBalanceFailure', () => {
  it('maps 401 → auth', () => {
    expect(
      classifyTrialBalanceFailure({ ok: false, status: 401, error: 'auth' }),
    ).toEqual({ kind: 'auth', message: 'Please sign in to run diagnostics.' })
  })

  it('maps EMAIL_NOT_VERIFIED errorCode → email_not_verified (takes precedence over 403)', () => {
    const outcome = classifyTrialBalanceFailure({
      ok: false,
      status: 403,
      error: 'email_not_verified',
      errorCode: 'EMAIL_NOT_VERIFIED',
    })
    expect(outcome.kind).toBe('email_not_verified')
  })

  it('maps generic 403 → forbidden', () => {
    expect(
      classifyTrialBalanceFailure({ ok: false, status: 403, error: 'access_denied' }),
    ).toEqual({ kind: 'forbidden', message: 'Access denied.' })
  })

  it('maps 422/429/5xx/0 → transport with server message', () => {
    const r = classifyTrialBalanceFailure({
      ok: false,
      status: 422,
      error: 'Column mapping required',
    })
    expect(r).toEqual({ kind: 'transport', status: 422, message: 'Column mapping required' })
  })

  it('falls back when backend provides no message', () => {
    const r = classifyTrialBalanceFailure({ ok: false, status: 500, error: '' })
    expect(r.kind).toBe('transport')
    if (r.kind === 'transport') expect(r.message).toContain('500')
  })
})

describe('uploadTrialBalance', () => {
  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('returns success with the audit result on 200', async () => {
    mockUploadFetch.mockResolvedValue({
      ok: true,
      status: 200,
      data: { status: 'success', row_count: 10 },
    })

    const outcome = await uploadTrialBalance({ file: makeFile(), materialityThreshold: 500 })

    expect(outcome.kind).toBe('success')
    if (outcome.kind === 'success') {
      expect(outcome.result.status).toBe('success')
    }
    expect(mockUploadFetch).toHaveBeenCalledWith('/audit/trial-balance', expect.any(FormData), null)
  })

  it('classifies uploadFetch non-ok outcomes', async () => {
    mockUploadFetch.mockResolvedValue({ ok: false, status: 401, error: 'auth' })
    const outcome = await uploadTrialBalance({ file: makeFile(), materialityThreshold: 1 })
    expect(outcome.kind).toBe('auth')
  })

  it('maps backend {status:error} bodies to audit_error', async () => {
    mockUploadFetch.mockResolvedValue({
      ok: true,
      status: 200,
      data: { status: 'error', message: 'File empty' },
    })

    const outcome = await uploadTrialBalance({ file: makeFile(), materialityThreshold: 1 })

    expect(outcome).toEqual({ kind: 'audit_error', message: 'File empty' })
  })

  it('maps missing body to audit_error with a default message', async () => {
    mockUploadFetch.mockResolvedValue({ ok: true, status: 200, data: undefined })
    const outcome = await uploadTrialBalance({ file: makeFile(), materialityThreshold: 1 })
    expect(outcome.kind).toBe('audit_error')
    if (outcome.kind === 'audit_error') expect(outcome.message).toBeTruthy()
  })

  it('forwards the token argument to uploadFetch', async () => {
    mockUploadFetch.mockResolvedValue({
      ok: true,
      status: 200,
      data: { status: 'success' },
    })
    await uploadTrialBalance({ file: makeFile(), materialityThreshold: 1 }, 'tok')
    expect(mockUploadFetch).toHaveBeenCalledWith(
      '/audit/trial-balance',
      expect.any(FormData),
      'tok',
    )
  })
})
