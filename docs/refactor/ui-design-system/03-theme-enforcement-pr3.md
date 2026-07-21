# PR3 Plan: Theme Enforcement

- Status: Completed
- Refactor: `ui-design-system`
- PR: #3

## Goal

Make an off-system value fail a check rather than merge. Without this stage, the locked theme is a convention, and a convention does not survive code written faster than it is read.

## Scope

1. A check that scans every `.svelte` file and rejects **off-palette colours**:
   - arbitrary colour utilities — `bg-[#1f7a58]`, `text-[rgb(20,30,40)]`, `border-[hsl(...)]`;
   - raw colour literals in `<style>` blocks and inline styles.

   It must **not** reject arbitrary geometry — `p-[13px]`, `rounded-[7px]`, `w-[238px]`, `gap-[5px]`. Those are judgements, not defects, and rejecting them would both flatten the design and be impossible to satisfy: 63% of the pixel values in `app.css` are not multiples of four, so the existing design cannot be expressed on any regular scale.

   It must **not** reject **arbitrary variants** — `data-[state=open]:`, `aria-[expanded=true]:`, `supports-[...]:`. These carry no design value; they select a state. The dialog and popover primitives adopted in stage 05 require them, so a rule written as "reject anything containing `-[`" would block the exact components this refactor is adding.

   The distinction is positional, not textual: a variant is everything before the final `:` in a class, the utility is what follows it. Apply the rule to the utility only. In `data-[state=open]:bg-forest`, `data-[state=open]` is a variant and `bg-forest` is the utility; in `data-[state=open]:bg-[#1f7a58]` the same variant is fine and `bg-[#1f7a58]` is the violation.
2. Wire it into the same command contributors already run, so it fails in the place they already look.
3. Document the rule in `AGENTS.md` beside the other executable contracts, including how to add a token when one is genuinely needed.
4. **Give TypeScript a single colour source.** Found while implementing: `.svelte` files contain no colour literals at all, but fifteen were scattered through `modules.ts` and `style-rules.ts`, because the map needs numeric values. Nine were off-palette, and `lime` had drifted to mean two different greens. A check that scanned only Svelte would have missed the majority of this product's colour.
4. Tests that confirm the check catches each violation class, verified by injecting one and watching it fail.

## Non-goals

No styling change. No opinion on class ordering or formatting — this is about values, not aesthetics. No blanket ban on inline styles: computed positioning for map overlays is legitimate and must stay possible.

## Implementation notes

- **Resolved: it lives in the JavaScript toolchain**, as a vitest suite next to the files it inspects, so it runs on `npm run test` and in the Web app CI job. `terrai validate` was the alternative, but parsing Svelte from Python puts the feedback in the wrong loop for frontend work.
- Three false-positive classes were found and fixed while implementing, each of which would have made the rule untrustworthy: it flagged colours named in **comments**, it flagged this project's own **`rgba()` helper** because the pattern matched the bare function name, and it flagged the **fixtures in its own test**. A rule that cries wolf gets disabled.
- An escape hatch will be needed eventually. Prefer one that is visible in review — a named exception list in one file, not a comment that can be sprinkled anywhere.
- The check must not fire on the map libraries' own class names, which this project does not control.

## Acceptance

- Injecting `bg-[#ff0000]` into any component fails the check with a message naming the file and the value.
- `p-[13px]` and `rounded-[7px]` pass, proving the rule distinguishes palette from geometry.
- `data-[state=open]:bg-forest` passes, and `data-[state=open]:bg-[#ff0000]` fails, proving the rule reads the utility rather than the whole class.
- Injecting a raw hex into a component `<style>` block fails likewise.
- The current tree passes with no exceptions needed, or with exceptions that are individually justified in review.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
