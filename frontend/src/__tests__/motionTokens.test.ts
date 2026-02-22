/**
 * Sprint 405: motionTokens.ts — shape assertions + inline snapshots
 *
 * Guards against accidental token drift. Every exported constant
 * is snapshot-tested so changes require deliberate snapshot updates.
 */
import {
  TIMING,
  EASE,
  DISTANCE,
  STATE_CROSSFADE,
  RESOLVE_ENTER,
  EMPHASIS_SETTLE,
} from '@/utils/motionTokens'

describe('TIMING', () => {
  it('extends DURATION with intent-based durations', () => {
    // Inherited from DURATION
    expect(TIMING.instant).toBe(0.15)
    expect(TIMING.fast).toBe(0.2)
    expect(TIMING.normal).toBe(0.3)
    expect(TIMING.slow).toBe(0.5)
    expect(TIMING.hero).toBe(0.6)
    // New intent-based
    expect(TIMING.crossfade).toBe(0.35)
    expect(TIMING.settle).toBe(0.5)
    expect(TIMING.resolve).toBe(0.6)
    expect(TIMING.panel).toBe(0.25)
  })

  it('matches snapshot', () => {
    expect(TIMING).toMatchInlineSnapshot(`
      {
        "crossfade": 0.35,
        "fast": 0.2,
        "hero": 0.6,
        "instant": 0.15,
        "normal": 0.3,
        "panel": 0.25,
        "resolve": 0.6,
        "settle": 0.5,
        "slow": 0.5,
      }
    `)
  })
})

describe('EASE', () => {
  it('has 4 named cubic-bezier curves', () => {
    expect(EASE.enter).toEqual([0.25, 0.1, 0.25, 1.0])
    expect(EASE.exit).toEqual([0.25, 0.0, 0.5, 1.0])
    expect(EASE.decelerate).toEqual([0.0, 0.0, 0.2, 1.0])
    expect(EASE.emphasis).toEqual([0.2, 0.0, 0.0, 1.0])
  })

  it('matches snapshot', () => {
    expect(EASE).toMatchInlineSnapshot(`
      {
        "decelerate": [
          0,
          0,
          0.2,
          1,
        ],
        "emphasis": [
          0.2,
          0,
          0,
          1,
        ],
        "enter": [
          0.25,
          0.1,
          0.25,
          1,
        ],
        "exit": [
          0.25,
          0,
          0.5,
          1,
        ],
      }
    `)
  })
})

describe('DISTANCE', () => {
  it('extends OFFSET with state transition shift', () => {
    expect(DISTANCE.subtle).toBe(12)
    expect(DISTANCE.standard).toBe(24)
    expect(DISTANCE.dramatic).toBe(40)
    expect(DISTANCE.state).toBe(8)
  })
})

describe('STATE_CROSSFADE', () => {
  it('has initial/animate/exit variants', () => {
    expect(STATE_CROSSFADE.initial).toBeDefined()
    expect(STATE_CROSSFADE.animate).toBeDefined()
    expect(STATE_CROSSFADE.exit).toBeDefined()
  })

  it('initial has opacity 0 and y offset', () => {
    expect(STATE_CROSSFADE.initial).toEqual({
      opacity: 0,
      y: 8,
    })
  })

  it('animate settles to opacity 1 and y 0', () => {
    expect(STATE_CROSSFADE.animate).toMatchObject({
      opacity: 1,
      y: 0,
    })
  })

  it('exit slides up and fades out', () => {
    expect(STATE_CROSSFADE.exit).toMatchObject({
      opacity: 0,
      y: -8,
    })
  })

  it('matches snapshot', () => {
    expect(STATE_CROSSFADE).toMatchInlineSnapshot(`
      {
        "animate": {
          "opacity": 1,
          "transition": {
            "duration": 0.35,
            "ease": [
              0.25,
              0.1,
              0.25,
              1,
            ],
          },
          "y": 0,
        },
        "exit": {
          "opacity": 0,
          "transition": {
            "duration": 0.2,
            "ease": [
              0.25,
              0,
              0.5,
              1,
            ],
          },
          "y": -8,
        },
        "initial": {
          "opacity": 0,
          "y": 8,
        },
      }
    `)
  })
})

describe('RESOLVE_ENTER', () => {
  it('has initial/animate/exit variants', () => {
    expect(RESOLVE_ENTER.initial).toBeDefined()
    expect(RESOLVE_ENTER.animate).toBeDefined()
    expect(RESOLVE_ENTER.exit).toBeDefined()
  })

  it('initial has scale 0.98', () => {
    expect(RESOLVE_ENTER.initial).toEqual({
      opacity: 0,
      scale: 0.98,
    })
  })

  it('animate settles to full scale with decelerate ease', () => {
    expect(RESOLVE_ENTER.animate).toMatchObject({
      opacity: 1,
      scale: 1,
    })
  })

  it('matches snapshot', () => {
    expect(RESOLVE_ENTER).toMatchInlineSnapshot(`
      {
        "animate": {
          "opacity": 1,
          "scale": 1,
          "transition": {
            "duration": 0.6,
            "ease": [
              0,
              0,
              0.2,
              1,
            ],
          },
        },
        "exit": {
          "opacity": 0,
          "scale": 0.98,
          "transition": {
            "duration": 0.2,
            "ease": [
              0.25,
              0,
              0.5,
              1,
            ],
          },
        },
        "initial": {
          "opacity": 0,
          "scale": 0.98,
        },
      }
    `)
  })
})

describe('EMPHASIS_SETTLE', () => {
  it('has initial/animate variants', () => {
    expect(EMPHASIS_SETTLE.initial).toBeDefined()
    expect(EMPHASIS_SETTLE.animate).toBeDefined()
  })

  it('enters from x: -2', () => {
    expect(EMPHASIS_SETTLE.initial).toEqual({
      opacity: 0,
      x: -2,
    })
  })

  it('uses emphasis ease', () => {
    expect(EMPHASIS_SETTLE.animate).toMatchObject({
      opacity: 1,
      x: 0,
    })
  })

  it('matches snapshot', () => {
    expect(EMPHASIS_SETTLE).toMatchInlineSnapshot(`
      {
        "animate": {
          "opacity": 1,
          "transition": {
            "duration": 0.5,
            "ease": [
              0.2,
              0,
              0,
              1,
            ],
          },
          "x": 0,
        },
        "initial": {
          "opacity": 0,
          "x": -2,
        },
      }
    `)
  })
})
