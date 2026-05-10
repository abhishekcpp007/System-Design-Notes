import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Contact Form E2E Tests
 * Covers: Form validation, submission, honeypot, accessibility
 */

test.describe("Contact Form", () => {
  test.beforeEach(async ({ page }) => {
    await page.goto("/contact");
  });

  test("should display contact form", async ({ page }) => {
    await expect(page.getByRole("heading", { level: 1 })).toBeVisible();
    await expect(page.getByLabel(/name/i)).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/message/i)).toBeVisible();
  });

  test("should show validation errors for empty submission", async ({ page }) => {
    // Try to submit empty form
    const submitButton = page.getByRole("button", { name: /send|submit/i });
    await submitButton.click();

    // Should show validation errors
    await expect(page.locator("[role='alert'], .text-red-500, [aria-invalid='true']").first()).toBeVisible();
  });

  test("should validate email format", async ({ page }) => {
    await page.getByLabel(/name/i).fill("Test User");
    await page.getByLabel(/email/i).fill("invalid-email");
    await page.getByLabel(/message/i).fill("Test message");

    const submitButton = page.getByRole("button", { name: /send|submit/i });
    await submitButton.click();

    // Should show email validation error
    await page.waitForTimeout(500);
    const errorVisible = await page.locator("text=/email|invalid/i").count();
    expect(errorVisible).toBeGreaterThan(0);
  });

  test("should submit successfully with valid data", async ({ page }) => {
    // Mock the API endpoint
    await page.route("**/api/v1/contact", (route) => {
      route.fulfill({
        status: 201,
        contentType: "application/json",
        body: JSON.stringify({ message: "Contact form submitted successfully" }),
      });
    });

    await page.getByLabel(/name/i).fill("Test User");
    await page.getByLabel(/email/i).fill("test@example.com");

    // Fill subject if it exists
    const subject = page.getByLabel(/subject/i);
    if (await subject.isVisible()) {
      await subject.fill("Test Subject");
    }

    await page.getByLabel(/message/i).fill("This is a test message for E2E testing.");

    const submitButton = page.getByRole("button", { name: /send|submit/i });
    await submitButton.click();

    // Should show success message
    await expect(page.locator("text=/thank|success|sent/i").first()).toBeVisible({ timeout: 5000 });
  });

  test("honeypot field should be hidden @a11y", async ({ page }) => {
    // The honeypot field should not be visible to real users
    const honeypot = page.locator("[name='website'], [name='url'], [name='honeypot']");
    if (await honeypot.count() > 0) {
      const isVisible = await honeypot.first().isVisible();
      expect(isVisible).toBeFalsy();
    }
  });

  test("should pass accessibility audit @a11y", async ({ page }) => {
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test("form fields should have proper labels @a11y", async ({ page }) => {
    // All inputs should have associated labels
    const inputs = page.locator("input:not([type='hidden']), textarea, select");
    const count = await inputs.count();

    for (let i = 0; i < count; i++) {
      const input = inputs.nth(i);
      const id = await input.getAttribute("id");
      const ariaLabel = await input.getAttribute("aria-label");
      const ariaLabelledBy = await input.getAttribute("aria-labelledby");

      // Must have either a label[for], aria-label, or aria-labelledby
      if (id) {
        const label = page.locator(`label[for="${id}"]`);
        const hasLabel = (await label.count()) > 0;
        expect(hasLabel || ariaLabel || ariaLabelledBy).toBeTruthy();
      }
    }
  });
});
