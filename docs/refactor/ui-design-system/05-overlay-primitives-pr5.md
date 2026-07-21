# PR5 Plan: Overlay Primitives

- Status: Completed
- Refactor: `ui-design-system`
- PR: #5

## Goal

Replace the hand-rolled audit drawer overlay with a real dialog primitive, fixing four accessibility defects that a code review would not catch, and prove it with assertions rather than inspection.

## Scope

1. Add `bits-ui`, pinned to an exact version, and use **only its Dialog**. Popover, Select, Tooltip and Dropdown are named in the overview as the primitives worth taking *eventually*; none of them is in this stage, and each waits for a component that actually needs it.
2. Add `@internationalized/date`, which `bits-ui` declares as a peer dependency and which this repository does not yet have. Adding a peer dependency is not optional even when the primitive in use does not exercise it.
3. Wrap the Dialog in a thin local component styled from the theme. Bits UI ships unstyled, so there is nothing to strip — but the wrapper is the seam that keeps primitive choice separate from appearance.
4. Rebuild `AuditDrawer` on that wrapper, fixing:
   - the missing focus trap;
   - `aria-hidden` sitting on the drawer rather than the background;
   - the absent `role="dialog"` and `aria-modal="true"`;
   - focus being moved into an `aria-hidden` subtree.
5. Delete the hand-rolled focus and return-focus handling that the primitive now owns.
6. Delete the three `test.fail()` annotations in `a11y_test.ts`, which Playwright will demand once the defects are gone, and drop `aria-hidden-focus` from the recorded baseline.

## Non-goals

No primitive beyond Dialog, and no decorative components. Cards, badges, separators and alerts stay local markup. No visual change to the drawer.

## Implementation notes

- Bits UI does not require Tailwind, so this stage stays independent of the styling decision in stage 02.
- Pin the version. Receiving upstream accessibility fixes is the reason for the dependency, but an upgrade can also move behaviour, so it should be a deliberate act with the baselines rerun.
- Escape-to-close, click-outside-to-close and focus return already work; the primitive must preserve them, not merely replace them.
- The drawer holds long trilingual prose. Check scrolling and focus order with the longest Japanese and English content, not the shortest.

## Findings

- **The primitive confines assistive technology with `aria-modal="true"`, not by marking the background.** The stage-01 test demanded `aria-hidden` or `inert` on the app shell, which encoded a technique rather than an outcome — marking siblings is the fallback for assistive technology that does not support `aria-modal`. The assertion now checks the outcome: modal semantics, a focus trap, and a covering overlay. axe reports no violations in the open state.
- **`Dialog.Title` renders a `div` with `role="heading"` by default**, which `.audit-head h2` does not match, so the title silently dropped from 20px to 16px. Caught by the screenshot baseline, not by review. It renders a real `<h2>` through the `child` snippet now.
- **Two pre-existing tests asserted the old mechanism** — that `.audit-drawer` loses its `open` class. The primitive unmounts instead, so they assert absence now, which is the stronger claim.

## Acceptance

- The four defects are gone, each asserted by an axe or Playwright check rather than by reading the markup.
- Escape, click-outside and focus return behave as before.
- Stage 01 screenshots of the drawer are unchanged.
- Only behaviour-hard primitives are used; no decorative component was adopted.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
