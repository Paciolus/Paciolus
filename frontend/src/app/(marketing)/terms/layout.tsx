import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Terms of Service — Paciolus',
  description: 'Terms of Service for Paciolus, the zero-storage trial balance diagnostic platform for financial professionals.',
  openGraph: {
    title: 'Terms of Service — Paciolus',
    description: 'Terms of Service for Paciolus, the zero-storage trial balance diagnostic platform.',
  },
}

export default function TermsLayout({ children }: { children: React.ReactNode }) {
  return children
}
