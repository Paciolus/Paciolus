/**
 * Sprint 752: pure validation engine tests.
 *
 * Demonstrates the engine's testability without React — no `renderHook`,
 * no `act`, no mocks. The same logic that powers `useFormValidation` is
 * exercised here as plain function calls.
 */
import {
  isFormDirty,
  isFormValid,
  validateAllFields,
  validateFieldValue,
  type ValidationRules,
} from '@/lib/validation/engine'
import { commonValidators } from '@/lib/validation/validators'

interface SignupForm {
  name: string
  email: string
  age: number | ''
  agree: boolean
  [key: string]: unknown
}

const baseValues: SignupForm = {
  name: '',
  email: '',
  age: '',
  agree: false,
}

const rules: ValidationRules<SignupForm> = {
  name: [
    commonValidators.required('Name required') as never,
    commonValidators.minLength(2, 'Name too short') as never,
  ],
  email: [
    commonValidators.required('Email required') as never,
    commonValidators.email('Bad email') as never,
  ],
  age: [
    commonValidators.min(18, 'Must be 18+') as never,
  ],
}

describe('validateFieldValue', () => {
  it('returns undefined when no rules exist for the field', () => {
    expect(validateFieldValue('agree', baseValues, rules)).toBeUndefined()
  })

  it('returns the first failing message', () => {
    const values = { ...baseValues, name: '' }
    expect(validateFieldValue('name', values, rules)).toBe('Name required')
  })

  it('returns the next-rule message after the first one passes', () => {
    const values = { ...baseValues, name: 'A' }
    expect(validateFieldValue('name', values, rules)).toBe('Name too short')
  })

  it('returns undefined when every rule passes', () => {
    const values = { ...baseValues, name: 'Alice' }
    expect(validateFieldValue('name', values, rules)).toBeUndefined()
  })

  it('passes the full values object to the rule function (for cross-field rules)', () => {
    const passwordRules: ValidationRules<{ pw: string; confirm: string }> = {
      confirm: [commonValidators.matches('pw', 'Passwords differ')],
    }
    expect(
      validateFieldValue('confirm', { pw: 'a', confirm: 'b' }, passwordRules),
    ).toBe('Passwords differ')
    expect(
      validateFieldValue('confirm', { pw: 'a', confirm: 'a' }, passwordRules),
    ).toBeUndefined()
  })
})

describe('validateAllFields', () => {
  it('returns an empty errors map when every field is valid', () => {
    const values: SignupForm = {
      name: 'Alice',
      email: 'a@b.co',
      age: 21,
      agree: true,
    }
    expect(validateAllFields(values, rules)).toEqual({})
  })

  it('collects the first failing message per field', () => {
    const values = baseValues
    expect(validateAllFields(values, rules)).toEqual({
      name: 'Name required',
      email: 'Email required',
    })
  })

  it('does not include passing fields in the errors map', () => {
    const values: SignupForm = {
      name: 'Alice',
      email: '',
      age: '',
      agree: false,
    }
    const errors = validateAllFields(values, rules)
    expect(errors.name).toBeUndefined()
    expect(errors.email).toBe('Email required')
  })
})

describe('isFormValid', () => {
  it('returns true when every field passes', () => {
    expect(isFormValid({ name: 'Ada', email: 'a@b.co', age: 25, agree: true }, rules)).toBe(true)
  })

  it('short-circuits and returns false on the first failing field', () => {
    expect(isFormValid(baseValues, rules)).toBe(false)
  })
})

describe('isFormDirty', () => {
  it('returns false when values strictly equal initialValues', () => {
    expect(isFormDirty(baseValues, baseValues)).toBe(false)
  })

  it('returns true when any field differs', () => {
    expect(isFormDirty({ ...baseValues, name: 'Ada' }, baseValues)).toBe(true)
  })

  it('compares with strict equality (no deep checks)', () => {
    // Two structurally-equal arrays at different references → dirty.
    const init = { ...baseValues, tags: [] as string[] } as SignupForm
    const next = { ...baseValues, tags: [] as string[] } as SignupForm
    expect(isFormDirty(next, init)).toBe(true)
  })
})

describe('commonValidators', () => {
  it('required: trims strings; rejects empty', () => {
    const rule = commonValidators.required()
    expect(rule.test('  ', {} as never)).toBe(false)
    expect(rule.test('a', {} as never)).toBe(true)
    expect(rule.test(null, {} as never)).toBe(false)
    expect(rule.test(undefined, {} as never)).toBe(false)
  })

  it('required: booleans always pass (checkboxes)', () => {
    expect(commonValidators.required().test(false, {} as never)).toBe(true)
    expect(commonValidators.required().test(true, {} as never)).toBe(true)
  })

  it('email: rejects malformed; passes empty (defers to required)', () => {
    const rule = commonValidators.email()
    expect(rule.test('not-an-email', {} as never)).toBe(false)
    expect(rule.test('a@b.co', {} as never)).toBe(true)
    expect(rule.test('', {} as never)).toBe(true)
  })

  it('min/max: parses string numbers via parseFloat', () => {
    expect(commonValidators.min(10).test('5', {} as never)).toBe(false)
    expect(commonValidators.min(10).test('15', {} as never)).toBe(true)
    expect(commonValidators.max(10).test('15', {} as never)).toBe(false)
    expect(commonValidators.max(10).test('5', {} as never)).toBe(true)
  })

  it('pattern: skips empty values', () => {
    const rule = commonValidators.pattern(/^[A-Z]{3}$/)
    expect(rule.test('', {} as never)).toBe(true)
    expect(rule.test('abc', {} as never)).toBe(false)
    expect(rule.test('ABC', {} as never)).toBe(true)
  })

  it('matches: cross-field comparison works', () => {
    const rule = commonValidators.matches<{ a: string; b: string }>('a')
    expect(rule.test('x', { a: 'x', b: 'x' })).toBe(true)
    expect(rule.test('y', { a: 'x', b: 'y' })).toBe(false)
  })
})
