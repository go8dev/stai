// Browser tests. Both workflows (API Server and web) must be running.
// Run with `pnpm run test:browser`.
import { defineConfig } from '@playwright/test';

// On Replit the browser comes from the system packages, so nothing is downloaded.
const executablePath = process.env.REPLIT_PLAYWRIGHT_CHROMIUM_EXECUTABLE;

export default defineConfig({
  testDir: 'e2e',
  outputDir: 'generated-artifacts/playwright',
  reporter: 'list',
  forbidOnly: true,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  timeout: 30_000,
  use: {
    // The workspace proxy: the web app at `/` and the backend under `/api`.
    baseURL: process.env.STAI_BASE_URL ?? 'http://localhost:80',
    browserName: 'chromium',
    launchOptions: executablePath ? { executablePath } : {},
    trace: 'off',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'desktop', use: { viewport: { width: 1280, height: 800 } } },
    {
      name: 'phone',
      use: { viewport: { width: 390, height: 844 }, hasTouch: true },
    },
  ],
});
