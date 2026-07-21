import { expect, test } from "@playwright/test";
import { mask, NARROW, open, openAudit, WIDE } from "./support/ui";

/** Visual baseline for the styling refactor.
 *
 *  These images exist to prove that stages 02-05 changed nothing they did not
 *  intend to. They are scaffolding with a known expiry: when the applications
 *  are redesigned, the baselines are regenerated wholesale and the diff is the
 *  artefact under review. During the refactor itself, a diff is a defect.
 *
 *  Coverage is deliberately not exhaustive. Every module is captured once,
 *  because per-module chrome differs; the language and viewport axes are
 *  captured on the densest module only, because 8 x 3 x 2 images cost more to
 *  maintain than they catch.
 */

const MODULES = [
  "overview",
  "evidence",
  "slope",
  "roads",
  "facilities",
  "solar",
  "joint",
  "development",
] as const;

// The module with the most text, so translation length has somewhere to show.
const DENSEST = "evidence";

test.describe("every module", () => {
  for (const module of MODULES) {
    test(`${module} renders its chrome`, async ({ page }) => {
      await page.setViewportSize(WIDE);
      await open(page, { module });
      await expect(page).toHaveScreenshot(`module-${module}.png`, { mask: mask(page) });
    });
  }
});

test.describe("translation length", () => {
  for (const lang of ["zh", "ja", "en"] as const) {
    test(`${DENSEST} in ${lang} fits its layout`, async ({ page }) => {
      await page.setViewportSize(WIDE);
      await open(page, { module: DENSEST, lang });
      await expect(page).toHaveScreenshot(`lang-${lang}.png`, { mask: mask(page) });
    });
  }
});

test.describe("narrow viewport", () => {
  // English is the longest of the three, so it is the one that overflows first.
  test("the shell reflows without clipping its longest labels", async ({ page }) => {
    await page.setViewportSize(NARROW);
    await open(page, { module: DENSEST, lang: "en" });
    await expect(page).toHaveScreenshot("narrow-en.png", { mask: mask(page) });
  });
});

test.describe("audit drawer", () => {
  // The component the styling refactor is most likely to break, and the one
  // whose overlay is replaced outright in stage 05.
  test("open drawer keeps its provenance layout", async ({ page }) => {
    await page.setViewportSize(WIDE);
    await open(page, { module: "slope" });
    await openAudit(page);
    await expect(page).toHaveScreenshot("audit-open.png", { mask: mask(page) });
  });

  test("open drawer in English", async ({ page }) => {
    await page.setViewportSize(WIDE);
    await open(page, { module: "slope", lang: "en" });
    await openAudit(page);
    await expect(page).toHaveScreenshot("audit-open-en.png", { mask: mask(page) });
  });
});
