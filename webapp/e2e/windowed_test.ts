import { expect, test, type Page } from "@playwright/test";
import { open } from "./support/ui";

/** The windowed foundation client, driven end to end: toggling the proving
 *  layer issues a viewport request, panning issues more, and panning back
 *  into a visited window is served from the cache with no request at all.
 *
 *  Keyboard pans move the camera an exact 100 px per press, so six presses
 *  east followed by six presses west return to the starting viewport and
 *  therefore to the same quantized window. */

function countRequests(page: Page): { count: () => number } {
  let seen = 0;
  page.on("request", (request) => {
    if (request.url().includes("/api/v1/features/landHistory")) seen += 1;
  });
  return { count: () => seen };
}

const chip = (page: Page) => page.locator(".windowed-chip");

async function settledStatus(page: Page): Promise<void> {
  await expect(chip(page)).toHaveAttribute("data-status", /ready|empty/, { timeout: 15000 });
}

async function pan(page: Page, key: "ArrowRight" | "ArrowLeft", presses: number): Promise<void> {
  for (let index = 0; index < presses; index += 1) {
    await page.keyboard.press(key);
    await page.waitForTimeout(150);
  }
}

test("panning loads windowed features and returning to a window hits the cache", async ({ page }) => {
  const requests = countRequests(page);
  await open(page, { module: "slope" });

  await page.locator(".windowed-toggle").click();
  await settledStatus(page);
  expect(requests.count()).toBeGreaterThan(0);

  // Focus the canvas so keyboard navigation drives the camera.
  await page.locator("#map .maplibregl-canvas").click({ position: { x: 200, y: 200 } });

  await pan(page, "ArrowRight", 6);
  await settledStatus(page);
  const afterPan = requests.count();
  expect(afterPan).toBeGreaterThan(1);

  // The way back crosses only windows the pan out already cached.
  await pan(page, "ArrowLeft", 6);
  await settledStatus(page);
  await page.waitForTimeout(600); // longer than the client debounce
  expect(requests.count()).toBe(afterPan);
});

test("below the minimum zoom no request is issued and the state says so", async ({ page }) => {
  await open(page, { module: "slope" });
  await page.locator(".windowed-toggle").click();
  await settledStatus(page);

  // Region zoom is 16; the floor is 15 and the map's own minimum is 14.
  // force: the control sits at the map's bottom edge, where CI font metrics
  // can leave it under the map note's hit area even though it renders fine.
  const zoomOut = page.locator(".maplibregl-ctrl-zoom-out");
  await zoomOut.click({ force: true });
  await page.waitForTimeout(500);
  await zoomOut.click({ force: true });

  await expect(chip(page)).toHaveAttribute("data-status", "belowZoom", { timeout: 10000 });
});
