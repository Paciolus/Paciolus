/**
 * Sprint 232: formatting.ts utility tests
 */
import {
  formatCurrency,
  formatCurrencyWhole,
  parseCurrency,
  formatNumber,
  formatPercent,
  formatPercentWhole,
  formatDate,
  formatTime,
  formatDateTime,
  formatDateTimeCompact,
  getRelativeTime,
} from '@/utils/formatting'

describe('formatCurrency', () => {
  it('formats positive amounts', () => {
    expect(formatCurrency(1234.5)).toBe('$1,234.50')
  })

  it('formats zero', () => {
    expect(formatCurrency(0)).toBe('$0.00')
  })

  it('returns dash for zero when showZeroAsEmpty is true', () => {
    expect(formatCurrency(0, true)).toBe('-')
  })

  it('formats negative amounts', () => {
    expect(formatCurrency(-500)).toBe('-$500.00')
  })

  it('rounds to 2 decimal places', () => {
    expect(formatCurrency(99.999)).toBe('$100.00')
  })
})

describe('formatCurrencyWhole', () => {
  it('formats without decimals', () => {
    expect(formatCurrencyWhole(5000)).toBe('$5,000')
  })

  it('rounds to nearest whole number', () => {
    expect(formatCurrencyWhole(1234.56)).toBe('$1,235')
  })
})

describe('parseCurrency', () => {
  it('parses formatted currency strings', () => {
    expect(parseCurrency('$1,234.56')).toBe(1234.56)
  })

  it('parses plain numbers', () => {
    expect(parseCurrency('1234')).toBe(1234)
  })

  it('returns null for invalid input', () => {
    expect(parseCurrency('invalid')).toBeNull()
  })

  it('handles whitespace', () => {
    expect(parseCurrency(' $ 1,000 ')).toBe(1000)
  })
})

describe('formatNumber', () => {
  it('adds thousands separators', () => {
    expect(formatNumber(1234567)).toBe('1,234,567')
  })

  it('handles small numbers', () => {
    expect(formatNumber(42)).toBe('42')
  })
})

describe('formatPercent', () => {
  it('formats decimal as percentage', () => {
    expect(formatPercent(0.1234)).toBe('12.34%')
  })

  it('handles values over 100%', () => {
    expect(formatPercent(1.5)).toBe('150.00%')
  })

  it('formats zero', () => {
    expect(formatPercent(0)).toBe('0.00%')
  })
})

describe('formatPercentWhole', () => {
  it('formats whole number as percentage', () => {
    expect(formatPercentWhole(12.34)).toBe('12.34%')
  })

  it('handles 100%', () => {
    expect(formatPercentWhole(100)).toBe('100.00%')
  })
})

describe('formatDate', () => {
  it('formats ISO string as readable date', () => {
    // Use UTC midnight to avoid timezone shifts
    const result = formatDate('2026-02-04T00:00:00Z')
    expect(result).toMatch(/Feb/)
    expect(result).toMatch(/2026/)
  })
})

describe('formatTime', () => {
  it('formats ISO string as readable time', () => {
    const result = formatTime('2026-02-04T15:45:00Z')
    expect(result).toMatch(/\d{1,2}:\d{2}\s?(AM|PM)/i)
  })
})

describe('formatDateTime', () => {
  it('combines date and time with "at"', () => {
    const result = formatDateTime('2026-02-04T15:45:00Z')
    expect(result).toContain('at')
    expect(result).toMatch(/2026/)
  })
})

describe('formatDateTimeCompact', () => {
  it('formats compact date+time', () => {
    const result = formatDateTimeCompact('2026-02-04T15:45:00Z')
    expect(result).toMatch(/Feb/)
  })
})

describe('getRelativeTime', () => {
  it('returns "Today" for current date', () => {
    expect(getRelativeTime(new Date().toISOString())).toBe('Today')
  })

  it('returns "Yesterday" for one day ago', () => {
    const yesterday = new Date()
    yesterday.setDate(yesterday.getDate() - 1)
    expect(getRelativeTime(yesterday.toISOString())).toBe('Yesterday')
  })

  it('returns "X days ago" for recent dates', () => {
    const threeDaysAgo = new Date()
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3)
    expect(getRelativeTime(threeDaysAgo.toISOString())).toBe('3 days ago')
  })

  it('returns "X weeks ago" for dates within a month', () => {
    const twoWeeksAgo = new Date()
    twoWeeksAgo.setDate(twoWeeksAgo.getDate() - 14)
    expect(getRelativeTime(twoWeeksAgo.toISOString())).toBe('2 weeks ago')
  })

  it('returns formatted date for dates older than a month', () => {
    const result = getRelativeTime('2025-01-15T12:00:00Z')
    expect(result).toMatch(/Jan/)
    expect(result).toMatch(/2025/)
  })
})
