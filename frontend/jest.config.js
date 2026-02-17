/**
 * Jest Configuration for Paciolus Frontend
 * Sprint 55: Frontend Test Foundation
 *
 * Configured for Next.js 16 with TypeScript, React Testing Library,
 * and CSS modules support.
 */

const nextJest = require('next/jest')

const createJestConfig = nextJest({
  // Provide the path to your Next.js app to load next.config.js and .env files
  dir: './',
})

/** @type {import('jest').Config} */
const customJestConfig = {
  // Test environment
  testEnvironment: 'jsdom',

  // Setup files
  setupFilesAfterEnv: ['<rootDir>/jest.setup.js'],

  // Module name mapping for path aliases and CSS modules
  moduleNameMapper: {
    // Handle module aliases (matching tsconfig paths)
    '^@/(.*)$': '<rootDir>/src/$1',

    // Handle CSS imports (with CSS modules)
    '^.+\\.module\\.(css|sass|scss)$': 'identity-obj-proxy',

    // Handle CSS imports (without CSS modules)
    '^.+\\.(css|sass|scss)$': '<rootDir>/__mocks__/styleMock.js',

    // Handle image imports
    '^.+\\.(png|jpg|jpeg|gif|webp|avif|ico|bmp|svg)$': '<rootDir>/__mocks__/fileMock.js',
  },

  // Test file patterns
  testMatch: [
    '**/__tests__/**/*.[jt]s?(x)',
    '**/?(*.)+(spec|test).[jt]s?(x)',
  ],

  // Ignore patterns
  testPathIgnorePatterns: [
    '<rootDir>/node_modules/',
    '<rootDir>/.next/',
  ],

  // Module path ignore patterns (fixes haste module collision)
  modulePathIgnorePatterns: [
    '<rootDir>/.next/',
  ],

  // Transform ignore patterns
  transformIgnorePatterns: [
    '/node_modules/',
    '^.+\\.module\\.(css|sass|scss)$',
  ],

  // Coverage configuration
  collectCoverageFrom: [
    'src/**/*.{js,jsx,ts,tsx}',
    '!src/**/*.d.ts',
    '!src/**/*.stories.{js,jsx,ts,tsx}',
    '!src/**/index.{js,ts}',
  ],

  // Coverage thresholds (Sprint 276: raised from 10% to 20%)
  coverageThreshold: {
    global: {
      branches: 20,
      functions: 20,
      lines: 20,
      statements: 20,
    },
  },

  // Verbose output
  verbose: true,
}

// createJestConfig returns an async function that returns the config
module.exports = createJestConfig(customJestConfig)
