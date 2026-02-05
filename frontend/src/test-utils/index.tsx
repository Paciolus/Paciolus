/**
 * Test Utilities for Paciolus Frontend
 * Sprint 55: Frontend Test Foundation
 *
 * Provides common test utilities, custom render functions,
 * and fixtures for consistent testing patterns.
 */

import React, { ReactElement } from 'react'
import { render, RenderOptions } from '@testing-library/react'
import userEvent from '@testing-library/user-event'

/**
 * Custom render function that wraps components with necessary providers.
 * Extend this as needed when adding context providers (auth, theme, etc.)
 */
interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  // Add provider-specific options here as needed
}

function AllTheProviders({ children }: { children: React.ReactNode }) {
  // Add providers here as the app grows (AuthContext, ThemeContext, etc.)
  return <>{children}</>
}

/**
 * Custom render that includes all providers
 */
function customRender(
  ui: ReactElement,
  options?: CustomRenderOptions
) {
  return {
    user: userEvent.setup(),
    ...render(ui, { wrapper: AllTheProviders, ...options }),
  }
}

// Re-export everything from testing-library
export * from '@testing-library/react'

// Override render with custom render
export { customRender as render }

// Export userEvent for convenience
export { userEvent }
