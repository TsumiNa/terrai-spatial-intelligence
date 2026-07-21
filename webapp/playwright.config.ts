import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  testMatch: /.*_test\.ts/,
  use: { baseURL: "http://127.0.0.1:4300" },
  webServer: [
    {
      command: "npm run build && npm run preview",
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
