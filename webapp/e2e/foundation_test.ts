import { expect, test, type Page } from "@playwright/test";
import { open } from "./support/ui";

/** Foundation overlays end to end: the registry-driven layer control, the
 *  windowed delivery beneath it, on-screen attribution, the audit record a
 *  clicked foundation feature opens, and visibility surviving module and
 *  region switches. */

function trackRequests(page: Page, key: string): { urls: string[] } {
  const urls: string[] = [];
  page.on("request", (request) => {
    if (request.url().includes(`/api/v1/features/${key}`)) urls.push(request.url());
  });
  return { urls };
}

async function toggleLayer(page: Page, key: string): Promise<void> {
  await page.locator(".foundation-toggle").click();
  await page.locator(`.foundation-item[data-layer="${key}"]`).click();
  await page.keyboard.press("Escape");
}

async function expectStatus(page: Page, key: string, status: RegExp): Promise<void> {
  await page.locator(".foundation-toggle").click();
  await expect(page.locator(`.foundation-item[data-layer="${key}"] .foundation-status`)).toHaveAttribute(
    "data-layer-status",
    status,
    { timeout: 15000 },
  );
  await page.keyboard.press("Escape");
}

async function pan(page: Page, key: "ArrowRight" | "ArrowLeft", presses: number): Promise<void> {
  // locator.press focuses the canvas itself — a click would instead pick a
  // foundation feature, and the popup it opens would steal keyboard focus.
  const canvas = page.locator("#map .maplibregl-canvas");
  for (let index = 0; index < presses; index += 1) {
    // A generous per-press timeout: tessellating a freshly loaded window can
    // stall the main thread for a beat, and the press queues behind it.
    await canvas.press(key, { timeout: 15000 });
    await page.waitForTimeout(150);
  }
}

test("panning loads windowed features and returning to a window hits the cache", async ({ page }) => {
  test.slow(); // two 12-press pans with loads in between
  // The pan/cache mechanics are layer-agnostic; railway's thin lines keep
  // deck's tessellation out of the timing. landHistory — the difficulty
  // proof — loads real windows in the attribution and below-zoom tests.
  const requests = trackRequests(page, "railway");
  await open(page, { module: "slope" });

  await toggleLayer(page, "railway");
  await expect(page.locator(".map-attribution")).toContainText("国土数値情報");
  await expectStatus(page, "railway", /ready|empty/);
  expect(requests.urls.length).toBeGreaterThan(0);

  await pan(page, "ArrowRight", 12);
  await expectStatus(page, "railway", /ready|empty/);
  expect(requests.urls.length).toBeGreaterThan(1);

  // Twelve 100 px presses (~1.4 km at z16) return exactly to the start, so
  // the settled window resolves from the cache: the starting window's URL
  // appears exactly once in the whole trace, and after settling no further
  // request fires. (Windows superseded mid-flight may repeat — cancellation
  // is deliberately prioritised over caching them.)
  const firstWindow = requests.urls[0];
  await pan(page, "ArrowLeft", 12);
  await expectStatus(page, "railway", /ready|empty/);
  const settled = requests.urls.length;
  await page.waitForTimeout(800); // longer than the client debounce
  expect(requests.urls.length).toBe(settled);
  expect(requests.urls.filter((url) => url === firstWindow)).toHaveLength(1);
});

test("below the minimum zoom no request is issued and the state says so", async ({ page }) => {
  // Point features: zero tessellation cost, so the gestures never queue
  // behind deck on software-GL hardware. The layer's floor is 15 and the
  // map's own minimum is 14, so two zoom-outs cross it.
  await open(page, { module: "slope" });
  await toggleLayer(page, "publishedLandPrice");
  await expectStatus(page, "publishedLandPrice", /ready|empty/);

  const canvas = page.locator("#map .maplibregl-canvas");
  await canvas.dblclick({ position: { x: 300, y: 200 }, modifiers: ["Shift"] });
  await expectStatus(page, "publishedLandPrice", /ready|empty/);
  await canvas.dblclick({ position: { x: 300, y: 200 }, modifiers: ["Shift"] });

  await expectStatus(page, "publishedLandPrice", /belowZoom/);
});

test("clicking a foundation feature opens its raw audit record", async ({ page }) => {
  await open(page, { module: "roads" });
  await toggleLayer(page, "landUseMesh");
  await expectStatus(page, "landUseMesh", /ready/);

  // The 2021 land-use mesh blankets the study window, so a click away from
  // the thin road lines lands on a mesh cell beneath the analysis.
  await page.locator("#map .maplibregl-canvas").click({ position: { x: 520, y: 320 } });
  const popup = page.locator(".maplibregl-popup");
  await expect(popup.locator(".popup-eyebrow")).toHaveText("基础图层");
  await expect(popup.locator(".popup-title")).toHaveText("土地利用网格 (2021)");

  await popup.locator(".audit-trigger").first().click();
  await expect(page.locator(".audit-drawer.open")).toBeVisible();
  // The record is raw-kind evidence with the source's own timestamp shown.
  await expect(page.locator(".audit-drawer.open")).toContainText("原始数据");
  await expect(page.locator(".audit-drawer.open")).toContainText("2021");
});

test("layer visibility survives module and region switches", async ({ page }) => {
  await open(page, { module: "slope" });
  await toggleLayer(page, "landHistory");
  await expect(page.locator(".map-attribution")).toBeVisible();

  await page.locator('[data-module="roads"]').click();
  await expect(page.locator(".map-attribution")).toContainText("国土交通省");

  // Mobara sits below the layer's zoom floor, so the state is a visible
  // "zoom in" rather than a silent absence — and the toggle survives.
  await page.locator('[data-module="solar"]').click();
  await expect(page.locator(".map-attribution")).toContainText("国土交通省");
  await expectStatus(page, "landHistory", /belowZoom|loading|ready|empty/);
});

test("the standard basemap hands its buildings over to windowed OSM data", async ({ page }) => {
  const requests = trackRequests(page, "osmBuildings");
  // roads draws no buildings of its own, so the detail layer is active.
  await open(page, { module: "roads" });

  // Auto-managed: no toggle was touched, yet the handover zoom requests data
  // and the ODbL notice joins the attribution strip.
  await expect.poll(() => requests.urls.length, { timeout: 15000 }).toBeGreaterThan(0);
  await expect(page.locator(".map-attribution")).toContainText("OpenStreetMap");

  // The layer is basemap experience, not a listed toggle.
  await page.locator(".foundation-toggle").click();
  await expect(page.locator('.foundation-item[data-layer="osmBuildings"]')).toHaveCount(0);
  await page.keyboard.press("Escape");

  // Modules that draw their own buildings suppress it — with no other
  // foundation layer active the whole attribution strip goes away.
  await open(page, { module: "slope" });
  await expect(page.locator(".map-attribution")).toHaveCount(0);
});
