import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Platform Demo — Explore Paciolus Diagnostic Tools',
  description: 'An interactive demo and an overview of all 18 diagnostic tools. See trial balance analysis, journal entry testing, revenue testing and more — no account required.',
  openGraph: {
    title: 'Platform Demo — Explore Paciolus Diagnostic Tools',
    description: 'An interactive demo and an overview of all 18 diagnostic tools. No account required.',
  },
}

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return children
}
