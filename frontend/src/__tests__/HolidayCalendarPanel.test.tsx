/**
 * Sprint 831: the auditor's holiday calendar for a JE run.
 */
import { HolidayCalendarPanel, parseClosureDates } from '@/components/jeTesting/HolidayCalendarPanel'
import { US_FEDERAL_HOLIDAYS } from '@/types/jeTesting'
import { fireEvent, render, screen } from '@/test-utils'

describe('parseClosureDates', () => {
  it('accepts ISO dates separated by commas, spaces or newlines and drops duplicates', () => {
    expect(parseClosureDates('2025-12-24, 2025-11-28\n2025-12-24')).toEqual({
      dates: ['2025-12-24', '2025-11-28'],
      invalid: [],
    })
  })

  it('reports anything that is not a date', () => {
    expect(parseClosureDates('12/24/2025 2025-13-40x').invalid).toEqual(['12/24/2025', '2025-13-40x'])
  })
})

describe('HolidayCalendarPanel', () => {
  it('lists all eleven federal holidays and marks the two commonly worked ones', () => {
    render(<HolidayCalendarPanel calendar={{ exclude: [], closed_dates: [] }} onChange={jest.fn()} />)
    for (const name of US_FEDERAL_HOLIDAYS) {
      expect(screen.getByLabelText(new RegExp(name.replace(/[.']/g, '.')))).toBeInTheDocument()
    }
    expect(screen.getAllByText('(flagged LOW)')).toHaveLength(2)
  })

  it('reports a worked holiday and closure days through onChange', () => {
    const onChange = jest.fn()
    render(<HolidayCalendarPanel calendar={{ exclude: [], closed_dates: [] }} onChange={onChange} />)
    fireEvent.click(screen.getByLabelText(/Columbus Day/))
    expect(onChange).toHaveBeenLastCalledWith({ exclude: ['Columbus Day'], closed_dates: [] })
    fireEvent.change(screen.getByLabelText(/Extra closure days/), { target: { value: '2025-12-24 bad' } })
    expect(onChange).toHaveBeenLastCalledWith({ exclude: [], closed_dates: ['2025-12-24'] })
    expect(screen.getByRole('alert')).toHaveTextContent('bad')
  })
})
