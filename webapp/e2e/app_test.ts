import { expect, test } from "@playwright/test";

const API = "http://127.0.0.1:8000/api/v1";

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.locator(".metrics .metric").first()).toBeVisible({ timeout: 15000 });
});

test("navigation switches modules and deep-links the URL", async ({ page }) => {
  await page.locator('[data-module="slope"]').click();
  await expect(page.locator("h1")).toHaveText("建筑级坡地暴露筛查");
  await expect(page).toHaveURL(/module=slope/);
  await expect(page.locator(".queue-item").first()).toBeVisible();

  await page.locator('[data-module="evidence"]').click();
  await expect(page.locator("h1")).toHaveText("验证每个结果背后的数据");
  await expect(page.locator(".view-tab")).toHaveCount(4);
});

test("language switching changes visible text without reload", async ({ page }) => {
  await expect(page.locator("h1")).toHaveText("城市韧性与新能源机会");
  await page.locator('.language-button[lang="en"]').click();
  await expect(page.locator("h1")).toHaveText("Urban resilience and renewable opportunities");
  await expect(page.locator(".panel-head h3")).toHaveText("Yokohama hub queue");
  await page.locator('.language-button[lang="ja"]').click();
  await expect(page.locator("h1")).toHaveText("都市レジリエンスと再エネ機会");
  await expect(page.locator(".nav-item", { hasText: "建物斜面リスク" })).toBeVisible();
});

test("the queue preserves the server ranking exactly", async ({ page }) => {
  await page.locator('[data-module="slope"]').click();
  await expect(page.locator(".queue-item").first()).toBeVisible();
  const shown = await page.locator(".queue-item .score").allInnerTexts();
  const values = shown.map((item) => Number(item.split("\n")[0]));

  const response = await page.request.get(`${API}/recommendations/slope`);
  const payload = await response.json();
  const expected = payload.features
    .slice(0, values.length)
    .map((feature: { properties: { risk_score: number } }) => feature.properties.risk_score);
  expect(values).toEqual(expected);
});

test("opening an audit record shows its provenance end to end", async ({ page }) => {
  await page.locator(".metric-value .audit-trigger").first().click();
  const drawer = page.locator(".audit-drawer");
  await expect(drawer).toHaveClass(/open/);
  // The first overview metric is a count calculation: formula, inputs, lineage.
  await expect(drawer.locator(".audit-section")).toHaveCount(3);
  await expect(drawer.locator(".audit-section").nth(2)).toContainText("building_risk.geojson");
  await expect(drawer.locator(".audit-caveat p")).not.toBeEmpty();
  await page.keyboard.press("Escape");
  // The dialog primitive unmounts on close rather than toggling a class, so
  // "gone" is the assertion now — and a stronger one than "unclassed".
  await expect(drawer).toHaveCount(0);
});
