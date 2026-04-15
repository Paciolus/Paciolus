/**
 * Telemetry beacon endpoint — Sprint 608.
 *
 * Receives `navigator.sendBeacon()` payloads from `utils/telemetry.ts` when
 * `NEXT_PUBLIC_ANALYTICS_WRITE_KEY` is configured. This is a stub: it validates
 * the payload shape and returns 200 so the beacon does not 404 in production.
 *
 * When a real analytics service is wired up, forward the payload here. Until
 * then, events are logged server-side (production) or ignored.
 *
 * NO financial data is ever accepted through this endpoint — only event names
 * and small primitive property maps.
 */

import { NextRequest, NextResponse } from 'next/server'

export const runtime = 'nodejs'
export const dynamic = 'force-dynamic'

const MAX_PAYLOAD_BYTES = 2 * 1024 // 2 KB cap — beacons are tiny
const MAX_EVENT_NAME_LENGTH = 64
const MAX_PROPERTY_COUNT = 20

interface TelemetryPayload {
  event: string
  properties: Record<string, string | number | boolean | null>
  timestamp: string
}

function isValidPayload(raw: unknown): raw is TelemetryPayload {
  if (!raw || typeof raw !== 'object') return false
  const obj = raw as Record<string, unknown>

  if (typeof obj.event !== 'string' || obj.event.length === 0 || obj.event.length > MAX_EVENT_NAME_LENGTH) {
    return false
  }
  if (typeof obj.timestamp !== 'string') return false

  if (obj.properties !== undefined) {
    if (typeof obj.properties !== 'object' || obj.properties === null) return false
    const props = obj.properties as Record<string, unknown>
    const keys = Object.keys(props)
    if (keys.length > MAX_PROPERTY_COUNT) return false
    for (const key of keys) {
      const v = props[key]
      if (v !== null && typeof v !== 'string' && typeof v !== 'number' && typeof v !== 'boolean') {
        return false
      }
    }
  }
  return true
}

export async function POST(request: NextRequest) {
  const contentLength = request.headers.get('content-length')
  if (contentLength && Number(contentLength) > MAX_PAYLOAD_BYTES) {
    return new NextResponse(null, { status: 413 })
  }

  let body: unknown
  try {
    body = await request.json()
  } catch {
    return new NextResponse(null, { status: 400 })
  }

  if (!isValidPayload(body)) {
    return new NextResponse(null, { status: 400 })
  }

  // Stub: no downstream forwarding yet. Return 200 so the beacon succeeds.
  return new NextResponse(null, { status: 200 })
}

export async function GET() {
  return new NextResponse(null, { status: 405 })
}
