import { expect, test } from "@playwright/test";

test("primary navigation is keyboard accessible", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".roadmap-home-card")).toBeVisible();
  await page.locator("body").click({ position: { x: 1, y: 1 } });
  const linesLink = page.getByRole("link", { name: "Linhas", exact: true });
  for (let index = 0; index < 20; index += 1) {
    await page.keyboard.press("Tab");
    if (await linesLink.evaluate((element) => document.activeElement === element)) break;
  }
  await expect(linesLink).toBeFocused();
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
