import { expect, test } from "@playwright/test";

test("the built shell loads against the live API", async ({ page }) => {
  await page.goto("/");
  await expect(page).toHaveTitle(/TerrAI Spatial Intelligence/);
  await expect(page.locator(".brand strong")).toHaveText("TerrAI");
  await expect(page.locator(".metrics .metric").first()).toBeVisible({ timeout: 15000 });
});
