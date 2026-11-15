import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'About Paciolus — Trial Balance and Ledger Testing for Audit Teams',
  description: 'Why Paciolus was built, what it is and what it is not. Your uploaded files are processed in memory and not kept after analysis.',
  openGraph: {
    title: 'About Paciolus — Trial Balance and Ledger Testing for Audit Teams',
    description: 'Why Paciolus was built, what it is and what it is not.',
  },
}

export default function AboutLayout({ children }: { children: React.ReactNode }) {
  return children
}
