import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  testMatch: /.*_test\.ts/,
  // Tests only read; nothing shares state, so they can all run at once. Without
  // this only whole files parallelise, which leaves the 14 visual tests serial.
  fullyParallel: true,
  // `workers` is deliberately left at Playwright's defaults, which means one
  // worker on CI. Overriding it was measured and rejected: these tests render
  // maps through software WebGL, so they are CPU-bound rather than
  // concurrency-bound. Four workers on the four-core runner starved each other
  // until map-dependent tests timed out, and two bought 12s. That is a poor
  // trade for the suite that guards the visual baselines. Locally, where cores
  // are spare, fullyParallel alone takes the suite from about 93s to 27s.
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
