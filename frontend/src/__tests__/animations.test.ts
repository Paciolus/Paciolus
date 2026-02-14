/**
 * Sprint 232: animations.ts utility tests
 */
import {
  fadeInUp,
  fadeInUpSpring,
  fadeIn,
  dataFillTransition,
  scoreCircleTransition,
} from '@/utils/animations'

describe('fadeInUp', () => {
  it('has initial with opacity 0 and y offset', () => {
    expect(fadeInUp.initial).toEqual({ opacity: 0, y: 12 })
  })

  it('has animate with opacity 1 and y 0', () => {
    expect(fadeInUp.animate).toEqual({ opacity: 1, y: 0 })
  })
})

describe('fadeInUpSpring', () => {
  it('has initial with opacity 0 and y 20', () => {
    expect(fadeInUpSpring.initial).toEqual({ opacity: 0, y: 20 })
  })

  it('has animate with opacity 1 and y 0', () => {
    expect(fadeInUpSpring.animate).toEqual({ opacity: 1, y: 0 })
  })

  it('uses spring transition', () => {
    expect(fadeInUpSpring.transition).toEqual({ duration: 0.5, type: 'spring' })
  })
})

describe('fadeIn', () => {
  it('has initial with opacity 0', () => {
    expect(fadeIn.initial).toEqual({ opacity: 0 })
  })

  it('has animate with opacity 1', () => {
    expect(fadeIn.animate).toEqual({ opacity: 1 })
  })

  it('has exit with opacity 0', () => {
    expect(fadeIn.exit).toEqual({ opacity: 0 })
  })
})

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
