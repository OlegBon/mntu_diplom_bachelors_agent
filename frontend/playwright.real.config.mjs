import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/e2e",
  testMatch: "real-report-workflow.spec.mjs",
  workers: 1,
  use: { baseURL: process.env.E2E_REAL_BASE_URL || "http://127.0.0.1:3211", headless: true },
});
