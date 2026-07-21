import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  testMatch: /.*_test\.ts/,
  use: { baseURL: "http://127.0.0.1:4300" },
  webServer: {
    command: "npm run build && npm run preview",
    url: "http://127.0.0.1:4300",
    reuseExistingServer: true,
  },
});
