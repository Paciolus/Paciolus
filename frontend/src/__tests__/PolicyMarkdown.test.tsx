/**
 * PolicyMarkdown (Sprint 862) — the renderer for the published compliance documents.
 */
import { PolicyMarkdown, parseBlocks } from '@/components/policy/PolicyMarkdown'
import { DATA_HANDLING_ARCHITECTURE_MD, SECURITY_POLICY_MD, SUBPROCESSOR_LIST_MD } from '@/content/policies.generated'
import { render, screen } from '@/test-utils'

jest.mock('next/link', () => ({
  __esModule: true,
  default: ({ children, href, ...rest }: any) => <a href={href} {...rest}>{children}</a>,
}))

describe('parseBlocks', () => {
  it('parses headings, paragraphs, lists and tables', () => {
    const blocks = parseBlocks('# Title\n\nOne\nline.\n\n- a\n- b\n\n1. first\n   continued\n2. second\n\n| H1 | H2 |\n|---|---|\n| x | y |\n')
    expect(blocks.map(b => b.kind)).toEqual(['heading', 'paragraph', 'list', 'list', 'table'])
    expect(blocks[1]).toEqual({ kind: 'paragraph', text: 'One line.' })
    expect(blocks[3]).toEqual({ kind: 'list', ordered: true, items: ['first continued', 'second'] })
    expect(blocks[4]).toEqual({ kind: 'table', header: ['H1', 'H2'], rows: [['x', 'y']] })
  })
})

describe('PolicyMarkdown', () => {
  it('links a published document to its site page', () => {
    render(<PolicyMarkdown markdown="See the [Security Policy](SECURITY_POLICY.md)." />)
    expect(screen.getByRole('link', { name: 'Security Policy' })).toHaveAttribute('href', '/security')
  })

  it('renders a link to an unpublished document as plain text, not a dead link', () => {
    render(<PolicyMarkdown markdown="See the [Incident Response Plan](INCIDENT_RESPONSE_PLAN.md)." />)
    expect(screen.getByText('Incident Response Plan')).toBeInTheDocument()
    expect(screen.queryByRole('link')).not.toBeInTheDocument()
  })

  it('renders bold, italics and code', () => {
    render(<PolicyMarkdown markdown="**Bold** and *italic* and `code`." />)
    expect(screen.getByText('Bold').tagName).toBe('STRONG')
    expect(screen.getByText('italic').tagName).toBe('EM')
    expect(screen.getByText('code').tagName).toBe('CODE')
  })

  it.each([
    ['Security Policy', SECURITY_POLICY_MD],
    ['Subprocessor List', SUBPROCESSOR_LIST_MD],
    ['Data Handling Architecture', DATA_HANDLING_ARCHITECTURE_MD],
  ])('renders the %s with its title and no raw markdown', (title, markdown) => {
    const { container } = render(<PolicyMarkdown markdown={markdown} />)
    expect(screen.getByRole('heading', { level: 1, name: title })).toBeInTheDocument()
    expect(container.textContent).not.toMatch(/\*\*|\]\(/)
  })
})
