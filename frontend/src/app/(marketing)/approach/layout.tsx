import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Our Approach — How Paciolus Works',
  description: 'Upload your trial balance, map accounts automatically, and receive diagnostic intelligence in seconds. Uploaded files are processed in memory and not kept, with references to the standards each test draws on.',
  openGraph: {
    title: 'Our Approach — How Paciolus Works',
    description: 'Upload, map and analyze, with references to the standards each test draws on.',
  },
}

export default function ApproachLayout({ children }: { children: React.ReactNode }) {
  return children
}
