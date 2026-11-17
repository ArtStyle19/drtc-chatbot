import { defineConfig, devices } from '@playwright/test';

const isCI = Boolean(process.env['CI']);

/**
 * End-to-end tests. By default the API is mocked (fixtures in e2e/fixtures), so the suite only
 * needs the Angular dev server. Set E2E_REAL_API=1 to run against a running backend instead.
 */
export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: isCI,
  retries: isCI ? 2 : 0,
  reporter: isCI ? [['github'], ['html', { open: 'never' }]] : 'list',
  use: {
    baseURL: 'http://localhost:4200',
    locale: 'es-PE',
    trace: 'on-first-retry',
  },
  projects: [{ name: 'chromium', use: { ...devices['Desktop Chrome'] } }],
  webServer: {
    command: 'npm run start -- --port 4200',
    url: 'http://localhost:4200',
    reuseExistingServer: !isCI,
    timeout: 180_000,
  },
});
