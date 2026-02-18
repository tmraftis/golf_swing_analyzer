import { type Page, type Locator } from "@playwright/test";
import { gotoWithRetry } from "../fixtures/helpers";

/**
 * Page object for the Shared Results page (/shared/[shareToken]).
 * No authentication required.
 */
export class SharedResultsPage {
  readonly page: Page;

  // Loading
  readonly loadingSpinner: Locator;

  // Error state
  readonly errorHeading: Locator;
  readonly errorMessage: Locator;
  readonly analyzeOwnSwingButton: Locator;

  // Success content
  readonly heading: Locator;
  readonly similarityScore: Locator;
  readonly metadataText: Locator;

  // Phase selector
  readonly phaseAddress: Locator;
  readonly phaseTop: Locator;
  readonly phaseImpact: Locator;
  readonly phaseFollowThrough: Locator;

  // Phase images
  readonly userImageLabel: Locator;
  readonly referenceImageLabel: Locator;

  // Top differences
  readonly topDifferencesHeading: Locator;

  // CTA
  readonly ctaHeading: Locator;
  readonly ctaButton: Locator;

  // Footer
  readonly footer: Locator;

  constructor(page: Page) {
    this.page = page;

    // Loading
    this.loadingSpinner = page.getByText("Loading swing analysis...");

    // Error
    this.errorHeading = page.getByText("Analysis Unavailable");
    this.errorMessage = page.getByText(
      "This swing analysis has expired or been made private."
    );
    this.analyzeOwnSwingButton = page.locator(
      'a:has-text("Analyze Your Own Swing")'
    );

    // Success
    this.heading = page.getByText("Swing Analysis").first();
    this.similarityScore = page.locator("text=/\\d+%/").first();
    this.metadataText = page.getByText(/Similarity to Tiger Woods/i);

    // Phase selector
    this.phaseAddress = page.locator('button:has-text("Address")').first();
    this.phaseTop = page.locator('button:has-text("Top")').first();
    this.phaseImpact = page.locator('button:has-text("Impact")').first();
    this.phaseFollowThrough = page.locator(
      'button:has-text("Follow-Through")'
    ).first();

    // Images
    this.userImageLabel = page.getByText("User");
    this.referenceImageLabel = page.getByText("Tiger Woods");

    // Top differences
    this.topDifferencesHeading = page.getByText("Top Areas for Improvement");

    // CTA
    this.ctaHeading = page.getByText("Think you can beat this score?");
    this.ctaButton = page.locator('a:has-text("Analyze Your Swing")').first();

    // Footer
    this.footer = page.getByText("Powered by Pure");
  }

  async goto(shareToken: string) {
    const content = this.page
      .getByText("Swing Analysis")
      .or(this.page.getByText("Analysis Unavailable"))
      .or(this.page.getByText("Loading swing analysis..."));

    await gotoWithRetry(this.page, `/shared/${shareToken}`, content.first());

    // If still loading, wait for it to resolve
    await this.loadingSpinner
      .waitFor({ state: "hidden", timeout: 10_000 })
      .catch(() => {});
  }
}
