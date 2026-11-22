import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: 'e2e',
  workers: 1,
  timeout: 15_000,                 // a missing selector must fail fast, not hold a 3.8 GB VM for 30 s per test
  expect: { timeout: 5_000 },
  reporter: 'line',
  use: { viewport: { width: 1280, height: 800 }, baseURL: 'http://localhost:5173' },
  webServer: { command: 'npx vite --port 5173 --strictPort', url: 'http://localhost:5173', reuseExistingServer: false },
});
