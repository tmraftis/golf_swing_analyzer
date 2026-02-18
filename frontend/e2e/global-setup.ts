/**
 * Global setup: Log into PropelAuth once and save storage state.
 *
 * Requires environment variables:
 *   E2E_TEST_EMAIL    — test account email
 *   E2E_TEST_PASSWORD — test account password
 *
 * The storage state (cookies + localStorage) is written to
 * e2e/.auth/user.json and reused by all tests.
 */
import { chromium, FullConfig } from "@playwright/test";
import path from "path";

const AUTH_FILE = path.resolve(__dirname, ".auth/user.json");

export default async function globalSetup(config: FullConfig) {
  const email = process.env.E2E_TEST_EMAIL;
  const password = process.env.E2E_TEST_PASSWORD;

  if (!email || !password) {
    console.warn(
      "\n⚠️  E2E_TEST_EMAIL / E2E_TEST_PASSWORD not set — skipping auth setup.\n" +
        "   Tests requiring auth will be skipped.\n"
    );
    // Write an empty storage state so Playwright doesn't error
    const fs = await import("fs/promises");
    await fs.mkdir(path.dirname(AUTH_FILE), { recursive: true });
    await fs.writeFile(
      AUTH_FILE,
      JSON.stringify({ cookies: [], origins: [] })
    );
    return;
  }

  // Use the first project's baseURL
  const baseURL =
    config.projects[0]?.use?.baseURL || "http://localhost:3000";

  const browser = await chromium.launch();
  const context = await browser.newContext();
  const page = await context.newPage();

  try {
    // Navigate to the PropelAuth login page
    await page.goto(`${baseURL}/api/auth/login`);

    // PropelAuth hosted login — fill email + password
    await page.waitForSelector('input[type="email"], input[name="email"]', {
      timeout: 15_000,
    });
    await page.fill('input[type="email"], input[name="email"]', email);

    // Some PropelAuth flows have a "Continue" step before the password field
    const continueBtn = page.locator(
      'button:has-text("Continue"), button[type="submit"]'
    );
    if (await continueBtn.isVisible({ timeout: 2_000 }).catch(() => false)) {
      await continueBtn.first().click();
    }

    await page.waitForSelector(
      'input[type="password"], input[name="password"]',
      { timeout: 10_000 }
    );
    await page.fill('input[type="password"], input[name="password"]', password);

    // Submit login form
    const loginBtn = page.locator(
      'button:has-text("Log In"), button:has-text("Sign In"), button[type="submit"]'
    );
    await loginBtn.first().click();

    // Wait for redirect back to the app
    await page.waitForURL(`${baseURL}/**`, { timeout: 30_000 });

    console.log("✅ PropelAuth login succeeded — saving storage state");
  } catch (err) {
    console.error("❌ PropelAuth login failed:", err);
    throw err;
  }

  // Save authenticated state
  await context.storageState({ path: AUTH_FILE });
  await browser.close();
}
