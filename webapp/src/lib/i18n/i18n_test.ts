import { expect, it } from "vitest";

import { en, ja, zh } from "./messages";
import { format, isLanguage } from "./i18n.svelte";

it("substitutes named placeholders", () => {
  expect(format("{n} groups", { n: 6 })).toBe("6 groups");
  expect(format("{ha} ha · slope {slope}°", { ha: "2.2", slope: 14 })).toBe("2.2 ha · slope 14°");
});

it("returns the template untouched without params", () => {
  expect(format("Data checked")).toBe("Data checked");
});

it("replaces every occurrence of a repeated placeholder", () => {
  expect(format("{x} and {x}", { x: "a" })).toBe("a and a");
});

it("keeps catalog key sets identical across the three languages", () => {
  // The type annotations already fail the build on drift; this guards the
  // runtime artifact so a type-cast regression cannot slip through.
  expect(Object.keys(zh).sort()).toEqual(Object.keys(en).sort());
  expect(Object.keys(ja).sort()).toEqual(Object.keys(en).sort());
});

it("keeps placeholders consistent between translations", () => {
  const names = (text: string) => (text.match(/\{[a-zA-Z]+\}/g) ?? []).sort();
  for (const key of Object.keys(en) as (keyof typeof en)[]) {
    expect(names(zh[key]), `zh ${key}`).toEqual(names(en[key]));
    expect(names(ja[key]), `ja ${key}`).toEqual(names(en[key]));
  }
});

it("accepts only known languages", () => {
  expect(isLanguage("zh")).toBe(true);
  expect(isLanguage("ja")).toBe(true);
  expect(isLanguage("en")).toBe(true);
  expect(isLanguage("fr")).toBe(false);
  expect(isLanguage(null)).toBe(false);
});
