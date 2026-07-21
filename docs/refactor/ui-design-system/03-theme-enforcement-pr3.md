# PR3 Plan: Theme Enforcement

- Status: Planned
- Refactor: `ui-design-system`
- PR: #3

## Goal

Make an off-system value fail a check rather than merge. Without this stage, the locked theme is a convention, and a convention does not survive code written faster than it is read.

## Scope

1. A check that scans every `.svelte` file and rejects:
   - **arbitrary utility values** — `bg-[#1f7a58]`, `p-[13px]`, `w-[238px]`, `text-[14px]`;
   - raw colour literals in `<style>` blocks and inline styles, where a token exists.

   It must **not** reject **arbitrary variants** — `data-[state=open]:`, `aria-[expanded=true]:`, `supports-[...]:`. These carry no design value; they select a state. The dialog and popover primitives adopted in stage 05 require them, so a rule written as "reject anything containing `-[`" would block the exact components this refactor is adding.

   The distinction is positional, not textual: a variant is everything before the final `:` in a class, the utility is what follows it. Apply the rule to the utility only. In `data-[state=open]:bg-forest`, `data-[state=open]` is a variant and `bg-forest` is the utility; in `data-[state=open]:bg-[#1f7a58]` the same variant is fine and `bg-[#1f7a58]` is the violation.
2. Wire it into the same command contributors already run, so it fails in the place they already look.
3. Document the rule in `AGENTS.md` beside the other executable contracts, including how to add a token when one is genuinely needed.
4. Tests that confirm the check catches each violation class, verified by injecting one and watching it fail.

## Non-goals

No styling change. No opinion on class ordering or formatting — this is about values, not aesthetics. No blanket ban on inline styles: computed positioning for map overlays is legitimate and must stay possible.

## Implementation notes

- Decide where this lives. Open question 3 in the overview: the JavaScript toolchain is where the files are, but `terrai validate` is where this repository's other executable contracts already live, and contributors already run it. Either is defensible; record which and why.
- An escape hatch will be needed eventually. Prefer one that is visible in review — a named exception list in one file, not a comment that can be sprinkled anywhere.
- The check must not fire on the map libraries' own class names, which this project does not control.

## Acceptance

- Injecting `bg-[#ff0000]` into any component fails the check with a message naming the file and the value.
- `data-[state=open]:bg-forest` passes, and `data-[state=open]:bg-[#ff0000]` fails, proving the rule reads the utility rather than the whole class.
- Injecting a raw hex into a component `<style>` block fails likewise.
- The current tree passes with no exceptions needed, or with exceptions that are individually justified in review.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
