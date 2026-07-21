import { readdirSync, readFileSync } from "node:fs";
import { join, relative } from "node:path";
import { describe, expect, it } from "vitest";
import { inspect, PALETTE_SOURCE, stylesheetLiterals, type Violation } from "./palette_guard";
import { palette } from "./theme";

const ROOT = new URL("../..", import.meta.url).pathname;

/** Walked by hand rather than with `fs.globSync`, which arrived in Node 22
 *  while `package.json` declares `>=20`. */
function sourceFiles(directory = join(ROOT, "src")): string[] {
  return readdirSync(directory, { withFileTypes: true }).flatMap((entry) => {
    const full = join(directory, entry.name);
    if (entry.isDirectory()) return sourceFiles(full);
    if (!/\.(svelte|ts)$/.test(entry.name)) return [];
    return [relative(ROOT, full).replace(/\\/g, "/")];
  });
}

function check(file: string, source: string): Violation[] {
  return inspect(file, source);
}

describe("what it rejects", () => {
  it("rejects an arbitrary colour utility", () => {
    const found = check("Card.svelte", `<div class="bg-[#1f7a58] p-2"></div>`);
    expect(found).toHaveLength(1);
    expect(found[0]?.reason).toBe("arbitrary colour utility");
  });

  it("rejects arbitrary colour in any colour-carrying utility", () => {
    for (const utility of ["bg", "text", "border", "ring", "fill", "stroke", "from"]) {
      const found = check("C.svelte", `<div class="${utility}-[rgb(1,2,3)]"></div>`);
      expect(found, utility).toHaveLength(1);
    }
  });

  it("rejects a colour literal in a style block", () => {
    const found = check("C.svelte", `<style>.a { color: #ff0000; }</style>`);
    expect(found[0]?.reason).toBe("colour literal in a style block");
  });

  it("rejects a colour literal in TypeScript outside the palette", () => {
    const found = check("src/lib/map/layers.ts", `const c = "#8e5eaa";`);
    expect(found[0]?.reason).toContain(PALETTE_SOURCE);
  });
});

describe("what it must not reject", () => {
  it("allows arbitrary geometry, which is a judgement rather than a defect", () => {
    const source = `<div class="p-[13px] rounded-[7px] w-[238px] gap-[5px] shadow-[0_2px_4px]"></div>`;
    expect(check("C.svelte", source)).toEqual([]);
  });

  it("allows arbitrary variants, which the dialog primitive requires", () => {
    const source = `<div class="data-[state=open]:bg-forest aria-[expanded=true]:text-ink"></div>`;
    expect(check("C.svelte", source)).toEqual([]);
  });

  it("still rejects an arbitrary colour behind an arbitrary variant", () => {
    const found = check("C.svelte", `<div class="data-[state=open]:bg-[#ff0000]"></div>`);
    expect(found).toHaveLength(1);
  });

  it("allows an interpolated colour, which came from the palette through data", () => {
    const source = "<span style={`background:${item.color}`}></span>";
    expect(check("C.svelte", source)).toEqual([]);
  });

  it("allows custom properties in style blocks", () => {
    expect(check("C.svelte", `<style>.a { color: var(--color-ink); }</style>`)).toEqual([]);
  });

  it("allows the palette source to declare literals", () => {
    expect(check(PALETTE_SOURCE, `export const palette = { ink: "#10231e" };`)).toEqual([]);
  });
});

