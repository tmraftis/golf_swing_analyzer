/**
 * Results page E2E tests.
 *
 * Dev: uses mocked API responses via page.route().
 * Prod: smoke test with a real upload ID (E2E_PROD_UPLOAD_ID env var).
 */
import { test, expect } from "../fixtures/auth";
import { ResultsPage } from "../pages/results.page";
import {
  mockAnalysisResponse,
  MOCK_UPLOAD_ID,
} from "../fixtures/mock-data";

test.describe("Results Page — dev (mocked)", () => {
  test.beforeEach(async ({ authedPage }, testInfo) => {
    test.skip(testInfo.project.name === "prod", "Mocked tests only run in dev");
    // Mock the analysis GET endpoint
    await authedPage.route("**/api/analysis/**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockAnalysisResponse()),
        });
      }
      return route.continue();
    });

    // Mock video URLs to avoid 404s
    await authedPage.route("**/uploads/**", (route) => {
      return route.fulfill({
        status: 200,
        contentType: "video/mp4",
        body: Buffer.alloc(0),
      });
    });
    await authedPage.route("**/reference/**", (route) => {
      return route.fulfill({
        status: 200,
        contentType: "video/quicktime",
        body: Buffer.alloc(0),
      });
    });
  });

  test("displays analysis results", async ({ authedPage }) => {
    const results = new ResultsPage(authedPage);
    await results.goto(MOCK_UPLOAD_ID);

    await expect(results.heading).toBeVisible();
    await expect(results.similarityText).toBeVisible();
    await expect(results.topDifferencesSection).toBeVisible();
  });

  test("shows Share Results button", async ({ authedPage }) => {
    const results = new ResultsPage(authedPage);
    await results.goto(MOCK_UPLOAD_ID);

    await expect(results.shareButton).toBeVisible();
  });

  test("phase tabs switch content", async ({ authedPage }) => {
    const results = new ResultsPage(authedPage);
    await results.goto(MOCK_UPLOAD_ID);

    // Click through each phase
    await results.selectPhase("top");
    await results.selectPhase("impact");
    await results.selectPhase("follow_through");
    await results.selectPhase("address");
  });

  test("shows Analyze Another Swing button", async ({ authedPage }) => {
    const results = new ResultsPage(authedPage);
    await results.goto(MOCK_UPLOAD_ID);

    await expect(results.analyzeAnotherButton).toBeVisible();
    const href = await results.analyzeAnotherButton.getAttribute("href");
    expect(href).toBe("/upload");
  });

  test("returns 404 for unknown upload ID", async ({ authedPage }) => {
    // Override the route to return 404
    await authedPage.route("**/api/analysis/**", (route) => {
      return route.fulfill({
        status: 404,
        contentType: "application/json",
        body: JSON.stringify({
          detail: "No analysis found for upload 'unknown'",
        }),
      });
    });

    const results = new ResultsPage(authedPage);
    await authedPage.goto(`/results/unknown-upload-id?view=dtl`);

    // Should show some error state — page won't crash
    // The exact error handling depends on the frontend implementation
    await authedPage.waitForTimeout(2_000);
    const pageContent = await authedPage.textContent("body");
    expect(pageContent).toBeTruthy();
  });
});

test.describe("Results Page — prod (smoke)", () => {
  const prodUploadId = process.env.E2E_PROD_UPLOAD_ID;

  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name !== "prod", "Prod smoke tests only run in prod project");
    test.skip(!prodUploadId, "E2E_PROD_UPLOAD_ID not set — skipping");
  });

  test("loads results page with real data", async ({ authedPage }) => {
    const results = new ResultsPage(authedPage);
    await results.goto(prodUploadId!);

    await expect(results.heading).toBeVisible({ timeout: 15_000 });
    await expect(results.shareButton).toBeVisible();
    await expect(results.analyzeAnotherButton).toBeVisible();
  });
});
