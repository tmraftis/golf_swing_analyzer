/**
 * Home page E2E tests.
 *
 * Runs on both dev and prod projects.
 * Tests both authenticated and unauthenticated states.
 */
import { test, expect } from "../fixtures/auth";
import { HomePage } from "../pages/home.page";

test.describe("Home Page — unauthenticated", () => {
  test("shows hero heading and Get Started CTA", async ({ unauthPage }) => {
    const home = new HomePage(unauthPage);
    await home.goto();

    // Hero heading
    await expect(home.heading).toBeVisible();
    await expect(home.heading).toContainText("Swing");

    // CTA should say "Get Started" for visitors
    await expect(home.ctaGetStarted).toBeVisible();
  });

  test("header shows Sign In link", async ({ unauthPage }) => {
    const home = new HomePage(unauthPage);
    await home.goto();

    await expect(home.signInLink).toBeVisible();
    await expect(home.signOutButton).not.toBeVisible();
  });

  test("Get Started CTA links to signup", async ({ unauthPage }) => {
    const home = new HomePage(unauthPage);
    await home.goto();

    const href = await home.ctaGetStarted.getAttribute("href");
    expect(href).toContain("/api/auth/signup");
  });

  test("How it works section is visible", async ({ unauthPage }) => {
    const home = new HomePage(unauthPage);
    await home.goto();

    await expect(home.howItWorksHeading).toBeVisible();
  });
});

test.describe("Home Page — authenticated", () => {
  test("shows Start Your Analysis CTA", async ({ authedPage }) => {
    const home = new HomePage(authedPage);
    await home.goto();

    // CTA should change for logged-in users
    await expect(home.ctaStartAnalysis).toBeVisible();
  });

  test("header shows Sign Out button", async ({ authedPage }) => {
    const home = new HomePage(authedPage);
    await home.goto();

    await expect(home.signOutButton).toBeVisible();
    await expect(home.signInLink).not.toBeVisible();
  });

  test("Start Your Analysis links to upload page", async ({ authedPage }) => {
    const home = new HomePage(authedPage);
    await home.goto();

    const href = await home.ctaStartAnalysis.getAttribute("href");
    expect(href).toBe("/upload");
  });
});