describe("the repository conforms", () => {
  it("has no colour written outside the palette", () => {
    // Test files are skipped: this one necessarily contains the violations it
    // asserts are caught, and a fixture is not a use.
    const files = sourceFiles().filter((file) => !file.endsWith("_test.ts"));
    const violations = files.flatMap((file) => inspect(file, readFileSync(join(ROOT, file), "utf8")));
    expect(violations).toEqual([]);
  });

  it("scans the files that matter", () => {
    const files = sourceFiles().filter((file) => !file.endsWith("_test.ts"));
    expect(files).toContain("src/lib/map/style-rules.ts");
    expect(files).toContain("src/lib/components/AuditDrawer.svelte");
    expect(files.length).toBeGreaterThan(15);
  });

  it("declares every palette entry as the matching CSS token, so the two cannot drift", () => {
    // Asserted by name and value together. Checking only that the value appears
    // somewhere would pass while `lime` and `hub` were swapped, or while a
    // token had been renamed out from under its palette entry.
    const css = readFileSync(join(ROOT, "src/app.css"), "utf8");
    const tokens = new Map(
      [...css.matchAll(/--color-([a-z-]+):\s*(#[0-9a-fA-F]{3,8})/g)].map((m) => [
        m[1]!,
        m[2]!.toLowerCase(),
      ]),
    );
    const kebab = (name: string) => name.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`);

    const wrong = Object.entries(palette)
      .filter(([name, value]) => tokens.get(kebab(name)) !== value.toLowerCase())
      .map(([name, value]) => `--color-${kebab(name)} should be ${value}, is ${tokens.get(kebab(name)) ?? "absent"}`);
    expect(wrong).toEqual([]);
  });
});


/** Colours written by eye in `app.css`, inventoried rather than fixed.
 *
 *  Turning these one-off tints into palette entries would make the palette a
 *  colour dump instead of a design system, and they disappear with the
 *  redesign. Asserted as an exact set so a new one fails — and so does removing
 *  one without updating this list, which keeps the inventory honest.
 *
 *  The first version of this list held 36 entries because the scanner skipped
 *  any line containing a `var()` reference. These rules are written one per
 *  line, so that hid 23 literals sharing a line with a token — including every
 *  `rgba()` overlay. Scanning strips the references instead.
 */
const STYLESHEET_DEBT = [
  "#102b23",
  "#153e30",
  "#153f33",
  "#173b2e",
  "#1b5944",
  "#275f81",
  "#315f4a",
  "#50aa75",
  "#6f5c35",
  "#78978c",
  "#889b94",
  "#8c5c13",
  "#93aaa1",
  "#9eb5ac",
  "#9fb9af",
  "#a9beb5",
  "#a9d96e",
  "#b9cac0",
  "#b9cdc5",
  "#d3e2dc",
  "#dce4df",
  "#dce8e2",
  "#e0ebe6",
  "#e2a43c",
  "#e3ece8",
  "#e7f0f6",
  "#e9f2ec",
  "#eaf0ec",
  "#edf1ee",
  "#eef3ef",
  "#eef4f0",
  "#f2f6f2",
  "#f4f7f3",
  "#f5f8f5",
  "#f6fbf7",
  "#f7f9f7",
  "#f8efdc",
  "#fbf6eb",
  "#fbfcfa",
  "rgba(0,0,0,.12)",
  "rgba(10,36,27,.18)",
  "rgba(12,36,28,.18)",
  "rgba(16,35,30,.9)",
  "rgba(16,43,35,.15)",
  "rgba(16,43,35,.18)",
  "rgba(169,217,110,.12)",
  "rgba(25,55,44,.035)",
  "rgba(255,255,255,.018)",
  "rgba(255,255,255,.025)",
  "rgba(255,255,255,.06)",
  "rgba(255,255,255,.07)",
  "rgba(255,255,255,.08)",
  "rgba(255,255,255,.10)",
  "rgba(255,255,255,.15)",
  "rgba(255,255,255,.16)",
  "rgba(255,255,255,.18)",
  "rgba(255,255,255,.7)",
  "rgba(26,55,45,.04)",
  "rgba(9, 27, 21, .28)",
];

describe("the stylesheet's inherited colour", () => {
  it("has not grown", () => {
    const css = readFileSync(join(ROOT, "src/app.css"), "utf8");
    expect([...new Set(stylesheetLiterals(css))].sort()).toEqual(STYLESHEET_DEBT);
  });

  it("exempts the theme block, which is where colour is supposed to be", () => {
    const source = `@theme { --color-ink: #10231e; }\n.a { color: var(--color-ink); }`;
    expect(stylesheetLiterals(source)).toEqual([]);
  });
});
