import { defineConfig } from "@playwright/test";

export default defineConfig({
  testDir: "./e2e",
  timeout: 60_000,
  expect: { timeout: 10_000 },
  retries: 0,
  globalSetup: "./e2e/global-setup",
  globalTeardown: "./e2e/global-teardown",
  use: {
    baseURL: "http://127.0.0.1:18080",
    trace: "retain-on-failure"
  }
});
