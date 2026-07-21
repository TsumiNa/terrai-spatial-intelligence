import { expect, type Locator, type Page } from "@playwright/test";

/** The exhibition drives module, view and language from the URL, so every state
 *  a screenshot needs is reachable without clicking through the app. */
export type UiState = {
  module?: string;
  view?: string;
  lang?: "zh" | "ja" | "en";
};

export const WIDE = { width: 1440, height: 900 };
export const NARROW = { width: 900, height: 1000 };

export function url({ module = "overview", view, lang = "zh" }: UiState): string {
  const params = new URLSearchParams({ module, lang });
  if (view) params.set("view", view);
  return `/?${params.toString()}`;
}

/** Wait until the page has stopped changing on its own.
 *
 *  Screenshots taken before the queue and metrics resolve differ run to run for
 *  reasons that have nothing to do with styling, which is the failure mode that
 *  makes people stop trusting a baseline and start regenerating it reflexively.
 */
export async function settle(page: Page): Promise<void> {
  await expect(page.locator(".metrics .metric").first()).toBeVisible({ timeout: 20000 });
  await expect(page.locator("#map .maplibregl-canvas")).toBeVisible({ timeout: 20000 });
  await page.waitForLoadState("networkidle");
}

/** The map canvas is deliberately excluded from every screenshot.
 *
 *  Tile arrival order, GPU rasterisation and antialiasing all differ between a
 *  developer machine and CI. Map rendering has its own tests; this baseline
 *  protects the chrome, which is what the styling refactor touches.
 */
export function mask(page: Page): Locator[] {
  return [page.locator("#map")];
}

export async function open(page: Page, state: UiState = {}): Promise<void> {
  await page.goto(url(state));
  await settle(page);
}

/** Open the first auditable value on the page and wait for the drawer. */
export async function openAudit(page: Page): Promise<void> {
  await page.locator(".audit-trigger").first().click();
  await expect(page.locator(".audit-drawer.open")).toBeVisible();
  await expect(page.locator("#audit-title")).not.toHaveText("—");
}
