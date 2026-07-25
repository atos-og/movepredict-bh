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

test("route origin actions keep equal dimensions and clear spacing", async ({ page }) => {
  await page.goto("/rota?destination=Savassi&lat=-19.937246&lon=-43.9355817");
  await expect(page.getByRole("heading", { name: "De onde voce esta saindo?" })).toBeVisible();

  const layout = await page.locator(".roadmap-unavailable-actions").evaluate((actions) => {
    const controls = [...actions.querySelectorAll<HTMLElement>("button, a")];
    const boxes = controls.map((control) => control.getBoundingClientRect());
    return {
      widths: boxes.map((box) => box.width),
      heights: boxes.map((box) => box.height),
      gap: boxes[1].top - boxes[0].bottom,
    };
  });

  expect(layout.widths).toHaveLength(2);
  expect(Math.abs(layout.widths[0] - layout.widths[1])).toBeLessThan(1);
  expect(layout.heights.every((height) => height >= 48)).toBe(true);
  expect(layout.gap).toBeGreaterThanOrEqual(12);
});

test("manual origin search opens as a separate section", async ({ page }) => {
  await page.goto("/rota?destination=Savassi&lat=-19.937246&lon=-43.9355817");
  const toggle = page.locator(".roadmap-unavailable-actions .roadmap-secondary");
  await expect(toggle).toHaveText("Informar outro ponto de partida");
  await toggle.click();

  await expect(toggle).toHaveAttribute("aria-expanded", "true");
  await expect(toggle).toHaveText("Fechar busca de origem");
  await expect(page.getByLabel("Buscar outro ponto de partida")).toBeVisible();

  const separation = await page.evaluate(() => {
    const actions = document.querySelector(".roadmap-unavailable-actions")?.getBoundingClientRect();
    const search = document.querySelector(".manual-origin-search")?.getBoundingClientRect();
    if (!actions || !search) throw new Error("Origin controls were not rendered");
    return search.top - actions.bottom;
  });

  expect(separation).toBeGreaterThanOrEqual(20);
});
