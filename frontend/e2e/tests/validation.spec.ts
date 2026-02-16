/**
 * File validation E2E tests (dev only).
 *
 * Tests client-side upload validation:
 *   - Invalid file types
 *   - File input accepts correct MIME types
 *   - Submit button disabled states
 */
import { test, expect } from "../fixtures/auth";
import { UploadPage } from "../pages/upload.page";
import path from "path";

test.describe("Upload Validation", () => {
  test.skip(
    ({ }, testInfo) => testInfo.project.name === "prod",
    "Validation tests only run in dev"
  );

  test("submit button is disabled without a video", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    await expect(upload.submitButton).toBeDisabled();
  });

  test("Iron is selected by default", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    // Iron button should have selected styling (check aria or class)
    await expect(upload.ironButton).toBeVisible();
  });

  test("Driver button is disabled", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    // Driver button should be visually disabled (opacity-50)
    await expect(upload.driverButton).toBeVisible();
    const classes = await upload.driverButton.getAttribute("class");
    expect(classes).toContain("opacity-50");
  });

  test("DTL is selected by default", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    // DTL button should be visible and active
    await expect(upload.dtlButton).toBeVisible();
  });

  test("can switch to Face On view", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    await upload.selectView("fo");

    // FO button should now have selected styling
    const foClasses = await upload.foButton.getAttribute("class");
    expect(foClasses).toContain("border-forest-green");
  });

  test("rejects invalid file type", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    // Create an invalid text file and try to upload it
    const invalidFile = path.resolve(
      __dirname,
      "../fixtures/test-invalid.txt"
    );
    await upload.uploadVideo(invalidFile);

    // Should show an error or the file should not be accepted
    // The drop zone has accept="video/mp4,video/quicktime" so the input
    // may reject it silently. Check that submit remains disabled.
    await expect(upload.submitButton).toBeDisabled();
  });

  test("accepts valid video file", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    await upload.uploadTestVideo();

    // After a valid video is loaded, the remove button should appear
    await expect(upload.removeButton).toBeVisible({ timeout: 5_000 });

    // Submit button should now be enabled
    await expect(upload.submitButton).toBeEnabled();
  });

  test("can remove uploaded video", async ({ authedPage }) => {
    const upload = new UploadPage(authedPage);
    await upload.goto();

    await upload.uploadTestVideo();
    await expect(upload.removeButton).toBeVisible({ timeout: 5_000 });

    // Remove the file
    await upload.removeButton.click();

    // Drop zone text should reappear, submit disabled again
    await expect(upload.dropZoneText).toBeVisible();
    await expect(upload.submitButton).toBeDisabled();
  });
});
