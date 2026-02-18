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
import fs from "fs";

const AUTH_FILE = path.resolve(__dirname, "../.auth/user.json");

/** Check if auth storage state has real credentials (not empty). */
function hasAuthCredentials(): boolean {
  try {
    const data = JSON.parse(fs.readFileSync(AUTH_FILE, "utf-8"));
    return data.cookies && data.cookies.length > 0;
  } catch {
    return false;
  }
}

type Fixtures = {
  /** Page with PropelAuth storage state (logged-in user). */
  authedPage: Page;
  /** Page with no auth state (anonymous visitor). */
  unauthPage: Page;
};

export const test = base.extend<Fixtures>({
  authedPage: async ({ browser }, use, testInfo) => {
    if (!hasAuthCredentials()) {
      testInfo.skip(true, "No auth credentials — set E2E_TEST_EMAIL and E2E_TEST_PASSWORD");
      return;
    }
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
