'use client'

/**
 * HolidayCalendarPanel — Sprint 831
 *
 * The auditor's holiday calendar for this client, sent with the next JE run.
 * The default list is the US federal holidays (5 U.S.C. 6103). The auditor
 * marks holidays the client works (not flagged) and adds client-specific
 * closure days (flagged like a holiday). Columbus Day and Veterans Day are
 * flagged LOW by default because most businesses are open on them.
 */

import { useState } from 'react'
import { COMMONLY_WORKED_HOLIDAYS, US_FEDERAL_HOLIDAYS, type HolidayCalendar } from '@/types/jeTesting'

const ISO_DATE = /^\d{4}-\d{2}-\d{2}$/
const MAX_CLOSURE_DATES = 60

/** Parse the closure-day text into ISO dates; returns the bad tokens too. */
export function parseClosureDates(text: string): { dates: string[]; invalid: string[] } {
  const tokens = text.split(/[\s,]+/).map(t => t.trim()).filter(Boolean)
  const dates: string[] = []
  const invalid: string[] = []
  for (const t of tokens) {
    const valid = ISO_DATE.test(t) && !Number.isNaN(new Date(`${t}T00:00:00Z`).getTime())
    if (valid) {
      if (!dates.includes(t)) dates.push(t)
    } else {
      invalid.push(t)
    }
  }
  return { dates, invalid }
}

interface HolidayCalendarPanelProps {
  calendar: HolidayCalendar
  onChange: (calendar: HolidayCalendar) => void
}

export function HolidayCalendarPanel({ calendar, onChange }: HolidayCalendarPanelProps) {
  const [closureText, setClosureText] = useState(calendar.closed_dates.join(', '))
  const { dates, invalid } = parseClosureDates(closureText)
  const tooMany = dates.length > MAX_CLOSURE_DATES

  const toggleWorked = (name: string) => {
    const exclude = calendar.exclude.includes(name)
      ? calendar.exclude.filter(n => n !== name)
      : [...calendar.exclude, name]
    onChange({ ...calendar, exclude })
  }

  const updateClosures = (text: string) => {
    setClosureText(text)
    const parsed = parseClosureDates(text)
    onChange({ ...calendar, closed_dates: parsed.dates.slice(0, MAX_CLOSURE_DATES) })
  }

  const changes = calendar.exclude.length + calendar.closed_dates.length

  return (
    <details className="theme-card p-4 mt-4">
      <summary className="cursor-pointer font-sans text-sm text-content-primary">
        Client holiday calendar
        {changes > 0 && (
          <span className="ml-2 text-content-tertiary">({changes} change{changes === 1 ? '' : 's'} from the federal list)</span>
        )}
      </summary>
      <div className="mt-4 space-y-4">
        <p className="font-sans text-xs text-content-tertiary">
          The holiday test uses the US federal holidays set by 5 U.S.C. 6103. Tick any day this client works so its
          postings are not flagged, and add days the client was closed. Columbus Day and Veterans Day are flagged at
          LOW severity because most businesses are open on them. Which days a client was closed is your call; Paciolus
          only applies the calendar you set here.
        </p>
        <fieldset>
          <legend className="font-sans text-xs text-content-secondary uppercase tracking-wider mb-2">Client works on</legend>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {US_FEDERAL_HOLIDAYS.map(name => (
              <label key={name} className="flex items-center gap-2 font-sans text-sm text-content-primary">
                <input
                  type="checkbox"
                  checked={calendar.exclude.includes(name)}
                  onChange={() => toggleWorked(name)}
                  className="accent-sage-600"
                />
                {name}
                {COMMONLY_WORKED_HOLIDAYS.includes(name) && (
                  <span className="text-xs text-content-tertiary">(flagged LOW)</span>
                )}
              </label>
            ))}
          </div>
        </fieldset>
        <div>
          <label htmlFor="je-closure-dates" className="font-sans text-xs text-content-secondary uppercase tracking-wider">
            Extra closure days
          </label>
          <textarea
            id="je-closure-dates"
            value={closureText}
            onChange={e => updateClosures(e.target.value)}
            placeholder="2025-12-24, 2025-11-28"
            rows={2}
            className="mt-1 w-full rounded-lg border border-theme bg-surface-input px-3 py-2 font-mono text-sm text-content-primary"
          />
          {invalid.length > 0 && (
            <p className="mt-1 font-sans text-xs text-clay-600" role="alert">
              Not a date (use YYYY-MM-DD): {invalid.join(', ')}
            </p>
          )}
          {tooMany && (
            <p className="mt-1 font-sans text-xs text-clay-600" role="alert">
              Only the first {MAX_CLOSURE_DATES} dates are sent.
            </p>
          )}
        </div>
      </div>
    </details>
  )
}
