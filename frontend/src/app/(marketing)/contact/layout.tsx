import type { Metadata } from 'next'

export const metadata: Metadata = {
  title: 'Contact Paciolus — Get in Touch',
  description: 'Have questions about Paciolus? Request a walkthrough, get support, or inquire about enterprise plans. We aim to reply within 1–2 business days.',
  openGraph: {
    title: 'Contact Paciolus — Get in Touch',
    description: 'Request a walkthrough, get support, or inquire about enterprise plans.',
  },
}

export default function ContactLayout({ children }: { children: React.ReactNode }) {
  return children
}
