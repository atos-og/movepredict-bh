import { expect, test } from "@playwright/test";

for (const viewport of [
  { width: 360, height: 800 },
  { width: 375, height: 812 },
  { width: 390, height: 844 },
  { width: 414, height: 896 },
]) {
  test(`home fits ${viewport.width}x${viewport.height}`, async ({ page }) => {
    await page.setViewportSize(viewport);
    await page.goto("/");
    await expect(page.locator(".roadmap-home-card")).toBeVisible();
    const metrics = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
      buttonsFit: [...document.querySelectorAll<HTMLElement>(".roadmap-home-card button")].every((button) => button.scrollWidth <= button.clientWidth + 1),
    }));
    expect(metrics.scrollWidth).toBe(metrics.clientWidth);
    expect(metrics.buttonsFit).toBe(true);
  });
}
