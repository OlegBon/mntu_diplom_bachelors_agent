import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  testIgnore: "real-report-workflow.spec.mjs",
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:3000",
    headless: true,
  },
  webServer: {
    command: "npm start -- --no-open",
    url: "http://127.0.0.1:3000",
    reuseExistingServer: !process.env.CI,
  },
});
