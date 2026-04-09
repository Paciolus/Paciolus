/**
 * BrandIcon component tests
 *
 * Tests: rendering with various icon names, className prop.
 */
import { BrandIcon } from '@/components/shared/BrandIcon/BrandIcon'
import type { BrandIconName } from '@/components/shared/BrandIcon/types'
import { render } from '@/test-utils'

describe('BrandIcon', () => {
  it('renders an SVG element', () => {
    const { container } = render(<BrandIcon name="padlock" />)
    expect(container.querySelector('svg')).toBeInTheDocument()
  })

  it('applies className prop', () => {
    const { container } = render(<BrandIcon name="padlock" className="w-4 h-4 text-sage-500" />)
    const svg = container.querySelector('svg')
    expect(svg).toHaveClass('w-4')
    expect(svg).toHaveClass('h-4')
  })

  it('renders different icons', () => {
    const icons: BrandIconName[] = ['padlock', 'shield-check', 'calculator', 'bar-chart', 'chevron-right', 'chevron-down']
    for (const name of icons) {
      const { container } = render(<BrandIcon name={name} />)
      expect(container.querySelector('svg')).toBeInTheDocument()
    }
  })

  it('renders with default styling when no className', () => {
    const { container } = render(<BrandIcon name="padlock" />)
    const svg = container.querySelector('svg')
    expect(svg).toBeInTheDocument()
  })
})
