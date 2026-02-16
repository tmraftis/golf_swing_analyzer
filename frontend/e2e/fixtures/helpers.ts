import { type Page, type Locator } from "@playwright/test";

/**
 * Navigate to a URL with retry on Next.js Turbopack ChunkLoadError.
 *
 * The Next.js dev server occasionally fails to serve chunks on first load.
 * This helper retries up to `maxRetries` times with a page reload if the
 * expected content doesn't appear within the initial timeout.
 */
export async function gotoWithRetry(
  page: Page,
  url: string,
  waitFor: Locator,
  timeout = 10_000,
  maxRetries = 2
) {
  await page.goto(url);
  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    try {
      await waitFor.waitFor({ timeout });
      return; // success
    } catch {
      if (attempt === maxRetries) throw new Error(
        `Page content not visible after ${maxRetries + 1} attempts at ${url}`
      );
      // Dismiss Next.js error overlay if present, then reload
      await page.keyboard.press("Escape").catch(() => {});
      await page.waitForTimeout(500);
      await page.reload();
    }
  }
}
