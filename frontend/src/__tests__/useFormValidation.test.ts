/**
 * Sprint 234: useFormValidation + commonValidators tests
 */
import { renderHook, act } from '@testing-library/react'
import { useFormValidation, commonValidators } from '@/hooks/useFormValidation'

type TestForm = {
  name: string
  email: string
  age: string
}

const defaultConfig = {
  initialValues: { name: '', email: '', age: '' } as TestForm,
  validationRules: {
    name: [commonValidators.required('Name is required')],
    email: [
      commonValidators.required('Email is required'),
      commonValidators.email(),
    ],
  },
}

describe('useFormValidation', () => {
  it('initializes with provided values', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    expect(result.current.values).toEqual({ name: '', email: '', age: '' })
    expect(result.current.errors).toEqual({})
    expect(result.current.touched).toEqual({})
    expect(result.current.isSubmitting).toBe(false)
    expect(result.current.isSubmitted).toBe(false)
  })

  it('setValue updates a field', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.setValue('name', 'John') })
    expect(result.current.values.name).toBe('John')
  })

  it('setValues updates multiple fields', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.setValues({ name: 'Jane', email: 'jane@test.com' }) })
    expect(result.current.values.name).toBe('Jane')
    expect(result.current.values.email).toBe('jane@test.com')
  })

  it('isDirty is false initially', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    expect(result.current.isDirty).toBe(false)
  })

  it('isDirty is true after change', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.setValue('name', 'Changed') })
    expect(result.current.isDirty).toBe(true)
  })

  it('isValid reflects validation state', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    // Initially invalid (required fields empty)
    expect(result.current.isValid).toBe(false)

    act(() => {
      result.current.setValue('name', 'John')
      result.current.setValue('email', 'john@test.com')
    })
    expect(result.current.isValid).toBe(true)
  })

  it('validateField returns error for invalid field', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    const error = result.current.validateField('name')
    expect(error).toBe('Name is required')
  })

  it('validateField returns undefined for valid field', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.setValue('name', 'John') })
    const error = result.current.validateField('name')
    expect(error).toBeUndefined()
  })

  it('validate checks all fields', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    let isValid: boolean
    act(() => { isValid = result.current.validate() })
    expect(isValid!).toBe(false)
    expect(result.current.errors.name).toBe('Name is required')
    expect(result.current.errors.email).toBe('Email is required')
  })

  it('handleBlur marks field as touched and validates', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.handleBlur('name')() })
    expect(result.current.touched.name).toBe(true)
    expect(result.current.errors.name).toBe('Name is required')
  })

  it('setError sets custom error', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.setError('name', 'Server error') })
    expect(result.current.errors.name).toBe('Server error')
  })

  it('clearErrors removes all errors', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => {
      result.current.setError('name', 'Error 1')
      result.current.setError('email', 'Error 2')
    })
    act(() => { result.current.clearErrors() })
    expect(result.current.errors).toEqual({})
  })

  it('setAllTouched marks all fields', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.setAllTouched() })
    expect(result.current.touched.name).toBe(true)
    expect(result.current.touched.email).toBe(true)
    expect(result.current.touched.age).toBe(true)
  })

  it('reset clears form state', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => {
      result.current.setValue('name', 'John')
      result.current.setError('email', 'Bad')
      result.current.handleBlur('name')()
    })
    act(() => { result.current.reset() })
    expect(result.current.values).toEqual({ name: '', email: '', age: '' })
    expect(result.current.errors).toEqual({})
    expect(result.current.touched).toEqual({})
  })

  it('reset with new initial values', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.reset({ name: 'New', email: 'new@test.com', age: '25' }) })
    expect(result.current.values.name).toBe('New')
    expect(result.current.values.email).toBe('new@test.com')
  })

  it('handleSubmit prevents default and calls onSubmit when valid', async () => {
    const onSubmit = jest.fn()
    const { result } = renderHook(() =>
      useFormValidation({
        ...defaultConfig,
        initialValues: { name: 'John', email: 'john@test.com', age: '25' },
        onSubmit,
      })
    )

    const preventDefault = jest.fn()
    await act(async () => {
      await result.current.handleSubmit({ preventDefault } as unknown as React.FormEvent)
    })

    expect(preventDefault).toHaveBeenCalled()
    expect(onSubmit).toHaveBeenCalledWith({ name: 'John', email: 'john@test.com', age: '25' })
  })

  it('handleSubmit does NOT call onSubmit when invalid', async () => {
    const onSubmit = jest.fn()
    const { result } = renderHook(() =>
      useFormValidation({ ...defaultConfig, onSubmit })
    )

    await act(async () => { await result.current.handleSubmit() })

    expect(onSubmit).not.toHaveBeenCalled()
    expect(result.current.isSubmitted).toBe(true)
  })

  it('getFieldProps returns value, onChange, onBlur', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    const props = result.current.getFieldProps('name')
    expect(props).toHaveProperty('value')
    expect(props).toHaveProperty('onChange')
    expect(props).toHaveProperty('onBlur')
  })

  it('getFieldState returns field metadata', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    const state = result.current.getFieldState('name')
    expect(state).toEqual({
      error: undefined,
      touched: false,
      hasValue: false,
      hasError: false,
      showError: false,
    })
  })

  it('getFieldState showError is true when touched and has error', () => {
    const { result } = renderHook(() => useFormValidation(defaultConfig))
    act(() => { result.current.handleBlur('name')() })
    const state = result.current.getFieldState('name')
    expect(state.showError).toBe(true)
    expect(state.hasError).toBe(true)
    expect(state.touched).toBe(true)
  })
})

