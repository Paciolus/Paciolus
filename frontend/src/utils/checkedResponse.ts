/**
 * Sprint 890 (CEO brief 15C, review ST-10): check a response before treating it as its type.
 *
 * The upload hooks cast `data as T` without looking at it. This checks the top-level keys the
 * backend's published schema marks required (generated into types/generated/responseRequiredKeys.ts)
 * and throws when one is missing, so a malformed response shows an error instead of a broken page.
 */
import { RESPONSE_REQUIRED_KEYS } from '@/types/generated/responseRequiredKeys'

export class ResponseShapeError extends Error {
  readonly missing: string[]

  constructor(endpoint: string, missing: string[]) {
    super(`The response from ${endpoint} is missing ${missing.join(', ')}.`)
    this.name = 'ResponseShapeError'
    this.missing = missing
  }
}

export function checkedResponse<T>(endpoint: string, data: unknown): T {
  if (data === null || typeof data !== 'object' || Array.isArray(data)) {
    throw new ResponseShapeError(endpoint, ['the response body'])
  }
  const required = RESPONSE_REQUIRED_KEYS[endpoint] ?? []
  const record = data as Record<string, unknown>
  const missing = required.filter(key => !(key in record))
  if (missing.length > 0) throw new ResponseShapeError(endpoint, missing)
  return data as T
}
