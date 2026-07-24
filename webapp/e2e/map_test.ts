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
  const spriteResponses: { ok: boolean; origin: string }[] = [];
  const invalidSpriteErrors: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/basemap/sprite/std")) spriteResponses.push({ ok: r.ok(), origin: new URL(r.url()).origin });
  });
  page.on("console", (m) => {
    if (m.text().includes("Invalid sprite URL")) invalidSpriteErrors.push(m.text());
  });

  await waitForMap(page);
  // wait for the sprite to be fetched rather than a fixed timeout
  await expect.poll(() => spriteResponses.length, { timeout: 15000 }).toBeGreaterThan(0);
  const pageOrigin = new URL(page.url()).origin;
  // the absolute URL resolved to our own origin (the fix) and every fetch succeeded…
  expect(spriteResponses.every((s) => s.ok && s.origin === pageOrigin)).toBe(true);
  // …and MapLibre v6 raised no "must be absolute" rejection
  expect(invalidSpriteErrors).toEqual([]);
});

test("basemap switching keeps the single map instance (no camera rebuild)", async ({ page }) => {
  await waitForMap(page);
  const canvas = await page.locator("#map .maplibregl-canvas").elementHandle();
  for (const label of ["影像", "起伏", "标准"]) {
    await page.locator(".basemap-button", { hasText: label }).click();
    await page.waitForTimeout(250);
    expect(await canvas!.evaluate((element) => element.isConnected)).toBe(true);
  }
});

test("the 2.5D toggle tilts every basemap but adds 3D terrain only on imagery/relief", async ({ page }) => {
  const demTiles: string[] = [];
  page.on("response", (r) => {
    // the DEM protocol resolves per tile across dem1a_png / dem5a_png / dem_png
    if (/cyberjapandata\.gsi\.go\.jp\/xyz\/dem[0-9a-z]*_png\//.test(r.url())) demTiles.push(r.url());
  });

  await waitForMap(page);
  // default basemap is standard: 2.5D tilts it (perspective) but adds no terrain,
  // so no DEM tiles are fetched — a warped vector cartographic map reads as noise.
  await page.locator(".view25d-toggle").click();
  await expect(page.locator(".view25d-toggle")).toHaveAttribute("aria-pressed", "true");
  await expect(page).toHaveURL(/[?&]tilt=1/); // deep link reflects the toggle
  await page.waitForTimeout(1500);
  expect(demTiles).toEqual([]);

  // switch to relief: now the 3D DEM surface loads under it
  await page.locator(".basemap-button", { hasText: "起伏" }).click();
  await expect.poll(() => demTiles.length, { timeout: 15000 }).toBeGreaterThan(0);

  // toggle 2.5D off — aria and the deep link both clear
  await page.locator(".view25d-toggle").click();
  await expect(page.locator(".view25d-toggle")).toHaveAttribute("aria-pressed", "false");
  await expect(page).not.toHaveURL(/tilt=1/);
});

test("hillshade shows the colour-by-height tint at wide zoom, only in that mode", async ({ page }) => {
  const reliefTiles: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("cyberjapandata.gsi.go.jp/xyz/relief/")) reliefTiles.push(r.url());
  });

  await waitForMap(page);
  // imagery at a wide view: the tint is bound to the hillshade mode, so nothing
  // requests the colour-by-height raster here even where it would be meaningful.
  await page.locator(".basemap-button", { hasText: "影像" }).click();
  for (let i = 0; i < 8; i += 1) {
    await page.locator(".maplibregl-ctrl-zoom-out").click({ timeout: 1000 }).catch(() => {});
    await page.waitForTimeout(200);
  }
  await page.waitForTimeout(1500);
  expect(reliefTiles).toEqual([]);

  // switch to hillshade at the same wide view: now the tint streams in
  await page.locator(".basemap-button", { hasText: "起伏" }).click();
  await expect.poll(() => reliefTiles.length, { timeout: 15000 }).toBeGreaterThan(0);
});

test("hillshade is computed from the 1m DEM at survey zoom, not the pre-rendered raster", async ({ page }) => {
  const dem1a: string[] = [];
  const hillshademap: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/xyz/dem1a_png/")) dem1a.push(r.url());
    if (r.url().includes("/xyz/hillshademap/")) hillshademap.push(r.url());
  });

  await waitForMap(page); // Yokohama at z16 — a 1m-LiDAR (DEM1A) covered area
  await page.locator(".basemap-button", { hasText: "起伏" }).click();
  // the shaded relief is computed from the 1m LiDAR DEM…
  await expect.poll(() => dem1a.length, { timeout: 15000 }).toBeGreaterThan(0);
  // …and the z16-capped pre-rendered hillshademap raster is retired
  expect(hillshademap).toEqual([]);
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

test("degrades to the production-raster fallback when the vector tiles fail", async ({ page }) => {
  // Only the fallback requests xyz/std — no user basemap uses it.
  const stdTiles: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("cyberjapandata.gsi.go.jp/xyz/std/")) stdTiles.push(r.url());
  });
  // Kill the experimental vector tiles: repeated errors promote the fallback.
  await page.route("**cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/**", (route) => route.abort());

  await waitForMap(page);
  await expect(page.locator(".maplibregl-ctrl-attrib")).toContainText("地理院");
  // the GSI production raster now streams the wide-view streets
  await expect.poll(() => stdTiles.length, { timeout: 30000 }).toBeGreaterThan(0);
});

