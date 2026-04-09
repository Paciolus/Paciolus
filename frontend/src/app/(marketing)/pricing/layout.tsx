import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Pricing — Paciolus Plans for Every Practice Size',
  description: 'Free, Solo, Professional, and Enterprise plans. All paid tiers include all 12 diagnostic tools. Start free, scale as you grow.',
  openGraph: {
    title: 'Pricing — Paciolus Plans for Every Practice Size',
    description: 'Free, Solo, Professional, and Enterprise plans. All paid tiers include all 12 diagnostic tools.',
  },
}

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children
}
