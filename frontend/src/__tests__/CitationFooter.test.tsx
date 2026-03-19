/**
 * CitationFooter component tests
 *
 * Tests: rendering with valid standards, empty rendering,
 * link display, code and full name.
 */
import { CitationFooter } from '@/components/shared/CitationFooter'
import { render, screen } from '@/test-utils'

jest.mock('@/lib/citations', () => ({
  getCitation: (code: string) => {
    const citations: Record<string, any> = {
      'ISA 240': {
        code: 'ISA 240',
        fullName: 'Fraud in an Audit of Financial Statements',
        officialUrl: 'https://example.com/isa240',
        officialNote: 'IFAC eISA',
        freeUrl: 'https://example.com/isa240-free',
        freeNote: 'IAASB open',
      },
      'PCAOB AS 2401': {
        code: 'PCAOB AS 2401',
        fullName: 'Consideration of Fraud',
        officialUrl: 'https://example.com/as2401',
        officialNote: 'PCAOB Standards',
        freeUrl: null,
        freeNote: null,
      },
    }
    return citations[code] ?? null
  },
}))

describe('CitationFooter', () => {
  it('renders nothing when no valid standards', () => {
    const { container } = render(<CitationFooter standards={['INVALID']} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders nothing for empty standards array', () => {
    const { container } = render(<CitationFooter standards={[]} />)
    expect(container.firstChild).toBeNull()
  })

  it('renders Standards Referenced heading', () => {
    render(<CitationFooter standards={['ISA 240']} />)
    expect(screen.getByText('Standards Referenced')).toBeInTheDocument()
  })

  it('renders citation code and full name', () => {
    render(<CitationFooter standards={['ISA 240']} />)
    expect(screen.getByText('ISA 240')).toBeInTheDocument()
    expect(screen.getByText('Fraud in an Audit of Financial Statements')).toBeInTheDocument()
  })

  it('renders official link', () => {
    render(<CitationFooter standards={['ISA 240']} />)
    expect(screen.getByText('IFAC eISA')).toBeInTheDocument()
  })

  it('renders free link when available', () => {
    render(<CitationFooter standards={['ISA 240']} />)
    expect(screen.getByText('IAASB open')).toBeInTheDocument()
  })

  it('does not render free link when not available', () => {
    render(<CitationFooter standards={['PCAOB AS 2401']} />)
    expect(screen.queryByText('IAASB open')).not.toBeInTheDocument()
  })

  it('renders multiple citations', () => {
    render(<CitationFooter standards={['ISA 240', 'PCAOB AS 2401']} />)
    expect(screen.getByText('ISA 240')).toBeInTheDocument()
    expect(screen.getByText('PCAOB AS 2401')).toBeInTheDocument()
  })
})
