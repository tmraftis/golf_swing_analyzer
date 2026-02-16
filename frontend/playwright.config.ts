import { defineConfig, devices } from "@playwright/test";
import path from "path";

const isCI = !!process.env.CI;

/**
 * Playwright configuration for Pure E2E tests.
 *
 * Two projects:
 *   - dev:  full suite against localhost:3000 (auto-starts dev server)
 *   - prod: smoke tests only against swingpure.ai
 */
export default defineConfig({
  testDir: "./e2e/tests",

  /* Sequential execution — auth state is shared, upload tests must not overlap */
  fullyParallel: false,
  workers: 1,

  /* Fail CI if test.only is left in source */
  forbidOnly: isCI,

  /* Retry once on CI */
  retries: isCI ? 1 : 0,

  /* HTML reporter + console list */
  reporter: [["html", { open: "never" }], ["list"]],

  /* Shared settings */
  use: {
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },

  /* Global setup — logs into PropelAuth and saves storage state */
  globalSetup: path.resolve(__dirname, "e2e/global-setup.ts"),

  projects: [
    {
      name: "dev",
      use: {
        ...devices["Desktop Chrome"],
        baseURL: "http://localhost:3000",
        storageState: path.resolve(__dirname, "e2e/.auth/user.json"),
      },
    },
    {
      name: "prod",
      use: {
        ...devices["Desktop Chrome"],
        baseURL: "https://swingpure.ai",
        storageState: path.resolve(__dirname, "e2e/.auth/user.json"),
      },
    },
  ],

  /* Auto-start dev server for the dev project */
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 30_000,
  },
});
