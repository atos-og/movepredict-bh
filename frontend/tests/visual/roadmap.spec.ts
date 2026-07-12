import { expect, test } from "@playwright/test";

const screens = [
  ["home", "/"],
  ["location-permission", "/?screen=permission"],
  ["location-loading", "/?screen=loading"],
  ["location-ready", "/?screen=ready"],
  ["destination-search", "/?screen=search"],
  ["route-options", "/rota?preview=1"],
  ["route-details", "/rota?preview=1&details=1"],
  ["active-journey", "/viagem?preview=1"],
  ["map-with-bus", "/viagem?preview=1&map=1"],
  ["line-details", "/linha/989341"],
  ["explore-lines", "/linhas"],
  ["nearby-stops", "/pontos"],
] as const;

for (const [name, path] of screens) {
  test(name, async ({ page }) => {
    await page.goto(path);
    await page.addStyleTag({ content: "nextjs-portal { display: none !important; } .leaflet-tile-pane { opacity: 0 !important; } .roadmap-map { background: #e7edf2 !important; }" });
    await expect(page.locator("main")).toBeVisible();
    if (path.includes("linha/")) await expect(page.locator(".stop-timeline > div").first()).toBeVisible({ timeout: 45_000 });
    if (path === "/linhas") await expect(page.locator(".roadmap-line-list > a").first()).toBeVisible({ timeout: 10_000 });
    if (path === "/pontos") await expect(page.locator(".nearby-cards article").first()).toBeVisible({ timeout: 10_000 });
    if (path.includes("screen=") || path.includes("map=1") || path === "/" || path === "/pontos") await page.waitForTimeout(900);
    await expect(page).toHaveScreenshot(`${name}.png`, { animations: "disabled", fullPage: true });
  });
}
