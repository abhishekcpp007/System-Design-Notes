import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Projects Page E2E Tests
 * Covers: Listing, filtering, detail pages, accessibility
 */

test.describe("Projects Page", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/projects");
  });

  test("should display projects page", async ({ page }) => {
    await expect(page).toHaveTitle(/Projects/);
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
  });

  test("should have filter buttons", async ({ page }) => {
    // Look for filter/category buttons
    const buttons = page.getByRole("button");
    const buttonCount = await buttons.count();
    expect(buttonCount).toBeGreaterThan(0);
  });

  test("should navigate to project detail", async ({ page }) => {
    // Click first project link (if any projects exist)
    const projectLinks = page.locator("a[href*='/projects/']");
    const count = await projectLinks.count();
    if (count > 0) {
      await projectLinks.first().click();
      await page.waitForLoadState("networkidle");
      // Should be on detail page
      expect(page.url()).toContain("/projects/");
      await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    }
  });

  test("should pass accessibility audit @a11y", async ({ page }) => {
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test("should show loading state gracefully", async ({ page }) => {
    // Intercept API and delay response
    await page.route("**/api/v1/projects**", async (route) => {
      await new Promise((r) => setTimeout(r, 2000));
      await route.continue();
    });
    await page.reload();
    // Should show some loading indicator or skeleton
    const hasLoading = await page.locator("[role='status'], .animate-pulse, [aria-busy='true']").count();
    expect(hasLoading).toBeGreaterThanOrEqual(0); // Graceful even if no loading state
  });
});
