import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Our Approach — How Paciolus Works',
  description: 'What happens to a file you upload, and exactly what Paciolus keeps. Your uploaded files are processed in memory and not kept after analysis.',
  openGraph: {
    title: 'Our Approach — How Paciolus Works',
    description: 'What happens to a file you upload, and exactly what Paciolus keeps.',
  },
}

export default function ApproachLayout({ children }: { children: React.ReactNode }) {
  return children
}
