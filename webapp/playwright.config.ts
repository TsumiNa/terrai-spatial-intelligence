import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  testMatch: /.*_test\.ts/,
  // Tests only read; nothing shares state, so they can all run at once. Without
  // this only whole files parallelise, which leaves the 14 visual tests serial.
  fullyParallel: true,
  // Playwright drops to a single worker when it detects CI, which made
  // fullyParallel do nothing there. Two is deliberate rather than one per core:
  // these tests render maps through software WebGL, and four workers on the
  // four-core runner starved each other until map-dependent tests timed out.
  // A flaky suite is worse than a slow one when it guards the visual baselines.
  workers: process.env.CI ? 2 : undefined,
  use: { baseURL: "http://127.0.0.1:4300" },
  webServer: [
    {
      // `npm run build` also runs svelte-check over 897 files, which the Web app
      // job already did. Only the bundle is needed to serve the app.
      command: "npx vite build && npm run preview",
      url: "http://127.0.0.1:4300",
      reuseExistingServer: true,
      timeout: 120000,
    },
    {
      command: "uv run python -m terrai_spatial api --no-ensure-data",
      url: "http://127.0.0.1:8000/api/v1/health",
      cwd: "..",
      reuseExistingServer: true,
      timeout: 60000,
    },
  ],
});
