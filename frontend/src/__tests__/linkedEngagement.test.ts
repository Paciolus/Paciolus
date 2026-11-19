/**
 * Sprint 886 (review OUT-18): memo exports name the linked engagement so the
 * server can resolve the client's reporting framework.
 */
import { act, renderHook } from '@testing-library/react'
import { useTestingExport } from '@/hooks/useTestingExport'
import { withLinkedEngagement } from '@/utils/linkedEngagement'
import { apiDownload } from '@/utils'

const mockEngagement = { current: null as null | { engagementId: number } }

jest.mock('@/contexts/AuthSessionContext', () => ({ useAuthSession: () => ({ token: 't' }) }))
jest.mock('@/contexts/EngagementContext', () => ({ useOptionalEngagementContext: () => mockEngagement.current }))
jest.mock('@/contexts/ToastContext', () => ({ useToast: () => ({ success: jest.fn(), error: jest.fn() }) }))
jest.mock('@/hooks/useSonification', () => ({ useSonification: () => ({ playTone: jest.fn() }) }))
jest.mock('@/utils', () => ({
  apiDownload: jest.fn().mockResolvedValue({ ok: true, blob: new Blob(), filename: 'm.pdf' }),
  downloadBlob: jest.fn(),
}))

describe('withLinkedEngagement', () => {
  it('adds engagement_id only when an engagement is linked', () => {
    expect(withLinkedEngagement({ a: 1 }, 7)).toEqual({ a: 1, engagement_id: 7 })
    expect(withLinkedEngagement({ a: 1 }, null)).toEqual({ a: 1 })
  })
})

describe('useTestingExport memo body', () => {
  beforeEach(() => (apiDownload as jest.Mock).mockClear())

  it('carries the linked engagement', async () => {
    mockEngagement.current = { engagementId: 42 }
    const { result } = renderHook(() => useTestingExport('/export/ap-testing-memo', '/export/csv/ap-testing'))
    await act(async () => { await result.current.handleExportMemo({ composite_score: {} }) })
    expect((apiDownload as jest.Mock).mock.calls[0][2].body).toEqual({ composite_score: {}, engagement_id: 42 })
  })

  it('carries none when no engagement is linked', async () => {
    mockEngagement.current = null
    const { result } = renderHook(() => useTestingExport('/export/ap-testing-memo', '/export/csv/ap-testing'))
    await act(async () => { await result.current.handleExportMemo({ composite_score: {} }) })
    expect((apiDownload as jest.Mock).mock.calls[0][2].body).toEqual({ composite_score: {} })
  })
})
