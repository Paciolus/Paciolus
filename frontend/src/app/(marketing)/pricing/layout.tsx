import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Pricing — Paciolus',
  description: 'Free, Solo, Professional, and Enterprise plans. All paid tiers include all 18 diagnostic tools.',
  openGraph: {
    title: 'Pricing — Paciolus',
    description: 'Free, Solo, Professional, and Enterprise plans. All paid tiers include all 18 diagnostic tools.',
  },
}

export default function PricingLayout({ children }: { children: React.ReactNode }) {
  return children
}
