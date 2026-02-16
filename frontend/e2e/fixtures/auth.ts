/**
 * Custom Playwright fixtures for authenticated and unauthenticated pages.
 *
 * Usage in tests:
 *   import { test, expect } from "../fixtures/auth";
 *
 *   test("logged-in user sees upload", async ({ authedPage }) => { ... });
 *   test("visitor sees Get Started", async ({ unauthPage }) => { ... });
 */
import { test as base, Page } from "@playwright/test";
import path from "path";

const AUTH_FILE = path.resolve(__dirname, "../.auth/user.json");

type Fixtures = {
  /** Page with PropelAuth storage state (logged-in user). */
  authedPage: Page;
  /** Page with no auth state (anonymous visitor). */
  unauthPage: Page;
};

export const test = base.extend<Fixtures>({
  authedPage: async ({ browser }, use) => {
    const context = await browser.newContext({
      storageState: AUTH_FILE,
    });
    const page = await context.newPage();
    await use(page);
    await context.close();
  },

  unauthPage: async ({ browser }, use) => {
    const context = await browser.newContext();
    const page = await context.newPage();
    await use(page);
    await context.close();
  },
});

export { expect } from "@playwright/test";
