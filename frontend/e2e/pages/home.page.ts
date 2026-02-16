import { type Page, type Locator } from "@playwright/test";

/**
 * Page object for the Home page (/).
 */
export class HomePage {
  readonly page: Page;

  // Hero section
  readonly heading: Locator;
  readonly ctaGetStarted: Locator;
  readonly ctaStartAnalysis: Locator;

  // Header
  readonly logo: Locator;
  readonly signInLink: Locator;
  readonly headerGetStarted: Locator;
  readonly signOutButton: Locator;
  readonly userEmail: Locator;

  // Feature cards
  readonly howItWorksHeading: Locator;
  readonly featureCards: Locator;

  constructor(page: Page) {
    this.page = page;

    // Hero
    this.heading = page.locator("h1");
    this.ctaGetStarted = page.locator('a:has-text("Get Started")').first();
    this.ctaStartAnalysis = page.locator(
      'a:has-text("Start Your Analysis"), button:has-text("Start Your Analysis")'
    );

    // Header
    this.logo = page.locator('a[href="/"]').first();
    this.signInLink = page.locator('a:has-text("Sign In")');
    this.headerGetStarted = page.locator(
      'header a:has-text("Get Started"), nav a:has-text("Get Started")'
    );
    this.signOutButton = page.locator('button:has-text("Sign Out")');
    this.userEmail = page.locator('[data-testid="user-email"]');

    // Features
    this.howItWorksHeading = page.getByText("How it works");
    this.featureCards = page.locator("section").filter({ hasText: "How it works" });
  }

  async goto() {
    await this.page.goto("/");
    await this.page.waitForLoadState("networkidle");
  }
}
