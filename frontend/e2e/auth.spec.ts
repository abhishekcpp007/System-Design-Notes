import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Authentication Flow E2E Tests
 * Covers: Login, signup, protected routes, session management
 */

test.describe("Authentication Flow", () => {
  test("should display login page", async ({ page }) => {
    await page.goto("/auth/login");
    await expect(page.getByRole("heading", { name: /log in|sign in/i })).toBeVisible();
    await expect(page.getByLabel(/email/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
  });

  test("should show validation errors on empty login", async ({ page }) => {
    await page.goto("/auth/login");

    const loginButton = page.getByRole("button", { name: /log in|sign in/i });
    await loginButton.click();

    // Should show validation errors
    await page.waitForTimeout(500);
    const errors = page.locator("[role='alert'], .text-red-500, [aria-invalid='true']");
    const errorCount = await errors.count();
    expect(errorCount).toBeGreaterThan(0);
  });

  test("should handle invalid credentials", async ({ page }) => {
    await page.goto("/auth/login");

    // Mock failed login
    await page.route("**/api/v1/auth/login", (route) => {
      route.fulfill({
        status: 401,
        contentType: "application/json",
        body: JSON.stringify({ detail: "Invalid email or password" }),
      });
    });

    await page.getByLabel(/email/i).fill("wrong@example.com");
    await page.getByLabel(/password/i).fill("wrongpassword");

    const loginButton = page.getByRole("button", { name: /log in|sign in/i });
    await loginButton.click();

    // Should show error message
    await expect(page.locator("text=/invalid|incorrect|wrong/i").first()).toBeVisible({ timeout: 5000 });
  });

  test("should redirect to admin on successful login", async ({ page }) => {
    await page.goto("/auth/login");

    // Mock successful login
    await page.route("**/api/v1/auth/login", (route) => {
      route.fulfill({
        status: 200,
        contentType: "application/json",
        body: JSON.stringify({
          access_token: "mock-jwt-token",
          token_type: "bearer",
        }),
      });
    });

    await page.getByLabel(/email/i).fill("admin@example.com");
    await page.getByLabel(/password/i).fill("StrongP@ss1");

    const loginButton = page.getByRole("button", { name: /log in|sign in/i });
    await loginButton.click();

    // Should redirect to admin dashboard
    await page.waitForURL("**/admin**", { timeout: 5000 });
    expect(page.url()).toContain("/admin");
  });

  test("should protect admin routes", async ({ page }) => {
    // Try to access admin without authentication
    await page.goto("/admin");

    // Should redirect to login or show unauthorized
    await page.waitForTimeout(2000);
    const url = page.url();
    const hasRedirected = url.includes("/auth/login") || url.includes("/login");
    const hasUnauthorized = await page.locator("text=/unauthorized|login|sign in/i").count() > 0;
    expect(hasRedirected || hasUnauthorized).toBeTruthy();
  });

  test("login page should pass accessibility audit @a11y", async ({ page }) => {
    await page.goto("/auth/login");
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
      .analyze();
    expect(results.violations).toEqual([]);
  });

  test("password field should have proper autocomplete @a11y", async ({ page }) => {
    await page.goto("/auth/login");
    const passwordInput = page.getByLabel(/password/i);
    const autocomplete = await passwordInput.getAttribute("autocomplete");
    expect(autocomplete).toBe("current-password");
  });
});
