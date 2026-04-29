import tsPlugin from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import importPlugin from 'eslint-plugin-import';
import jsxA11y from 'eslint-plugin-jsx-a11y';
import reactHooks from 'eslint-plugin-react-hooks';

/**
 * Paciolus ESLint Configuration
 * Phase 3 Refactor: Import ordering enforcement
 *
 * Import order:
 * 1. React imports
 * 2. Next.js imports
 * 3. External libraries (framer-motion, etc.)
 * 4. @/app/* imports (page/layout imports in tests)
 * 5. @/contexts/* imports
 * 6. @/components/* imports
 * 7. @/hooks/* imports
 * 8. @/types/* imports (type imports)
 * 9. @/utils/*, @/lib/*, @/data/* imports
 * 10. @/test-utils (test utilities, last)
 */
const eslintConfig = [
  {
    files: ['**/*.ts', '**/*.tsx'],
    languageOptions: {
      parser: tsParser,
      parserOptions: {
        ecmaVersion: 'latest',
        sourceType: 'module',
        ecmaFeatures: {
          jsx: true,
        },
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
      import: importPlugin,
      'jsx-a11y': jsxA11y,
      'react-hooks': reactHooks,
    },
    rules: {
      // React hooks
      'react-hooks/rules-of-hooks': 'error',
      'react-hooks/exhaustive-deps': 'warn',

      // XSS sink governance — ban patterns that expose the app to injection
      'no-eval': 'error',
      'no-implied-eval': 'error',
      'no-restricted-properties': [
        'error',
        {
          object: 'document',
          property: 'write',
          message: 'document.write is an XSS sink. Use DOM APIs instead.',
        },
      ],
      'no-restricted-syntax': [
        'error',
        {
          selector: 'JSXAttribute[name.name="dangerouslySetInnerHTML"]',
          message: 'dangerouslySetInnerHTML bypasses React XSS protections. Use safe alternatives or get security review.',
        },
        {
          selector: 'AssignmentExpression[left.property.name="innerHTML"]',
          message: 'Direct innerHTML assignment is an XSS sink. Use textContent or DOM APIs.',
        },
        {
          // Sprint 744: ban direct fetch() outside the canonical transport allowlist.
          // Use apiClient (apiGet/apiPost/apiPut/apiDelete), apiDownload, or uploadFetch.
          // Allowlist: utils/transport.ts, utils/authMiddleware.ts, utils/downloadAdapter.ts,
          // utils/uploadTransport.ts, contexts/AuthSessionContext.tsx, app/shared/[token]/page.tsx.
          selector: 'CallExpression[callee.type="Identifier"][callee.name="fetch"]',
          message: 'Direct fetch() is banned. Use apiClient (apiGet/apiPost/etc.), apiDownload, or uploadFetch from @/utils/apiClient. Low-level transport modules are allowlisted via per-file override.',
        },
      ],

      // Accessibility
      ...jsxA11y.configs.recommended.rules,
      'jsx-a11y/label-has-associated-control': ['error', { assert: 'either', depth: 3 }],

      // Import ordering
      'import/order': [
        'error',
        {
          groups: [
            'builtin',
            'external',
            'internal',
            ['parent', 'sibling'],
            'index',
            'type',
          ],
          pathGroups: [
            {
              pattern: 'react',
              group: 'builtin',
              position: 'before',
            },
            {
              pattern: 'react-dom',
              group: 'builtin',
              position: 'before',
            },
            {
              pattern: 'next',
              group: 'builtin',
              position: 'after',
            },
            {
              pattern: 'next/**',
              group: 'builtin',
              position: 'after',
            },
            {
              pattern: '@/app/**',
              group: 'internal',
              position: 'before',
            },
            {
              pattern: '@/contexts/**',
              group: 'internal',
              position: 'before',
            },
            {
              pattern: '@/contexts',
              group: 'internal',
              position: 'before',
            },
            {
              pattern: '@/components/**',
              group: 'internal',
              position: 'before',
            },
            {
              pattern: '@/hooks/**',
              group: 'internal',
              position: 'before',
            },
            {
              pattern: '@/hooks',
              group: 'internal',
              position: 'before',
            },
            {
              pattern: '@/types/**',
              group: 'internal',
              position: 'after',
            },
            {
              pattern: '@/utils/**',
              group: 'internal',
              position: 'after',
            },
            {
              pattern: '@/utils',
              group: 'internal',
              position: 'after',
            },
            {
              pattern: '@/lib/**',
              group: 'internal',
              position: 'after',
            },
            {
              pattern: '@/data/**',
              group: 'internal',
              position: 'after',
            },
            {
              pattern: '@/test-utils',
              group: 'internal',
              position: 'after',
            },
          ],
          pathGroupsExcludedImportTypes: ['react', 'react-dom'],
          'newlines-between': 'never',
          alphabetize: {
            order: 'asc',
            caseInsensitive: true,
          },
        },
      ],

      // Require newline after imports
      'import/newline-after-import': ['error', { count: 1 }],

      // No duplicate imports
      'import/no-duplicates': 'error',
    },
    settings: {
      'import/resolver': {
        typescript: {
          alwaysTryTypes: true,
        },
      },
    },
  },
  {
    // Sprint 744: allowlist for direct fetch() — low-level transport / auth / public share modules.
    files: [
      'src/utils/transport.ts',
      'src/utils/authMiddleware.ts',
      'src/utils/downloadAdapter.ts',
      'src/utils/uploadTransport.ts',
      'src/contexts/AuthSessionContext.tsx',
      // Literal `[token]` in path — escape brackets for minimatch.
      'src/app/shared/\\[token\\]/page.tsx',
    ],
    rules: {
      'no-restricted-syntax': [
        'error',
        // Preserve XSS-sink rules; only the fetch() ban is relaxed for these files.
        {
          selector: 'JSXAttribute[name.name="dangerouslySetInnerHTML"]',
          message: 'dangerouslySetInnerHTML bypasses React XSS protections. Use safe alternatives or get security review.',
        },
        {
          selector: 'AssignmentExpression[left.property.name="innerHTML"]',
          message: 'Direct innerHTML assignment is an XSS sink. Use textContent or DOM APIs.',
        },
      ],
    },
  },
  {
    // Ignore node_modules and build output
    ignores: ['node_modules/**', '.next/**', 'out/**', 'coverage/**'],
  },
];

export default eslintConfig;
