import { type Page, type Locator } from "@playwright/test";

/**
 * Page object for the Results page (/results/[uploadId]).
 * Requires authentication.
 */
export class ResultsPage {
  readonly page: Page;

  // Hero header
  readonly heading: Locator;
  readonly similarityScore: Locator;
  readonly similarityText: Locator;

  // Metadata
  readonly swingType: Locator;
  readonly viewLabel: Locator;

  // Share
  readonly shareButton: Locator;

  // Phase navigation
  readonly phaseAddress: Locator;
  readonly phaseTop: Locator;
  readonly phaseImpact: Locator;
  readonly phaseFollowThrough: Locator;

  // Top differences
  readonly topDifferencesSection: Locator;
  readonly differenceCards: Locator;

  // Analyze another
  readonly analyzeAnotherButton: Locator;

  constructor(page: Page) {
    this.page = page;

    this.heading = page.locator('h1:has-text("Swing Analysis")');
    this.similarityScore = page.locator("h1").locator("..").locator("span").first();
    this.similarityText = page.getByText(/similarity to Tiger Woods/i);

    // Metadata row
    this.swingType = page.getByText(/Iron|Driver/i).first();
    this.viewLabel = page.getByText(/Down the Line|Face On/i).first();

    // Share
    this.shareButton = page.locator('button:has-text("Share Results")');

    // Phase navigation buttons
    this.phaseAddress = page.locator('button:has-text("Address")').first();
    this.phaseTop = page.locator('button:has-text("Top")').first();
    this.phaseImpact = page.locator('button:has-text("Impact")').first();
    this.phaseFollowThrough = page.locator(
      'button:has-text("Follow Through")'
    ).first();

    // Differences
    this.topDifferencesSection = page.getByText("Top Areas for Improvement");
    this.differenceCards = page.locator('[class*="difference"], [class*="Difference"]');

    // Analyze another
    this.analyzeAnotherButton = page.locator(
      'a:has-text("Analyze Another Swing"), button:has-text("Analyze Another Swing")'
    );
  }

  async goto(uploadId: string, view = "dtl") {
    await this.page.goto(`/results/${uploadId}?view=${view}`);
    await this.heading.waitFor({ timeout: 15_000 });
  }

  /** Click a phase tab */
  async selectPhase(phase: "address" | "top" | "impact" | "follow_through") {
    const map = {
      address: this.phaseAddress,
      top: this.phaseTop,
      impact: this.phaseImpact,
      follow_through: this.phaseFollowThrough,
    };
    await map[phase].click();
  }
}
