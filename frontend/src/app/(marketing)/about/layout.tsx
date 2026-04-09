import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About Paciolus — The Story Behind Zero-Storage Audit Intelligence',
  description: 'Built on the legacy of Luca Pacioli, Paciolus brings surgical precision to trial balance diagnostics. Learn how we protect your data with zero-storage architecture.',
  openGraph: {
    title: 'About Paciolus — The Story Behind Zero-Storage Audit Intelligence',
    description: 'Built on the legacy of Luca Pacioli, Paciolus brings surgical precision to trial balance diagnostics.',
  },
}

export default function AboutLayout({ children }: { children: React.ReactNode }) {
  return children
}
