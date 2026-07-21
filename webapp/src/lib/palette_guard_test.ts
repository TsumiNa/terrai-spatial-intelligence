import { readFileSync } from "node:fs";
import { join } from "node:path";
import { describe, expect, it } from "vitest";
import { inspect, PALETTE_SOURCE, type Violation } from "./palette_guard";
import { palette } from "./theme";

const ROOT = new URL("../..", import.meta.url).pathname;

async function sourceFiles(): Promise<string[]> {
  const { globSync } = await import("node:fs");
  return globSync("src/**/*.{svelte,ts}", { cwd: ROOT }).map((p: string) => p.replace(/\\/g, "/"));
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
  it("has no colour written outside the palette", async () => {
    // Test files are skipped: this one necessarily contains the violations it
    // asserts are caught, and a fixture is not a use.
    const files = (await sourceFiles()).filter((file) => !file.endsWith("_test.ts"));
    const violations = files.flatMap((file) => inspect(file, readFileSync(join(ROOT, file), "utf8")));
    expect(violations).toEqual([]);
  });

  it("scans the files that matter", async () => {
    const files = (await sourceFiles()).filter((file) => !file.endsWith("_test.ts"));
    expect(files).toContain("src/lib/map/style-rules.ts");
    expect(files).toContain("src/lib/components/AuditDrawer.svelte");
    expect(files.length).toBeGreaterThan(15);
  });

  it("declares every palette entry as a CSS token, so the two cannot drift", () => {
    const css = readFileSync(join(ROOT, "src/app.css"), "utf8");
    const declared = new Set(
      [...css.matchAll(/--color-[a-z-]+:\s*(#[0-9a-fA-F]{3,8})/g)].map((m) => m[1]!.toLowerCase()),
    );
    const missing = Object.entries(palette)
      .filter(([, value]) => !declared.has(value.toLowerCase()))
      .map(([name, value]) => `${name} (${value})`);
    expect(missing).toEqual([]);
  });
});
