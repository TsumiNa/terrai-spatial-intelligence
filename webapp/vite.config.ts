import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [svelte()],
  server: { host: "127.0.0.1", port: 4300 },
  preview: { host: "127.0.0.1", port: 4300 },
  test: {
    include: ["src/**/*_test.ts"],
    environment: "node",
  },
});
