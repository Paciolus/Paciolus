import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Our Approach — How Paciolus Audit Intelligence Works',
  description: 'Upload your trial balance, map accounts automatically, and receive diagnostic intelligence in seconds. Zero-storage processing with ISA and PCAOB alignment.',
  openGraph: {
    title: 'Our Approach — How Paciolus Audit Intelligence Works',
    description: 'Upload, map, and analyze with zero-storage processing aligned to ISA and PCAOB standards.',
  },
}

export default function ApproachLayout({ children }: { children: React.ReactNode }) {
  return children
}
