import { type Page, type Locator } from "@playwright/test";
import { gotoWithRetry } from "../fixtures/helpers";

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

    // Hero — scope CTAs to the hero section so we don't pick up header links
    this.heading = page.locator("h1");
    this.ctaGetStarted = page
      .locator("section")
      .filter({ has: page.locator("h1") })
      .locator('a:has-text("Get Started")');
    this.ctaStartAnalysis = page
      .locator("section")
      .filter({ has: page.locator("h1") })
      .locator('a:has-text("Start Your Analysis")');

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
    await gotoWithRetry(this.page, "/", this.heading);
  }
}
