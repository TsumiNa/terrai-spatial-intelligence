/** Rejects colours written outside the palette.
 *
 *  The lock is on the palette, not the geometry. A colour outside the palette
 *  fragments the brand, is where a model most plausibly invents a near miss,
 *  and carries a contrast risk. A radius or a spacing step is a judgement with
 *  no correctness dimension, so `p-[13px]` and `rounded-[7px]` are legitimate
 *  and this must not touch them.
 *
 *  Two more things it must not touch, both of which a naive rule would break:
 *
 *  - **Arbitrary variants.** `data-[state=open]:` and `aria-[expanded=true]:`
 *    select a state rather than carry a value, and the dialog primitive coming
 *    in stage 05 requires them. A variant is everything before the final `:`;
 *    the rule reads only what follows.
 *  - **Interpolated values.** `style={`background:${item.color}`}` passes a
 *    colour that came from the palette through a data path. The literal is what
 *    matters, not the property.
 */

/** Utilities whose arbitrary value is a colour rather than a measurement. */
const COLOUR_UTILITIES = [
  "bg",
  "text",
  "border",
  "outline",
  "ring",
  "fill",
  "stroke",
  "decoration",
  "divide",
  "accent",
  "caret",
  "shadow",
  "from",
  "via",
  "to",
];

/** A hand-written colour, as opposed to a reference to one.
 *
 *  The function forms must be followed by a digit: `rgba(palette.red, 0.2)` is
 *  a call passing a palette entry, while `rgba(215, 91, 76, 1)` is a literal.
 *  Matching the bare function name flagged every use of this project's own
 *  `rgba` helper, which is how colours reach deck.gl.
 */
const COLOUR_LITERAL = /#[0-9a-fA-F]{3,8}\b|\b(?:rgba?|hsla?|oklch|lab)\(\s*[\d.]/;

const CLASS_ATTRIBUTE = /class(?:Name)?\s*=\s*(?:"([^"]*)"|'([^']*)'|\{`([^`]*)`\})/g;
const STYLE_BLOCK = /<style[^>]*>([\s\S]*?)<\/style>/g;

export type Violation = { file: string; value: string; reason: string };

/** A colour named in a comment is not a colour being used, and this file's own
 *  patterns would otherwise trip it. */
function withoutComments(source: string): string {
  return source.replace(/\/\*[\s\S]*?\*\//g, "").replace(/^\s*\/\/.*$/gm, "");
}

/** The utility is what follows the final `:`; everything before it is a variant. */
function utility(className: string): string {
  const parts = className.split(":");
  return parts[parts.length - 1] ?? className;
}

function arbitraryColourUtilities(source: string): string[] {
  const found: string[] = [];
  for (const match of source.matchAll(CLASS_ATTRIBUTE)) {
    const value = match[1] ?? match[2] ?? match[3] ?? "";
    for (const className of value.split(/\s+/).filter(Boolean)) {
      const util = utility(className);
      const bracket = util.indexOf("-[");
      if (bracket < 0) continue;
      const prefix = util.slice(0, bracket).replace(/^-/, "");
      const inner = util.slice(bracket + 2, util.lastIndexOf("]"));
      if (!COLOUR_UTILITIES.includes(prefix)) continue;
      // `shadow-[0_2px_4px]` is geometry; `shadow-[#000]` is colour.
      if (!COLOUR_LITERAL.test(inner)) continue;
      found.push(className);
    }
  }
  return found;
}

function literalsInStyleBlocks(source: string): string[] {
  const found: string[] = [];
  for (const block of source.matchAll(STYLE_BLOCK)) {
    for (const line of withoutComments(block[1] ?? "").split("\n")) {
      // An interpolated value carries a palette colour through a data path.
      if (line.includes("${") || line.includes("var(--")) continue;
      const match = line.match(COLOUR_LITERAL);
      if (match) found.push(line.trim());
    }
  }
  return found;
}

/** Colour literals are declared in one file; everywhere else imports from it. */
export const PALETTE_SOURCE = "src/lib/theme.ts";

export function inspect(file: string, source: string): Violation[] {
  const violations: Violation[] = [];

  for (const value of arbitraryColourUtilities(source)) {
    violations.push({ file, value, reason: "arbitrary colour utility" });
  }

  if (file.endsWith(".svelte")) {
    for (const value of literalsInStyleBlocks(source)) {
      violations.push({ file, value, reason: "colour literal in a style block" });
    }
  }

  if (file.endsWith(".ts") && !file.endsWith(PALETTE_SOURCE) && !file.endsWith("_test.ts")) {
    for (const line of withoutComments(source).split("\n")) {
      if (!COLOUR_LITERAL.test(line)) continue;
      violations.push({ file, value: line.trim(), reason: `colour literal outside ${PALETTE_SOURCE}` });
    }
  }

  return violations;
}
