import { redirect } from 'next/navigation'

/**
 * Root page — redirects to Trial Balance Diagnostics tool.
 *
 * Sprint 62: Route scaffolding — tools live at /tools/*
 * Sprint 66: This will become the platform marketing homepage.
 */
export default function Home() {
  redirect('/tools/trial-balance')
}
