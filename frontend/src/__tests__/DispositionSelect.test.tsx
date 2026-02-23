/**
 * DispositionSelect component tests — Sprint 277
 *
 * Tests: select rendering, option count, selected value,
 * onChange callback, disabled state.
 */
import { DispositionSelect } from '@/components/engagement/DispositionSelect'
import { render, screen, fireEvent } from '@/test-utils'

jest.mock('framer-motion', () => {
  const R = require('react')
  return {
    motion: new Proxy(
      {},
      {
        get: (_: unknown, tag: string) =>
          R.forwardRef(
            (
              {
                initial,
                animate,
                exit,
                transition,
                variants,
                whileHover,
                whileInView,
                whileTap,
                viewport,
                layout,
                layoutId,
                ...rest
              }: any,
              ref: any,
            ) => R.createElement(tag, { ...rest, ref }),
          ),
      },
    ),
    AnimatePresence: ({ children }: any) => children,
  }
})

jest.mock('@/utils/themeUtils', () => ({
  getSelectClasses: jest.fn(() => 'mock-select-class'),
}))

jest.mock('@/types/engagement', () => ({
  DISPOSITION_LABELS: {
    not_reviewed: 'Not Reviewed',
    investigated_no_issue: 'Investigated \u2014 No Issue',
    investigated_adjustment_posted: 'Investigated \u2014 Adjustment Posted',
    investigated_further_review: 'Investigated \u2014 Further Review',
    immaterial: 'Immaterial',
  },
}))


describe('DispositionSelect', () => {
  const defaultProps = {
    value: 'not_reviewed' as const,
    onChange: jest.fn(),
  }

  beforeEach(() => {
    jest.clearAllMocks()
  })

  it('renders a select element', () => {
    render(<DispositionSelect {...defaultProps} />)
    const select = screen.getByRole('combobox')
    expect(select).toBeInTheDocument()
  })

  it('renders all 5 disposition options', () => {
    render(<DispositionSelect {...defaultProps} />)
    const options = screen.getAllByRole('option')
    expect(options).toHaveLength(5)
    expect(screen.getByText('Not Reviewed')).toBeInTheDocument()
    expect(screen.getByText('Investigated \u2014 No Issue')).toBeInTheDocument()
    expect(screen.getByText('Investigated \u2014 Adjustment Posted')).toBeInTheDocument()
    expect(screen.getByText('Investigated \u2014 Further Review')).toBeInTheDocument()
    expect(screen.getByText('Immaterial')).toBeInTheDocument()
  })

  it('shows correct selected value', () => {
    render(<DispositionSelect {...defaultProps} value="immaterial" />)
    const select = screen.getByRole('combobox') as HTMLSelectElement
    expect(select.value).toBe('immaterial')
  })

  it('calls onChange when selection changes', () => {
    const onChange = jest.fn()
    render(<DispositionSelect {...defaultProps} onChange={onChange} />)
    fireEvent.change(screen.getByRole('combobox'), {
      target: { value: 'investigated_no_issue' },
    })
    expect(onChange).toHaveBeenCalledWith('investigated_no_issue')
  })

  it('is disabled when disabled prop is true', () => {
    render(<DispositionSelect {...defaultProps} disabled={true} />)
    const select = screen.getByRole('combobox') as HTMLSelectElement
    expect(select.disabled).toBe(true)
  })
})
