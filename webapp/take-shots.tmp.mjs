import { chromium } from "@playwright/test";

const BASE = "http://127.0.0.1:4300";
const OUT = process.env.OUT;

const browser = await chromium.launch();
const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });

async function settle() {
  await page.locator(".metrics .metric").first().waitFor({ timeout: 20000 });
  await page.locator("#map .maplibregl-canvas").waitFor({ timeout: 20000 });
  await page.waitForLoadState("networkidle");
  await page.waitForTimeout(1200); // let tiles/deck settle for a clean frame
}

async function shot(name) {
  await page.screenshot({ path: `${OUT}/${name}.png` });
  console.log("saved", name);
}

// 1. Decision overview (zh)
await page.goto(`${BASE}/?module=overview&lang=zh`);
await settle();
await shot("01-overview-zh");

// 2. Urban resilience projects (joint)
await page.goto(`${BASE}/?module=joint&lang=zh`);
await settle();
await shot("02-joint");

// 3. Slope module with the Layers control open
await page.goto(`${BASE}/?module=slope&lang=zh`);
await settle();
await page.locator(".foundation-toggle").click();
await page.waitForTimeout(400);
await shot("03-slope-layers-panel");

// 4. Toggle two foundation overlays: land-use mesh + flood history
await page.locator('.foundation-item[data-layer="landUseMesh"]').click();
await page.locator('.foundation-item[data-layer="floodHistory"]').click();
await page
  .locator('.foundation-item[data-layer="landUseMesh"] .foundation-status[data-layer-status="ready"]')
  .waitFor({ timeout: 20000 });
await page
  .locator('.foundation-item[data-layer="floodHistory"] .foundation-status[data-layer-status="ready"]')
  .waitFor({ timeout: 20000 });
await page.waitForTimeout(800);
await shot("04-slope-with-overlays");

// 5. Close the panel; click a foundation feature; open its raw audit record
await page.keyboard.press("Escape");
await page.waitForTimeout(300);
await page.goto(`${BASE}/?module=roads&lang=zh`);
await settle();
await page.locator(".foundation-toggle").click();
await page.locator('.foundation-item[data-layer="landUseMesh"]').click();
await page
  .locator('.foundation-item[data-layer="landUseMesh"] .foundation-status[data-layer-status="ready"]')
  .waitFor({ timeout: 20000 });
await page.keyboard.press("Escape");
await page.waitForTimeout(500);
await page.locator("#map .maplibregl-canvas").click({ position: { x: 520, y: 320 } });
await page.locator(".maplibregl-popup").waitFor({ timeout: 10000 });
await page.locator(".maplibregl-popup .audit-trigger").first().click();
await page.locator(".audit-drawer.open").waitFor({ timeout: 10000 });
await page.waitForTimeout(400);
await shot("05-foundation-audit-record");

// 6. Underground module (Nihonbashi networks on the map)
await page.goto(`${BASE}/?module=underground&lang=zh`);
await page.locator("#map .maplibregl-canvas").waitFor({ timeout: 20000 });
await page.waitForLoadState("networkidle");
await page.waitForTimeout(2500); // lowered camera ease + tiles
await shot("06-underground-networks");

// 7. Box-select into the 3D site scene (demo notice + datum strip visible)
await page.locator(".basemap-button", { hasText: "框选 3D 场景" }).click();
const box = await page.locator("#map").boundingBox();
await page.mouse.move(box.x + box.width * 0.4, box.y + box.height * 0.4);
await page.mouse.down();
await page.mouse.move(box.x + box.width * 0.6, box.y + box.height * 0.6, { steps: 5 });
await page.mouse.up();
await page.locator('[role="dialog"]').waitFor({ timeout: 20000 });
await page.waitForTimeout(3500); // let 3D assets load
await shot("07-scene-viewer");

// 8. Evidence module in English (language + trust view)
await page.goto(`${BASE}/?module=evidence&lang=en`);
await settle();
await shot("08-evidence-en");

await browser.close();
