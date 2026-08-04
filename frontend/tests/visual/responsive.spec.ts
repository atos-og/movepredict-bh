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

test("floating navigation slides before changing sections", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");

  const navigation = page.locator(".roadmap-nav");
  const indicator = navigation.locator(".floating-navigation-indicator");
  const initialTransform = await indicator.evaluate(
    (element) => getComputedStyle(element).transform,
  );
  const navigationBox = await navigation.boundingBox();

  expect(navigationBox?.height).toBeLessThanOrEqual(64);
  await navigation.getByRole("link", { name: "Linhas" }).click({ noWaitAfter: true });
  await page.waitForTimeout(140);

  const movingTransform = await indicator.evaluate(
    (element) => getComputedStyle(element).transform,
  );
  expect(movingTransform).not.toBe(initialTransform);

  await page.waitForURL(/\/linhas$/);
  await expect(page.locator(".roadmap-nav a[aria-current='page']")).toHaveText("Linhas");
});

test("favorites and more preserve the selected navigation item", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto("/");
  await page.getByRole("link", { name: "Favoritos", exact: true }).click();

  await page.waitForURL(/\/explorar\?view=favorites$/);
  await expect(page.locator(".roadmap-nav [aria-current='page']")).toHaveText("Favoritos");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Favoritos");
  await expect(page.locator(".experience-panel")).toHaveCount(0);

  await page.getByRole("link", { name: "Mais", exact: true }).click();
  await page.waitForURL(/\/explorar\?view=more$/);
  await expect(page.locator(".roadmap-nav [aria-current='page']")).toHaveText("Mais");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mais");
});

test("primary screens keep one page heading and no horizontal overflow", async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  for (const path of [
    "/",
    "/linhas",
    "/pontos",
    "/rota",
    "/viagem",
    "/explorar",
    "/explorar?view=favorites",
    "/explorar?view=more",
  ]) {
    await page.goto(path);
    await expect(page.locator("h1")).toHaveCount(1);
    const layout = await page.evaluate(() => ({
      clientWidth: document.documentElement.clientWidth,
      scrollWidth: document.documentElement.scrollWidth,
    }));
    expect(layout.scrollWidth, path).toBe(layout.clientWidth);
  }
});
