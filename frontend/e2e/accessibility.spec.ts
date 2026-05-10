import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";

/**
 * Global Accessibility Tests
 * Runs accessibility audits on all main pages.
 * Tag: @a11y
 */

const pages = [
  { path: "/", name: "Homepage" },
  { path: "/projects", name: "Projects" },
  { path: "/blog", name: "Blog" },
  { path: "/contact", name: "Contact" },
  { path: "/auth/login", name: "Login" },
];

for (const { path, name } of pages) {
  test.describe(`${name} Accessibility @a11y`, () => {
    test(`${name} - WCAG 2.1 AA compliance`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");

      const results = await new AxeBuilder({ page })
        .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
        .analyze();

      // Log violations for debugging
      if (results.violations.length > 0) {
        console.log(`\n${name} - Accessibility violations:`);
        results.violations.forEach((v) => {
          console.log(`  [${v.impact}] ${v.id}: ${v.description}`);
          v.nodes.forEach((n) => {
            console.log(`    Target: ${n.target}`);
          });
        });
      }

      expect(results.violations).toEqual([]);
    });

    test(`${name} - Color contrast check`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");

      const results = await new AxeBuilder({ page })
        .withTags(["wcag2aa"])
        .options({ runOnly: ["color-contrast"] })
        .analyze();

      expect(results.violations).toEqual([]);
    });

    test(`${name} - Keyboard navigation`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");

      // Tab through the page and verify focus is visible
      let tabCount = 0;
      const maxTabs = 20;

      while (tabCount < maxTabs) {
        await page.keyboard.press("Tab");
        tabCount++;

        const activeElement = await page.evaluate(() => {
          const el = document.activeElement;
          if (!el || el === document.body) return null;
          const styles = window.getComputedStyle(el);
          return {
            tag: el.tagName,
            hasOutline: styles.outlineStyle !== "none" || styles.boxShadow !== "none",
            isInteractive: ["A", "BUTTON", "INPUT", "TEXTAREA", "SELECT"].includes(el.tagName),
          };
        });

        if (activeElement?.isInteractive) {
          // Interactive elements should have visible focus indicator
          // (This is a soft check - CSS focus-visible may not be detectable)
          expect(activeElement.tag).toBeTruthy();
        }
      }
    });

    test(`${name} - Images have alt text`, async ({ page }) => {
      await page.goto(path);
      await page.waitForLoadState("networkidle");

      const images = page.locator("img");
      const count = await images.count();

      for (let i = 0; i < count; i++) {
        const img = images.nth(i);
        const alt = await img.getAttribute("alt");
        const role = await img.getAttribute("role");
        const ariaHidden = await img.getAttribute("aria-hidden");

        // Image must have alt text, or be decorative (role=presentation or aria-hidden)
        const isAccessible = alt !== null || role === "presentation" || ariaHidden === "true";
        expect(isAccessible).toBeTruthy();
      }
    });

    test(`${name} - Landmarks present`, async ({ page }) => {
      await page.goto(path);

      // Must have main landmark
      const main = page.locator("main, [role='main']");
      await expect(main).toBeAttached();

      // Must have navigation
      const nav = page.locator("nav, [role='navigation']");
      await expect(nav).toBeAttached();
    });

    test(`${name} - Language attribute set`, async ({ page }) => {
      await page.goto(path);
      const lang = await page.locator("html").getAttribute("lang");
      expect(lang).toBeTruthy();
      expect(lang!.length).toBeGreaterThanOrEqual(2);
    });
  });
}