test("the ops switch (?fallback=raster) starts on the production raster", async ({ page }) => {
  const stdTiles: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("cyberjapandata.gsi.go.jp/xyz/std/")) stdTiles.push(r.url());
  });
  // The operational answer if GSI announces a bvmap change: force the fallback on
  // from the start. Vector tiles are healthy here, so this proves the switch —
  // not a failure — promotes the layer.
  await page.goto("/?fallback=raster");
  await expect(page.locator("#map .maplibregl-canvas")).toBeVisible({ timeout: 20000 });
  await expect.poll(() => stdTiles.length, { timeout: 20000 }).toBeGreaterThan(0);
});

test("leaves the fallback hidden and unrequested in normal operation", async ({ page }) => {
  const stdTiles: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("cyberjapandata.gsi.go.jp/xyz/std/")) stdTiles.push(r.url());
  });
  await waitForMap(page);
  await page.waitForTimeout(2500);
  // vector tiles are healthy, so the fallback never promotes and asks for nothing
  expect(stdTiles).toEqual([]);
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
  await page.locator(".basemap-button", { hasText: "起伏" }).click();
  await page.waitForTimeout(800);
  expect(failures).toEqual([]);
});

test("renders the merged building tiles in coverage, with both credits", async ({ page }) => {
  const pmtiles: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/basemap/buildings.pmtiles")) pmtiles.push(r.url());
  });

  await waitForMap(page);
  // Standard basemap over Mobara (z15, inside coverage, below the z16 handover):
  // the self-built building fabric shows and requests the PMTiles archive.
  await page.locator(".basemap-button", { hasText: "标准" }).click();
  await page.locator(".view-tab", { hasText: "茂原" }).click();

  await expect.poll(() => pmtiles.length, { timeout: 20000 }).toBeGreaterThan(0);
  // No out-of-service badge inside coverage.
  await expect(page.locator(".building-out-of-service")).toHaveCount(0);
  // Every source credit renders wherever the merged fabric shows.
  await expect(page.locator(".maplibregl-ctrl-attrib")).toContainText("OpenStreetMap");
  await expect(page.locator(".maplibregl-ctrl-attrib")).toContainText("基盤地図情報");
  await expect(page.locator(".maplibregl-ctrl-attrib")).toContainText("PLATEAU");
});

test("2.5D extrudes the building fabric without error", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  const pmtiles: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/basemap/buildings.pmtiles")) pmtiles.push(r.url());
  });

  await waitForMap(page);
  await page.locator(".basemap-button", { hasText: "标准" }).click();
  await page.locator(".view-tab", { hasText: "茂原" }).click();
  await expect.poll(() => pmtiles.length, { timeout: 20000 }).toBeGreaterThan(0);
  // Toggle 2.5D: the flat fill yields to the fill-extrusion; the tiles still load
  // and nothing throws (the 3D itself is inside the masked #map canvas).
  await page.locator(".view25d-toggle").click();
  await expect(page.locator(".view25d-toggle")).toHaveAttribute("aria-pressed", "true");
  await page.waitForTimeout(1200);
  expect(errors).toEqual([]);
});

test("the self-built fabric survives the GSI vector host being blocked", async ({ page }) => {
  // Offline proof: kill the experimental vector tiles; the merged building
  // PMTiles is our own asset and must still load, so the buildings do not vanish
  // with GSI's cartography.
  await page.route("**cyberjapandata.gsi.go.jp/xyz/experimental_bvmap/**", (route) => route.abort());
  const pmtiles: string[] = [];
  page.on("response", (r) => {
    if (r.url().includes("/basemap/buildings.pmtiles")) pmtiles.push(r.url());
  });

  await waitForMap(page);
  await page.locator(".basemap-button", { hasText: "标准" }).click();
  await page.locator(".view-tab", { hasText: "茂原" }).click();
  await expect.poll(() => pmtiles.length, { timeout: 20000 }).toBeGreaterThan(0);
});

test("shows the out-of-service badge when panning wholly outside coverage", async ({ page }) => {
  await waitForMap(page);
  await page.locator(".basemap-button", { hasText: "标准" }).click();
  await page.locator(".view-tab", { hasText: "茂原" }).click();
  await expect(page.locator(".building-out-of-service")).toHaveCount(0);

  // Zoom out to ~z13 (still building zoom, but a wide enough viewport that a
  // handful of drags clears the coverage) via the ±1 zoom control.
  for (let i = 0; i < 2; i += 1) {
    await page.locator(".maplibregl-ctrl-zoom-out").click();
    await page.waitForTimeout(300);
  }

  const canvas = page.locator("#map .maplibregl-canvas");
  const box = (await canvas.boundingBox())!;
  const cx = box.x + box.width / 2;
  // Drag the view north (drag the canvas downward) until the viewport clears the
  // coverage's north edge (~36.33) and the fabric goes out of service.
  for (let i = 0; i < 36; i += 1) {
    await page.mouse.move(cx, box.y + box.height * 0.2);
    await page.mouse.down();
    await page.mouse.move(cx, box.y + box.height * 0.85, { steps: 6 });
    await page.mouse.up();
    await page.waitForTimeout(180);
    if (await page.locator(".building-out-of-service").count()) break;
  }
  await expect(page.locator(".building-out-of-service")).toBeVisible();
});
