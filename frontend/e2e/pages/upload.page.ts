import { type Page, type Locator } from "@playwright/test";
import path from "path";
import { gotoWithRetry } from "../fixtures/helpers";

/**
 * Page object for the Upload page (/upload).
 * Requires authentication.
 */
export class UploadPage {
  readonly page: Page;

  // Page heading
  readonly heading: Locator;

  // Step 1: Swing type
  readonly ironButton: Locator;
  readonly driverButton: Locator;

  // Step 2: Camera angle
  readonly dtlButton: Locator;
  readonly foButton: Locator;

  // Step 3: Video drop zone
  readonly dropZone: Locator;
  readonly dropZoneText: Locator;
  readonly fileInput: Locator;
  readonly removeButton: Locator;

  // Submit
  readonly submitButton: Locator;
  readonly errorMessage: Locator;

  // Loading state
  readonly loadingAnimation: Locator;

  constructor(page: Page) {
    this.page = page;

    this.heading = page.locator('h1:has-text("Upload Your Swing")');

    // Swing type
    this.ironButton = page.locator('button:has-text("Iron")');
    this.driverButton = page.locator('button:has-text("Driver")');

    // Camera angle
    this.dtlButton = page.locator('button:has-text("Down the Line")');
    this.foButton = page.locator('button:has-text("Face On")');

    // Video drop zone — the hidden file input
    this.dropZone = page.locator('text="Drag & drop or click to select"');
    this.dropZoneText = page.getByText("Drag & drop or click to select");
    this.fileInput = page.locator('input[type="file"]');
    this.removeButton = page.locator('button:has-text("Remove")');

    // Submit
    this.submitButton = page.locator('button:has-text("Submit for Analysis")');
    this.errorMessage = page.locator(
      'text=/Upload failed|Analysis failed|error/i'
    );

    // Loading
    this.loadingAnimation = page.locator(
      'text=/uploading|analyzing/i'
    );
  }

  async goto() {
    await gotoWithRetry(this.page, "/upload", this.heading);
  }

  /** Upload a video file via the hidden input */
  async uploadVideo(filePath: string) {
    await this.fileInput.setInputFiles(filePath);
  }

  /** Upload the test video fixture */
  async uploadTestVideo() {
    const testVideo = path.resolve(__dirname, "../fixtures/test-video.mp4");
    await this.uploadVideo(testVideo);
  }

  /** Select a camera angle */
  async selectView(view: "dtl" | "fo") {
    if (view === "dtl") {
      await this.dtlButton.click();
    } else {
      await this.foButton.click();
    }
  }

  /** Submit the form and wait for navigation or loading */
  async submit() {
    await this.submitButton.click();
  }
}
