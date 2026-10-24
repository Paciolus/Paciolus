/**
 * useJETesting Hook (Sprint 66, refactored Sprint 82, factory Sprint 161)
 *
 * Journal Entry Testing upload hook. Sprint 831: sends the auditor's holiday
 * calendar for the client with each run when one is set.
 * Zero-Storage: file processed on backend, results ephemeral.
 */

import { useMemo } from 'react'
import type { HolidayCalendar, JETestingResult } from '@/types/jeTesting'
import type { UploadStatus } from '@/types/shared'
import { useAuditUpload } from './useAuditUpload'

export interface UseJETestingReturn {
  status: UploadStatus
  result: JETestingResult | null
  error: string
  runTests: (file: File) => Promise<void>
  reset: () => void
}

/** True when the calendar changes nothing, so no field is sent. */
function isDefaultCalendar(calendar?: HolidayCalendar): boolean {
  return !calendar || (calendar.exclude.length === 0 && calendar.closed_dates.length === 0)
}

export function useJETesting(calendar?: HolidayCalendar): UseJETestingReturn {
  const calendarJson = isDefaultCalendar(calendar) ? null : JSON.stringify(calendar)
  const options = useMemo(() => ({
    endpoint: '/audit/journal-entries',
    toolName: 'JE tests',
    buildFormData: (...files: File[]) => {
      const fd = new FormData()
      if (files[0]) fd.append('file', files[0])
      if (calendarJson) fd.append('holiday_calendar', calendarJson)
      return fd
    },
    parseResult: (data: unknown) => data as JETestingResult,
  }), [calendarJson])

  const { run, ...rest } = useAuditUpload<JETestingResult>(options)
  return { ...rest, runTests: run as (file: File) => Promise<void> }
}
