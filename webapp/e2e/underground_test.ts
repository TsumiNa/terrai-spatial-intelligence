import { expect, test, type Page } from "@playwright/test";

/**
 * CI has no PLATEAU tile cache, so the unconditional assertions cover the
 * honest unavailable state; the cache-dependent assertions run only where
 * `/catalog` reports the dataset ready (a developer machine after
 * `terrai fetch underground_utilities`).
 */

async function undergroundReady(page: Page): Promise<boolean> {
  const response = await page.request.get("http://127.0.0.1:8000/api/v1/catalog");
  const rows = (await response.json()).datasets as { key: string; ready: boolean }[];
  return rows.find((row) => row.key === "uc24_16_nihonbashi")?.ready ?? false;
}

async function openUnderground(page: Page) {
  await page.goto("/?module=underground");
  // Not `.metrics`: the unavailable state renders it empty, and an empty grid
  // has zero height, which Playwright reads as invisible.
  await expect(page.locator(".map-card")).toBeVisible({ timeout: 15000 });
  await expect(page.locator("#map .maplibregl-canvas")).toBeVisible({ timeout: 20000 });
}

test("entering the underground module is one action and leaving restores the surface", async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".metrics .metric").first()).toBeVisible({ timeout: 15000 });
  await page.locator('[data-module="underground"]').click();
  await expect(page.locator("h1")).toHaveText("城市语境中的实测地下管线");
  await expect(page.locator(".region-pill")).toHaveText("东京 · 日本桥");
  // The nationwide live rasters cover every region; nothing disables here.
  await expect(page.locator(".basemap-button", { hasText: "影像" })).toBeEnabled();

  await page.locator('[data-module="overview"]').click();
  await expect(page.locator("h1")).toHaveText("城市韧性与新能源机会");
  await expect(page.locator(".basemap-button", { hasText: "影像" })).toBeEnabled();
});

test("an absent tile cache states unavailability and requests nothing that can fail", async ({ page }) => {
  test.skip(await undergroundReady(page), "cache present: the unavailable state is not reachable");
  const failures: string[] = [];
  page.on("response", (response) => {
    if (response.url().includes("plateau") && response.status() >= 400) failures.push(response.url());
  });
  await openUnderground(page);
  await expect(page.locator('[role="status"]')).toContainText("尚未下载 3D 资产缓存");
  await expect(page.locator('[role="status"]')).toContainText("terrai_spatial fetch underground_utilities");
  expect(failures).toEqual([]);
});

test("the cached scene renders, frames a layer from the inventory, and reaches an audit record", async ({ page }) => {
  test.skip(!(await undergroundReady(page)), "no PLATEAU cache on this runner");
  test.setTimeout(120000);

  const failures: string[] = [];
  page.on("response", (response) => {
    if (response.url().includes("plateau") && response.status() >= 400) failures.push(response.url());
  });

  await openUnderground(page);
  await expect(page.locator(".metrics .metric").first()).toBeVisible();
  await expect(page.locator(".metric").filter({ hasText: "管网要素" })).toContainText("810");
  await expect(page.locator(".queue-item")).toHaveCount(5); // five network layers

  // Queue click frames the resource extent without inventing a popup.
  await page.locator(".queue-item").first().locator(".rank").click();
  await page.waitForTimeout(1500);

  // Deck picking on the network geometry reaches the audit drawer. Zoom to
  // street level first: pipes are decimetres wide and sub-pixel at region
  // scale. Probe a few points; tubes are thin even at maximum zoom.
  for (let index = 0; index < 7; index += 1) {
    try {
      await page.locator(".maplibregl-ctrl-zoom-in").click({ timeout: 1000 });
    } catch {
      break;
    }
    await page.waitForTimeout(300);
  }
  await page.waitForTimeout(3000);
  const box = (await page.locator("#map").boundingBox())!;
  let picked = false;
  for (const [fx, fy] of [[0.5, 0.5], [0.45, 0.55], [0.35, 0.6], [0.55, 0.62], [0.6, 0.45]]) {
    await page.mouse.click(box.x + box.width * fx, box.y + box.height * fy);
    await page.waitForTimeout(900);
    if (await page.locator(".maplibregl-popup").isVisible().catch(() => false)) {
      picked = true;
      break;
    }
  }
  expect(picked, "no network element under any probe point").toBe(true);

  await page.locator(".maplibregl-popup .audit-trigger").first().click();
  const drawer = page.locator('[role="dialog"]');
  await expect(drawer).toBeVisible();
  await expect(drawer).toContainText("audit_index.json");
  await expect(drawer).toContainText("PLATEAU");
  await page.keyboard.press("Escape");
  await expect(drawer).toHaveCount(0);

  expect(failures).toEqual([]);
});