// =============================================================================
// COMMON VALIDATORS
// =============================================================================

describe('commonValidators.required', () => {
  const rule = commonValidators.required()

  it('fails for empty string', () => {
    expect(rule.test('', {} as TestForm)).toBe(false)
  })

  it('fails for whitespace-only string', () => {
    expect(rule.test('   ', {} as TestForm)).toBe(false)
  })

  it('passes for non-empty string', () => {
    expect(rule.test('hello', {} as TestForm)).toBe(true)
  })

  it('passes for boolean true', () => {
    expect(rule.test(true, {} as TestForm)).toBe(true)
  })

  it('passes for boolean false', () => {
    expect(rule.test(false, {} as TestForm)).toBe(true)
  })

  it('fails for null', () => {
    expect(rule.test(null, {} as TestForm)).toBe(false)
  })

  it('uses custom message', () => {
    const custom = commonValidators.required('Custom required')
    expect(custom.message).toBe('Custom required')
  })
})

describe('commonValidators.email', () => {
  const rule = commonValidators.email()

  it('passes for valid email', () => {
    expect(rule.test('user@example.com', {} as TestForm)).toBe(true)
  })

  it('fails for missing @', () => {
    expect(rule.test('userexample.com', {} as TestForm)).toBe(false)
  })

  it('fails for missing domain', () => {
    expect(rule.test('user@', {} as TestForm)).toBe(false)
  })

  it('passes for empty string (let required handle it)', () => {
    expect(rule.test('', {} as TestForm)).toBe(true)
  })
})

describe('commonValidators.minLength', () => {
  const rule = commonValidators.minLength(3)

  it('fails for short string', () => {
    expect(rule.test('ab', {} as TestForm)).toBe(false)
  })

  it('passes for string at minimum', () => {
    expect(rule.test('abc', {} as TestForm)).toBe(true)
  })

  it('passes for non-string values', () => {
    expect(rule.test(42, {} as TestForm)).toBe(true)
  })

  it('uses default message', () => {
    expect(rule.message).toBe('Must be at least 3 characters')
  })
})

describe('commonValidators.maxLength', () => {
  const rule = commonValidators.maxLength(5)

  it('passes for short string', () => {
    expect(rule.test('abc', {} as TestForm)).toBe(true)
  })

  it('fails for too-long string', () => {
    expect(rule.test('abcdef', {} as TestForm)).toBe(false)
  })
})

describe('commonValidators.min', () => {
  const rule = commonValidators.min(10)

  it('fails for value below minimum', () => {
    expect(rule.test('5', {} as TestForm)).toBe(false)
  })

  it('passes for value at minimum', () => {
    expect(rule.test('10', {} as TestForm)).toBe(true)
  })

  it('passes for non-numeric string', () => {
    expect(rule.test('abc', {} as TestForm)).toBe(true)
  })
})

describe('commonValidators.max', () => {
  const rule = commonValidators.max(100)

  it('passes for value below maximum', () => {
    expect(rule.test('50', {} as TestForm)).toBe(true)
  })

  it('fails for value above maximum', () => {
    expect(rule.test('101', {} as TestForm)).toBe(false)
  })
})

describe('commonValidators.pattern', () => {
  const rule = commonValidators.pattern(/^\d{3}-\d{4}$/, 'Invalid format')

  it('passes for matching pattern', () => {
    expect(rule.test('123-4567', {} as TestForm)).toBe(true)
  })

  it('fails for non-matching pattern', () => {
    expect(rule.test('abc', {} as TestForm)).toBe(false)
  })

  it('passes for empty string', () => {
    expect(rule.test('', {} as TestForm)).toBe(true)
  })
})

describe('commonValidators.matches', () => {
  type PasswordForm = { password: string; confirm: string }
  const rule = commonValidators.matches<PasswordForm>('password', 'Passwords must match')

  it('passes when fields match', () => {
    expect(rule.test('abc123', { password: 'abc123', confirm: 'abc123' })).toBe(true)
  })

  it('fails when fields differ', () => {
    expect(rule.test('abc123', { password: 'different', confirm: 'abc123' })).toBe(false)
  })
})
