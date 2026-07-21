import { expect, test, type Page } from "@playwright/test";

async function waitForApp(page: Page) {
  await page.goto("/");
  await expect(page.locator(".metrics .metric").first()).toBeVisible({ timeout: 15000 });
  await expect(page.locator("#map .maplibregl-canvas")).toBeVisible({ timeout: 20000 });
}

const MODULES = [
  { module: "overview", eyebrow: "社区光储韧性枢纽" },
  { module: "evidence", eyebrow: "Satellite Embedding 年度变化" },
  { module: "slope", eyebrow: "坡地暴露" },
  { module: "roads", eyebrow: "道路韧性" },
  { module: "facilities", eyebrow: "横滨市官方地域防灾拠点" },
  { module: "solar", eyebrow: "光伏选址单元" },
  { module: "joint", eyebrow: "社区光储韧性枢纽" },
  { module: "development", eyebrow: "可交付光伏单元" },
];

test("a queue selection frames its feature and its popup reaches an audit record, per module", async ({ page }) => {
  test.setTimeout(120000);
  await waitForApp(page);
  for (const { module, eyebrow } of MODULES) {
    if (module !== "overview") {
      await page.locator(`[data-module="${module}"]`).click();
      await expect(page.locator(".queue-item").first()).toBeVisible();
    }
    await page.locator(".queue-item").first().locator(".rank").click();
    const popup = page.locator(".maplibregl-popup");
    await expect(popup, module).toBeVisible();
    await expect(popup.locator(".popup-eyebrow"), module).toHaveText(eyebrow);

    await popup.locator(".audit-trigger").first().click();
    await expect(page.locator(".audit-drawer"), module).toHaveClass(/open/);
    await expect(page.locator(".audit-drawer .audit-caveat p"), module).not.toBeEmpty();
    await page.keyboard.press("Escape");
    await expect(page.locator(".audit-drawer"), module).not.toHaveClass(/open/);
  }
});

test("clicking a feature on the map opens its popup through deck picking", async ({ page }) => {
  await waitForApp(page);
  await page.locator('[data-module="slope"]').click();
  await expect(page.locator(".queue-item").first()).toBeVisible();
  await page.locator(".queue-item").first().locator(".rank").click();
  await expect(page.locator(".maplibregl-popup")).toBeVisible();
  await page.locator(".maplibregl-popup-close-button").click();
  await expect(page.locator(".maplibregl-popup")).toHaveCount(0);
  await page.waitForTimeout(1500); // let the framing animation settle

  const box = await page.locator("#map").boundingBox();
  await page.mouse.click(box!.x + box!.width / 2, box!.y + box!.height / 2);
  await expect(page.locator(".maplibregl-popup .popup-eyebrow")).toHaveText("坡地暴露", { timeout: 5000 });
});
