import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service — Paciolus',
  description: 'Terms of Service for Paciolus, diagnostic software for financial professionals.',
  openGraph: {
    title: 'Terms of Service — Paciolus',
    description: 'Terms of Service for Paciolus, diagnostic software for financial professionals.',
  },
}

export default function TermsLayout({ children }: { children: React.ReactNode }) {
  return children
}
