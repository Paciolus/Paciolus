/**
 * Sprint 232: constants.ts utility tests
 */
import {
  API_URL,
  DEFAULT_REQUEST_TIMEOUT,
  DOWNLOAD_TIMEOUT,
  MAX_RETRIES,
  BASE_RETRY_DELAY,
  DEFAULT_CACHE_TTL,
  minutes,
  hours,
} from '@/utils/constants'

describe('minutes', () => {
  it('converts 1 minute to milliseconds', () => {
    expect(minutes(1)).toBe(60_000)
  })

  it('converts 5 minutes to milliseconds', () => {
    expect(minutes(5)).toBe(300_000)
  })

  it('handles zero', () => {
    expect(minutes(0)).toBe(0)
  })

  it('handles fractional minutes', () => {
    expect(minutes(0.5)).toBe(30_000)
  })
})

describe('hours', () => {
  it('converts 1 hour to milliseconds', () => {
    expect(hours(1)).toBe(3_600_000)
  })

  it('converts 24 hours to milliseconds', () => {
    expect(hours(24)).toBe(86_400_000)
  })

  it('handles zero', () => {
    expect(hours(0)).toBe(0)
  })
})

describe('constant values', () => {
  it('API_URL defaults to localhost:8000', () => {
    expect(API_URL).toBe('http://localhost:8000')
  })

  it('DEFAULT_REQUEST_TIMEOUT is 30 seconds', () => {
    expect(DEFAULT_REQUEST_TIMEOUT).toBe(30_000)
  })

  it('DOWNLOAD_TIMEOUT is 60 seconds', () => {
    expect(DOWNLOAD_TIMEOUT).toBe(60_000)
  })

  it('MAX_RETRIES is 3', () => {
    expect(MAX_RETRIES).toBe(3)
  })

  it('BASE_RETRY_DELAY is 1 second', () => {
    expect(BASE_RETRY_DELAY).toBe(1_000)
  })

  it('DEFAULT_CACHE_TTL is 5 minutes', () => {
    expect(DEFAULT_CACHE_TTL).toBe(minutes(5))
  })
})
