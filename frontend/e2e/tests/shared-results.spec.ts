/**
 * Shared Results page E2E tests.
 *
 * Dev: uses mocked API responses via page.route().
 * Prod: smoke test with a real share token (E2E_PROD_SHARE_TOKEN env var).
 */
import { test, expect } from "@playwright/test";
import { SharedResultsPage } from "../pages/shared.page";
import { mockSharedAnalysis, MOCK_SHARE_TOKEN } from "../fixtures/mock-data";

test.describe("Shared Results — dev (mocked)", () => {
  test.skip(
    ({ }, testInfo) => testInfo.project.name === "prod",
    "Mocked tests only run in dev"
  );

  test("displays analysis data for a valid share token", async ({ page }) => {
    // Intercept the share API
    await page.route("**/api/share/**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockSharedAnalysis()),
        });
      }
      return route.continue();
    });

    const shared = new SharedResultsPage(page);
    await shared.goto(MOCK_SHARE_TOKEN);

    // Should show the analysis content
    await expect(shared.heading).toBeVisible();
    await expect(shared.topDifferencesHeading).toBeVisible();
    await expect(shared.ctaButton).toBeVisible();
    await expect(shared.footer).toBeVisible();
  });

  test("phase selector switches phases", async ({ page }) => {
    await page.route("**/api/share/**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockSharedAnalysis()),
        });
      }
      return route.continue();
    });

    const shared = new SharedResultsPage(page);
    await shared.goto(MOCK_SHARE_TOKEN);

    // Click through phases
    await shared.phaseTop.click();
    await shared.phaseImpact.click();
    await shared.phaseFollowThrough.click();
    await shared.phaseAddress.click();
  });

  test("shows error state for invalid share token", async ({ page }) => {
    await page.route("**/api/share/**", (route) => {
      return route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "This swing analysis has expired or been made private.",
        }),
      });
    });

    const shared = new SharedResultsPage(page);
    await shared.goto("invalid-token-123");

    await expect(shared.errorHeading).toBeVisible();
    await expect(shared.analyzeOwnSwingButton).toBeVisible();
  });

  test("CTA button links to home page", async ({ page }) => {
    await page.route("**/api/share/**", (route) => {
      return route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify(mockSharedAnalysis()),
      });
    });

    const shared = new SharedResultsPage(page);
    await shared.goto(MOCK_SHARE_TOKEN);

    const href = await shared.ctaButton.getAttribute("href");
    expect(href).toBe("/");
  });
});

test.describe("Shared Results — prod (smoke)", () => {
  test.skip(
    ({ }, testInfo) => testInfo.project.name !== "prod",
    "Prod smoke tests only run in prod project"
  );

  const prodShareToken = process.env.E2E_PROD_SHARE_TOKEN;

  test.skip(!prodShareToken, "E2E_PROD_SHARE_TOKEN not set — skipping");

  test("loads shared analysis page", async ({ page }) => {
    const shared = new SharedResultsPage(page);
    await shared.goto(prodShareToken!);

    // Should show either the analysis or an error — not a crash
    const hasContent = await shared.heading
      .isVisible({ timeout: 10_000 })
      .catch(() => false);
    const hasError = await shared.errorHeading
      .isVisible({ timeout: 2_000 })
      .catch(() => false);

    expect(hasContent || hasError).toBe(true);
  });
});
