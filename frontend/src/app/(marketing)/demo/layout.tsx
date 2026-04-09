import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Platform Demo — Explore Paciolus Diagnostic Tools',
  description: 'Interactive demo of all 12 audit diagnostic tools. See trial balance analysis, journal entry testing, revenue testing, and more — no account required.',
  openGraph: {
    title: 'Platform Demo — Explore Paciolus Diagnostic Tools',
    description: 'Interactive demo of all 12 audit diagnostic tools. No account required.',
  },
}

export default function DemoLayout({ children }: { children: React.ReactNode }) {
  return children
}
