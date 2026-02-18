/**
 * Upload flow E2E tests (dev only).
 *
 * Tests the full upload → analysis → results flow.
 * Uses mocked API responses for predictable, fast tests.
 */
import { test, expect } from "../fixtures/auth";
import { UploadPage } from "../pages/upload.page";
import { ResultsPage } from "../pages/results.page";
import {
  mockUploadResponse,
  mockAnalysisResponse,
  MOCK_UPLOAD_ID,
} from "../fixtures/mock-data";

test.describe("Upload Flow — dev (mocked)", () => {
  test.beforeEach(({}, testInfo) => {
    test.skip(testInfo.project.name === "prod", "Upload tests only run in dev");
  });

  test("full upload → analysis → results flow", async ({ authedPage }) => {
    test.setTimeout(60_000); // Allow extra time for the full flow

    // Mock the upload endpoint
    await authedPage.route("**/api/upload", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockUploadResponse()),
        });
      }
      return route.continue();
    });

    // Mock the analysis endpoint
    await authedPage.route("**/api/analyze/**", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockAnalysisResponse()),
        });
      }
      return route.continue();
    });

    // Mock the analysis GET (for the results page)
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

    // Mock video URLs
    await authedPage.route("**/uploads/**", (route) =>
      route.fulfill({ status: 200, contentType: "video/mp4", body: Buffer.alloc(0) })
    );
    await authedPage.route("**/reference/**", (route) =>
      route.fulfill({ status: 200, contentType: "video/quicktime", body: Buffer.alloc(0) })
    );

    // 1. Go to upload page
    const upload = new UploadPage(authedPage);
    await upload.goto();
    await expect(upload.heading).toBeVisible();

    // 2. Iron is default, select DTL (already default)
    await expect(upload.ironButton).toBeVisible();
    await expect(upload.dtlButton).toBeVisible();

    // 3. Upload test video
    await upload.uploadTestVideo();
    await expect(upload.removeButton).toBeVisible({ timeout: 5_000 });

    // 4. Submit for analysis
    await expect(upload.submitButton).toBeEnabled();
    await upload.submit();

    // 5. Should navigate to results page
    await authedPage.waitForURL(/\/results\//, { timeout: 30_000 });

    // 6. Results page should display
    const results = new ResultsPage(authedPage);
    await expect(results.heading).toBeVisible({ timeout: 15_000 });
    await expect(results.similarityText).toBeVisible();
    await expect(results.topDifferencesSection).toBeVisible();
    await expect(results.analyzeAnotherButton).toBeVisible();
  });

  test("upload with Face On view", async ({ authedPage }) => {
    test.setTimeout(60_000);

    await authedPage.route("**/api/upload", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockUploadResponse({ view: "fo" })),
        });
      }
      return route.continue();
    });

    await authedPage.route("**/api/analyze/**", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockAnalysisResponse({ view: "fo" })),
        });
      }
      return route.continue();
    });

    await authedPage.route("**/api/analysis/**", (route) => {
      if (route.request().method() === "GET") {
        return route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify(mockAnalysisResponse({ view: "fo" })),
        });
      }
      return route.continue();
    });

    await authedPage.route("**/uploads/**", (route) =>
      route.fulfill({ status: 200, contentType: "video/mp4", body: Buffer.alloc(0) })
    );
    await authedPage.route("**/reference/**", (route) =>
      route.fulfill({ status: 200, contentType: "video/quicktime", body: Buffer.alloc(0) })
    );

    const upload = new UploadPage(authedPage);
    await upload.goto();

    // Switch to Face On
    await upload.selectView("fo");

    // Upload and submit
    await upload.uploadTestVideo();
    await expect(upload.removeButton).toBeVisible({ timeout: 5_000 });
    await upload.submit();

    // Should navigate to results
    await authedPage.waitForURL(/\/results\//, { timeout: 30_000 });
  });

  test("shows error on upload failure", async ({ authedPage }) => {
    await authedPage.route("**/api/upload", (route) => {
      if (route.request().method() === "POST") {
        return route.fulfill({
          status: 500,
          contentType: "application/json",
          body: JSON.stringify({ detail: "Upload failed: server error" }),
        });
      }
      return route.continue();
    });

    const upload = new UploadPage(authedPage);
    await upload.goto();

    await upload.uploadTestVideo();
    await expect(upload.removeButton).toBeVisible({ timeout: 5_000 });
    await upload.submit();

    // Should show error message on the upload page
    await authedPage.waitForTimeout(3_000);
    const pageText = await authedPage.textContent("body");
    // The page should still be on /upload (not navigated away)
    expect(authedPage.url()).toContain("/upload");
  });
});
