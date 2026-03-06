/**
 * Sprint 232: animations.ts utility tests
 */
import {
  dataFillTransition,
  scoreCircleTransition,
} from '@/utils/animations'

describe('dataFillTransition', () => {
  it('has 0.8s duration', () => {
    expect(dataFillTransition.duration).toBe(0.8)
  })

  it('uses easeOut', () => {
    expect(dataFillTransition.ease).toBe('easeOut')
  })
})

describe('scoreCircleTransition', () => {
  it('has 1.2s duration', () => {
    expect(scoreCircleTransition.duration).toBe(1.2)
  })

  it('uses easeOut', () => {
    expect(scoreCircleTransition.ease).toBe('easeOut')
  })
})
