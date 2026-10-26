import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About Paciolus — Diagnostic Intelligence for Financial Professionals',
  description: 'Built on the legacy of Luca Pacioli, Paciolus brings surgical precision to trial balance diagnostics. Uploaded files are processed in memory and not kept after analysis.',
  openGraph: {
    title: 'About Paciolus — Diagnostic Intelligence for Financial Professionals',
    description: 'Built on the legacy of Luca Pacioli, Paciolus brings surgical precision to trial balance diagnostics.',
  },
}

export default function AboutLayout({ children }: { children: React.ReactNode }) {
  return children
}
