// ESLint for the TypeScript in this project. Python is linted by Ruff (see pyproject.toml).
// Run with `pnpm run lint`.
import js from '@eslint/js';
import globals from 'globals';
import reactHooks from 'eslint-plugin-react-hooks';
import tseslint from 'typescript-eslint';

const BROWSER_CODE = [
  'artifacts/stai/src/**/*.{ts,tsx}',
  'lib/api-client-react/src/**/*.{ts,tsx}',
  'lib/replit-auth-web/src/**/*.{ts,tsx}',
];

export default tseslint.config(
  {
    ignores: [
      '**/node_modules/**',
      '**/dist/**',
      '.cache/**',
      '.local/**',
      '.pythonlibs/**',
      'generated-artifacts/**',
      'test-results/**',
      // Directories written by the platform.
      '.agents/**',
      '.config/**',
      '.conversation/**',
      '.upm/**',
      // Read-only source material supplied by the owner.
      'stai_handoff/**',
      // Generated from the API contract by `pnpm --filter @workspace/api-spec run codegen`.
      'lib/api-client-react/src/generated/**',
      'lib/api-zod/src/generated/**',
      // The platform's canvas scaffold is not part of STAI.
      'artifacts/mockup-sandbox/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: BROWSER_CODE,
    languageOptions: { globals: globals.browser },
    plugins: { 'react-hooks': reactHooks },
    rules: reactHooks.configs.recommended.rules,
  },
  {
    // Interface primitives copied in from the shadcn/ui scaffold. They are kept as
    // supplied, so the rules they were not written for are switched off here only.
    files: [
      'artifacts/stai/src/components/ui/**/*.tsx',
      'artifacts/stai/src/hooks/**/*.{ts,tsx}',
    ],
    rules: {
      'react-hooks/purity': 'off',
      'react-hooks/set-state-in-effect': 'off',
      '@typescript-eslint/no-unused-vars': 'off',
    },
  },
  {
    files: ['**/*.config.{ts,mjs}', 'scripts/**/*.ts', 'e2e/**/*.ts'],
    languageOptions: { globals: globals.node },
  },
);
