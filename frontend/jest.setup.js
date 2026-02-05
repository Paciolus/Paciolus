/**
 * Jest Setup File
 * Sprint 55: Frontend Test Foundation
 *
 * This file runs before each test file.
 */

// Extend Jest matchers with React Testing Library
import '@testing-library/jest-dom'

// Mock window.matchMedia (required for some components)
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: jest.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: jest.fn(), // Deprecated
    removeListener: jest.fn(), // Deprecated
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    dispatchEvent: jest.fn(),
  })),
})

// Mock ResizeObserver (required for some components)
global.ResizeObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock IntersectionObserver (required for lazy loading)
global.IntersectionObserver = jest.fn().mockImplementation(() => ({
  observe: jest.fn(),
  unobserve: jest.fn(),
  disconnect: jest.fn(),
}))

// Mock window.URL.createObjectURL (for file downloads)
window.URL.createObjectURL = jest.fn(() => 'mock-url')
window.URL.revokeObjectURL = jest.fn()

// Mock window.scrollTo (not implemented in jsdom)
window.scrollTo = jest.fn()

// Mock window.getComputedStyle for framer-motion
const originalGetComputedStyle = window.getComputedStyle
window.getComputedStyle = (element, pseudoElt) => {
  const style = originalGetComputedStyle(element, pseudoElt)
  return {
    ...style,
    getPropertyValue: (prop) => style.getPropertyValue(prop) || '',
  }
}

// Suppress console errors during tests (optional, comment out for debugging)
// const originalError = console.error
// beforeAll(() => {
//   console.error = (...args) => {
//     if (
//       typeof args[0] === 'string' &&
//       args[0].includes('Warning: ReactDOM.render is no longer supported')
//     ) {
//       return
//     }
//     originalError.call(console, ...args)
//   }
// })
// afterAll(() => {
//   console.error = originalError
// })

// Set up environment variables for tests
process.env.NEXT_PUBLIC_API_URL = 'http://localhost:8000'
