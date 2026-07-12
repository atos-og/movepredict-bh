import { expect, test } from "@playwright/test";

test("primary navigation is keyboard accessible", async ({ page }) => {
  await page.goto("/");
  await page.keyboard.press("Tab");
  const focused = page.locator(":focus");
  await expect(focused).toBeVisible();
  await expect(focused).toHaveAccessibleName(/.+/);
  expect(await focused.evaluate((element) => ["A", "BUTTON", "INPUT"].includes(element.tagName))).toBe(true);
});

test("interactive controls have accessible names", async ({ page }) => {
  await page.goto("/?screen=search");
  const unnamed = await page.locator("button, a, input").evaluateAll((elements) =>
    elements.filter((element) => {
      const text = element.textContent?.trim();
      const label = element.getAttribute("aria-label");
      const title = element.getAttribute("title");
      const placeholder = element.getAttribute("placeholder");
      return !text && !label && !title && !placeholder;
    }).length,
  );
  expect(unnamed).toBe(0);
});

test("home loads without horizontal overflow", async ({ page }) => {
  await page.goto("/");
  const layout = await page.evaluate(() => ({
    viewport: document.documentElement.clientWidth,
    content: document.documentElement.scrollWidth,
  }));
  expect(layout.content).toBeLessThanOrEqual(layout.viewport);
});
