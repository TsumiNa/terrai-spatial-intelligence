import AxeBuilder from "@axe-core/playwright";
import { expect, test, type Page } from "@playwright/test";
import { open, openAudit, WIDE } from "./support/ui";

/** Accessibility baseline.
 *
 *  This stage records what is wrong rather than demanding it be fixed. The
 *  value is the regression net: a new violation fails, and so does fixing an
 *  old one, which forces the list below to stay honest.
 *
 *  Two groups, with different owners:
 *
 *  - The recorded violations are pre-existing and none are fixed by this
 *    refactor. `color-contrast` is a palette problem and belongs to whoever
 *    revisits the tokens; `nested-interactive` is a markup problem in the queue.
 *    Both are logged here so they cannot grow unnoticed.
 *  - The drawer's structural defects are marked `test.fail()`. They are fixed in
 *    stage 05, and Playwright will report "expected to fail but passed" the
 *    moment they are, which is the signal to delete the annotation.
 *
 *  The map canvas is excluded throughout: MapLibre and deck.gl own that markup.
 */

/** Violations present on `main` when this baseline was taken.
 *
 *  Asserted as an exact set of rule ids plus a ceiling on total nodes, rather
 *  than an exact node count per rule. The counts are not portable: macOS
 *  reports 14 `color-contrast` nodes and the Linux runner reports 15, because
 *  the font stack falls back differently and one label lands on the other side
 *  of the size threshold axe uses. A check that goes red for that reason is one
 *  people stop believing.
 *
 *  What survives the relaxation is what matters: a violation of a **new kind**
 *  fails, and violations **multiplying** fails. What is lost is that fixing one
 *  no longer fails, so the ceilings can drift below reality — the id list is the
 *  part that keeps this honest, since removing a category does fail.
 *
 *  `aria-hidden-focus` appears only while the drawer is closed: it carries
 *  `aria-hidden="true"` over a focusable close button, which is defect 4 in the
 *  plan. It disappears when open because the attribute is toggled off.
 */
const CLOSED_BASELINE = {
  ids: ["aria-hidden-focus", "color-contrast", "nested-interactive"],
  maxNodes: 34,
};

const OPEN_BASELINE = {
  ids: ["color-contrast", "nested-interactive"],
  maxNodes: 33,
};

type Scan = { ids: string[]; nodes: number };

async function scan(page: Page): Promise<Scan> {
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"])
    .exclude("#map")
    .analyze();
  return {
    ids: result.violations.map((v) => v.id).sort(),
    nodes: result.violations.reduce((total, v) => total + v.nodes.length, 0),
  };
}

test("the closed exhibition matches its recorded violations", async ({ page }) => {
  await page.setViewportSize(WIDE);
  await open(page, { module: "slope" });
  const result = await scan(page);
  expect(result.ids).toEqual(CLOSED_BASELINE.ids);
  expect(result.nodes).toBeLessThanOrEqual(CLOSED_BASELINE.maxNodes);
});

test("the open audit drawer matches its recorded violations", async ({ page }) => {
  await page.setViewportSize(WIDE);
  await open(page, { module: "slope" });
  await openAudit(page);
  const result = await scan(page);
  expect(result.ids).toEqual(OPEN_BASELINE.ids);
  expect(result.nodes).toBeLessThanOrEqual(OPEN_BASELINE.maxNodes);
});

// --- Defects stage 05 removes -------------------------------------------------
// Each is a real failure today. Delete the annotation when the dialog primitive
// lands; Playwright fails a `test.fail()` that passes, so it cannot be forgotten.

test("the open audit drawer is announced as a modal dialog", async ({ page }) => {
  test.fail(true, "fixed in stage 05: the drawer is an <aside>, not a dialog");
  await page.setViewportSize(WIDE);
  await open(page, { module: "slope" });
  await openAudit(page);

  const drawer = page.locator(".audit-drawer");
  await expect(drawer).toHaveAttribute("role", "dialog");
  await expect(drawer).toHaveAttribute("aria-modal", "true");
});

test("focus stays inside the open audit drawer", async ({ page }) => {
  test.fail(true, "fixed in stage 05: there is no focus trap");
  await page.setViewportSize(WIDE);
  await open(page, { module: "slope" });
  await openAudit(page);

  // Walk further than the drawer has focusable elements.
  for (let step = 0; step < 12; step++) {
    await page.keyboard.press("Tab");
    const inside = await page.evaluate(
      () => !!document.activeElement?.closest(".audit-drawer"),
    );
    expect(inside, `focus left the drawer after ${step + 1} tabs`).toBe(true);
  }
});

test("the background is hidden from assistive technology while the drawer is open", async ({
  page,
}) => {
  test.fail(true, "fixed in stage 05: aria-hidden sits on the drawer, not the background");
  await page.setViewportSize(WIDE);
  await open(page, { module: "slope" });
  await openAudit(page);

  const shellHidden = await page.evaluate(() => {
    const shell = document.querySelector(".app-shell");
    return shell?.getAttribute("aria-hidden") === "true" || shell?.hasAttribute("inert");
  });
  expect(shellHidden).toBe(true);
});
