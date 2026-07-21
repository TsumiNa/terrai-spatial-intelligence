# PR5 Plan: Overlay Primitives

- Status: Planned
- Refactor: `ui-design-system`
- PR: #5

## Goal

Replace the hand-rolled audit drawer overlay with a real dialog primitive, fixing four accessibility defects that a code review would not catch, and prove it with assertions rather than inspection.

## Scope

1. Add `bits-ui` and use **only** the primitives actually needed now. Dialog is required; Popover, Select, Tooltip and Dropdown come in only when a component needs them.
2. Wrap each in a thin local component styled from the theme. Bits UI ships unstyled, so there is nothing to strip — but the wrapper is the seam that keeps primitive choice separate from appearance.
3. Rebuild `AuditDrawer` on Dialog, fixing:
   - the missing focus trap;
   - `aria-hidden` sitting on the drawer rather than the background;
   - the absent `role="dialog"` and `aria-modal="true"`;
   - focus being moved into an `aria-hidden` subtree.
4. Delete the hand-rolled focus and return-focus handling that the primitive now owns.
5. Turn the stage 01 axe baseline from "recorded" into "asserted" for the states now fixed.

## Non-goals

No decorative components, and no component library beyond the primitives. Cards, badges, separators and alerts stay local markup. No visual change to the drawer.

## Implementation notes

- Bits UI does not require Tailwind, so this stage stays independent of the styling decision in stage 02.
- Pin the version. Receiving upstream accessibility fixes is the reason for the dependency, but an upgrade can also move behaviour, so it should be a deliberate act with the baselines rerun.
- Escape-to-close, click-outside-to-close and focus return already work; the primitive must preserve them, not merely replace them.
- The drawer holds long trilingual prose. Check scrolling and focus order with the longest Japanese and English content, not the shortest.

## Acceptance

- The four defects are gone, each asserted by an axe or Playwright check rather than by reading the markup.
- Escape, click-outside and focus return behave as before.
- Stage 01 screenshots of the drawer are unchanged.
- Only behaviour-hard primitives are used; no decorative component was adopted.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
