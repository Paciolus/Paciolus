import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Privacy Policy — Paciolus',
  description: 'Privacy Policy for Paciolus: what we collect, what we keep, and your rights. Uploaded files are processed in memory and not kept after analysis.',
  openGraph: {
    title: 'Privacy Policy — Paciolus',
    description: 'What we collect, what we keep, and your rights.',
  },
}

export default function PrivacyLayout({ children }: { children: React.ReactNode }) {
  return children
}
