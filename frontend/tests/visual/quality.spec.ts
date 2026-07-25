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

test("destination search keeps a readable mobile hierarchy", async ({ page }) => {
  await page.goto("/?screen=search");

  const layout = await page.evaluate(() => {
    const tabItems = [...document.querySelectorAll<HTMLElement>(".search-tabs > *")];
    const controls = [...document.querySelectorAll<HTMLElement>(".search-submit, .search-cancel")];
    return {
      viewport: document.documentElement.clientWidth,
      content: document.documentElement.scrollWidth,
      tabHeights: tabItems.map((item) => item.getBoundingClientRect().height),
      tabDecorations: tabItems.map((item) => getComputedStyle(item).textDecorationLine),
      controlSizes: controls.map((control) => ({
        height: control.getBoundingClientRect().height,
        width: control.getBoundingClientRect().width,
      })),
    };
  });

  expect(layout.content).toBeLessThanOrEqual(layout.viewport);
  expect(layout.tabHeights.every((height) => height >= 38)).toBe(true);
  expect(layout.tabDecorations.every((decoration) => decoration === "none")).toBe(true);
  expect(layout.controlSizes.every(({ height, width }) => height >= 40 && width >= 40)).toBe(true);
});
