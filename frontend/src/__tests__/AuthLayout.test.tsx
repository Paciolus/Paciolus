/**
 * Sprint 702: Auth layout pins the wordmark + autofill contract.
 *
 * The autofill CSS lives in globals.css (not imported by the test
 * renderer), so these tests cover what we can verify at render time:
 *   - Wordmark renders and links to /
 *   - Footer "Back to Paciolus" still present (no regression on the
 *     existing footer link)
 *   - Children render
 */
import AuthLayout from '@/app/(auth)/layout'
import { render, screen } from '@/test-utils'

describe('AuthLayout', () => {
  it('renders the wordmark as a link to the homepage', () => {
    render(
      <AuthLayout>
        <div>child-body</div>
      </AuthLayout>,
    )

    const wordmark = screen.getByRole('link', { name: /Paciolus — go to homepage/i })
    expect(wordmark).toBeInTheDocument()
    expect(wordmark).toHaveAttribute('href', '/')
    expect(wordmark.textContent).toBe('Paciolus')
  })

  it('renders the footer Back-to-Paciolus link unchanged', () => {
    render(
      <AuthLayout>
        <div>child-body</div>
      </AuthLayout>,
    )

    const footer = screen.getByRole('link', { name: /Back to Paciolus/i })
    expect(footer).toBeInTheDocument()
    expect(footer).toHaveAttribute('href', '/')
  })

  it('renders children inside the card slot', () => {
    render(
      <AuthLayout>
        <section data-testid="auth-body">child-body</section>
      </AuthLayout>,
    )

    expect(screen.getByTestId('auth-body')).toHaveTextContent('child-body')
  })
})
