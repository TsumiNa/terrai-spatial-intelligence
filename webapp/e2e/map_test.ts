import { expect, test, type Page } from "@playwright/test";

async function waitForMap(page: Page) {
  await page.goto("/");
  await expect(page.locator(".metrics .metric").first()).toBeVisible({ timeout: 15000 });
  await expect(page.locator("#map .maplibregl-canvas")).toBeVisible({ timeout: 20000 });
}

test("both regions load with GSI attribution", async ({ page }) => {
  const photoTiles: string[] = [];
  page.on("response", (response) => {
    if (response.url().includes("cyberjapandata.gsi.go.jp/xyz/seamlessphoto/")) photoTiles.push(response.url());
  });

  await waitForMap(page);
  await expect(page.locator(".maplibregl-ctrl-attrib")).toContainText("地理院");

  // Mobara via the overview's renewable tab, with the photo basemap active —
  // the live nationwide imagery streams there just as it does everywhere.
  await page.locator(".basemap-button", { hasText: "影像" }).click();
  await page.locator(".view-tab", { hasText: "茂原" }).click();
  await expect(page.locator(".region-pill")).toHaveText("千叶 · 茂原市");
  await expect.poll(() => photoTiles.length, { timeout: 15000 }).toBeGreaterThan(0);
});

test("loads the vendored sprite from an absolute URL (v6 requires it)", async ({ page }) => {
  const spriteResponses: boolean[] = [];
  const invalidSpriteErrors: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/basemap/sprite/std")) spriteResponses.push(r.ok());
  });
  page.on("console", (m) => {
    if (m.text().includes("Invalid sprite URL")) invalidSpriteErrors.push(m.text());
  });

  await waitForMap(page);
  await page.waitForTimeout(1500);
  // the sprite json/png were fetched from our own origin and succeeded…
  expect(spriteResponses.length).toBeGreaterThan(0);
  expect(spriteResponses.every(Boolean)).toBe(true);
  // …and MapLibre v6 raised no "must be absolute" rejection
  expect(invalidSpriteErrors).toEqual([]);
});

test("basemap switching keeps the single map instance (no camera rebuild)", async ({ page }) => {
  await waitForMap(page);
  const canvas = await page.locator("#map .maplibregl-canvas").elementHandle();
  for (const label of ["影像", "起伏", "坡度", "标准"]) {
    await page.locator(".basemap-button", { hasText: label }).click();
    await page.waitForTimeout(250);
    expect(await canvas!.evaluate((element) => element.isConnected)).toBe(true);
  }
});

test("boots and renders with gsi-cyberjapan.github.io blocked (pinned snapshot)", async ({ page }) => {
  // The experimental GitHub Pages host served the style and its sprite; both are
  // now vendored, so nothing should reach that host. Abort any request to it and
  // prove the map still constructs and renders (tiles from cyberjapandata, glyphs
  // from maps.gsi.go.jp) with zero hits to the retired host.
  const blockedHits: string[] = [];
  await page.route("**gsi-cyberjapan.github.io**", (route) => {
    blockedHits.push(route.request().url());
    return route.abort();
  });

  await waitForMap(page);
  await expect(page.locator(".maplibregl-ctrl-attrib")).toContainText("地理院");
  expect(blockedHits).toEqual([]);
});

test("zooming past the raster ceilings produces no failed tile requests", async ({ page }) => {
  const failures: string[] = [];
  page.on("response", (response) => {
    if (response.url().includes("cyberjapandata.gsi.go.jp/xyz/") && response.status() >= 400) failures.push(response.url());
  });

  await waitForMap(page);
  await page.locator(".basemap-button", { hasText: "影像" }).click();
  // Photo tiles cap at z18; ride the camera to its maximum and let overscale
  // take over. MapLibre disables the control at maxZoom — stop there.
  for (let index = 0; index < 4; index += 1) {
    try {
      await page.locator(".maplibregl-ctrl-zoom-in").click({ timeout: 1500 });
    } catch {
      break; // the control disables itself at maxZoom
    }
    await page.waitForTimeout(400);
  }
  await page.locator(".basemap-button", { hasText: "坡度" }).click();
  await page.waitForTimeout(800);
  expect(failures).toEqual([]);
});
