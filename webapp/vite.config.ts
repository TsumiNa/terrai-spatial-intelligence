import tailwindcss from "@tailwindcss/vite";
import { svelte } from "@sveltejs/vite-plugin-svelte";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [tailwindcss(), svelte()],
  // Dev and preview deliberately sit on different ports: e2e targets the
  // preview port, and a forgotten dev server must never be a valid-looking
  // stand-in for the freshly built bundle.
  server: { host: "127.0.0.1", port: 4310 },
  preview: { host: "127.0.0.1", port: 4300 },
  test: {
    include: ["src/**/*_test.ts"],
    environment: "node",
  },
});
