/**
 * Sprint 232: themeUtils.ts utility tests
 */
import {
  getHealthClasses,
  getHealthLabel,
  getVarianceClasses,
  getInputClasses,
  getSelectClasses,
  getBadgeClasses,
  getRiskLevelClasses,
  cx,
  HEALTH_STATUS_CLASSES,
  INPUT_BASE_CLASSES,
  INPUT_STATE_CLASSES,
  BADGE_CLASSES,
  RISK_LEVEL_CLASSES,
} from '@/utils/themeUtils'

describe('getHealthClasses', () => {
  it('returns sage classes for above_threshold', () => {
    const classes = getHealthClasses('above_threshold')
    expect(classes.border).toContain('sage')
    expect(classes.bg).toContain('sage')
  })

  it('returns oatmeal classes for at_threshold', () => {
    const classes = getHealthClasses('at_threshold')
    expect(classes.border).toContain('oatmeal')
  })

  it('returns clay classes for below_threshold', () => {
    const classes = getHealthClasses('below_threshold')
    expect(classes.border).toContain('clay')
  })

  it('returns neutral classes for neutral', () => {
    const classes = getHealthClasses('neutral')
    expect(classes.border).toBe('border-theme')
  })

  it('returns all 4 class properties', () => {
    const classes = getHealthClasses('above_threshold')
    expect(classes).toHaveProperty('border')
    expect(classes).toHaveProperty('bg')
    expect(classes).toHaveProperty('badge')
    expect(classes).toHaveProperty('icon')
  })
})

describe('getHealthLabel', () => {
  it('returns Above for above_threshold', () => {
    expect(getHealthLabel('above_threshold')).toBe('Above')
  })

  it('returns Near for at_threshold', () => {
    expect(getHealthLabel('at_threshold')).toBe('Near')
  })

  it('returns Below for below_threshold', () => {
    expect(getHealthLabel('below_threshold')).toBe('Below')
  })

  it('returns N/A for neutral', () => {
    expect(getHealthLabel('neutral')).toBe('N/A')
  })
})

describe('getVarianceClasses', () => {
  it('returns sage for positive', () => {
    expect(getVarianceClasses('positive')).toContain('sage')
  })

  it('returns clay for negative', () => {
    expect(getVarianceClasses('negative')).toContain('clay')
  })

  it('returns content-secondary for neutral', () => {
    expect(getVarianceClasses('neutral')).toContain('content-secondary')
  })
})

describe('getInputClasses', () => {
  it('returns default classes when untouched', () => {
    const result = getInputClasses(false, false)
    expect(result).toContain(INPUT_BASE_CLASSES)
    expect(result).toContain(INPUT_STATE_CLASSES.default)
  })

  it('returns error classes when touched with error', () => {
    const result = getInputClasses(true, true)
    expect(result).toContain(INPUT_STATE_CLASSES.error)
  })

  it('returns valid classes when touched with value and no error', () => {
    const result = getInputClasses(true, false, true)
    expect(result).toContain(INPUT_STATE_CLASSES.valid)
  })

  it('returns disabled classes when disabled', () => {
    const result = getInputClasses(false, false, false, true)
    expect(result).toContain(INPUT_STATE_CLASSES.disabled)
  })

  it('disabled takes priority over error', () => {
    const result = getInputClasses(true, true, true, true)
    expect(result).toContain(INPUT_STATE_CLASSES.disabled)
    expect(result).not.toContain(INPUT_STATE_CLASSES.error)
  })
})

describe('getSelectClasses', () => {
  it('includes appearance-none and cursor-pointer', () => {
    const result = getSelectClasses()
    expect(result).toContain('appearance-none')
    expect(result).toContain('cursor-pointer')
  })

  it('uses disabled state when disabled', () => {
    const result = getSelectClasses(true)
    expect(result).toContain(INPUT_STATE_CLASSES.disabled)
  })
})

describe('getBadgeClasses', () => {
  it('returns sage classes for success', () => {
    expect(getBadgeClasses('success')).toContain('sage')
  })

  it('returns clay classes for error', () => {
    expect(getBadgeClasses('error')).toContain('clay')
  })

  it('returns oatmeal classes for warning', () => {
    expect(getBadgeClasses('warning')).toContain('oatmeal')
  })
})

describe('getRiskLevelClasses', () => {
  it('returns clay for high risk', () => {
    expect(getRiskLevelClasses('high')).toContain('clay')
  })

  it('returns oatmeal for medium risk', () => {
    expect(getRiskLevelClasses('medium')).toContain('oatmeal')
  })

  it('returns sage for low risk', () => {
    expect(getRiskLevelClasses('low')).toContain('sage')
  })

  it('returns neutral for no risk', () => {
    expect(getRiskLevelClasses('none')).toContain('content-secondary')
  })
})

describe('cx', () => {
  it('joins class strings', () => {
    expect(cx('a', 'b', 'c')).toBe('a b c')
  })

  it('filters out falsy values', () => {
    expect(cx('a', false, 'b', undefined, null, 'c')).toBe('a b c')
  })

  it('returns empty string for no truthy values', () => {
    expect(cx(false, undefined, null)).toBe('')
  })
})

describe('HEALTH_STATUS_CLASSES constant', () => {
  it('has all 4 status keys', () => {
    expect(Object.keys(HEALTH_STATUS_CLASSES)).toEqual(['above_threshold', 'at_threshold', 'below_threshold', 'neutral'])
  })
})

describe('BADGE_CLASSES constant', () => {
  it('has all 5 variant keys', () => {
    expect(Object.keys(BADGE_CLASSES)).toEqual(['success', 'error', 'warning', 'neutral', 'info'])
  })
})

describe('RISK_LEVEL_CLASSES constant', () => {
  it('has all 4 level keys', () => {
    expect(Object.keys(RISK_LEVEL_CLASSES)).toEqual(['high', 'medium', 'low', 'none'])
  })
})
