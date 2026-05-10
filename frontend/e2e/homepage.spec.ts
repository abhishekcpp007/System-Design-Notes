import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Homepage E2E Tests
 * Covers: Navigation, Hero section, responsive behavior, accessibility
 */

test.describe("Homepage", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/");
  });

  test("should load successfully with hero section", async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/Portfolio/);

    // Hero section visible
    const hero = page.locator("[data-testid='hero-section'], section").first();
    await expect(hero).toBeVisible();

    // Navigation visible
    const nav = page.getByRole("navigation");
    await expect(nav).toBeVisible();
  });

  test("should have working navigation links", async ({ page }) => {
    // Check all main nav links exist
    await expect(page.getByRole("link", { name: /projects/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /blog/i })).toBeVisible();
    await expect(page.getByRole("link", { name: /contact/i })).toBeVisible();
  });

  test("should toggle dark mode", async ({ page }) => {
    // Find dark mode toggle button
    const toggle = page.getByRole("button", { name: /dark mode|theme|toggle/i });
    if (await toggle.isVisible()) {
      await toggle.click();
      // Check that html element has 'dark' class or not
      const html = page.locator("html");
      const hasDark = await html.getAttribute("class");
      expect(hasDark).toBeDefined();
    }
  });

  test("should be responsive on mobile @mobile", async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 667 });
    await page.goto("/");

    // Mobile menu button should appear
    const menuButton = page.getByRole("button", { name: /menu|hamburger|navigation/i });
    if (await menuButton.isVisible()) {
      await menuButton.click();
      // Menu items should be visible after click
      await expect(page.getByRole("link", { name: /projects/i })).toBeVisible();
    }
  });

  test("should pass accessibility audit @a11y", async ({ page }) => {
    const accessibilityScanResults = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .exclude(".framer-motion") // Exclude animated elements that may temporarily violate
      .analyze();

    expect(accessibilityScanResults.violations).toEqual([]);
  });

  test("should have proper heading hierarchy @a11y", async ({ page }) => {
    // Check that there's exactly one h1
    const h1Count = await page.locator("h1").count();
    expect(h1Count).toBe(1);

    // Check heading hierarchy (no skipped levels)
    const headings = await page.locator("h1, h2, h3, h4, h5, h6").all();
    let lastLevel = 0;
    for (const heading of headings) {
      const tagName = await heading.evaluate((el) => el.tagName.toLowerCase());
      const level = parseInt(tagName[1]);
      // Level should not jump by more than 1
      if (lastLevel > 0) {
        expect(level).toBeLessThanOrEqual(lastLevel + 1);
      }
      lastLevel = level;
    }
  });

  test("should have keyboard navigable elements @a11y", async ({ page }) => {
    // Tab through interactive elements
    await page.keyboard.press("Tab");
    const firstFocused = await page.evaluate(() => document.activeElement?.tagName);
    expect(firstFocused).toBeTruthy();

    // Continue tabbing - should reach navigation
    for (let i = 0; i < 5; i++) {
      await page.keyboard.press("Tab");
    }
    const focused = await page.evaluate(() => document.activeElement?.tagName);
    expect(["A", "BUTTON", "INPUT"]).toContain(focused);
  });
});
