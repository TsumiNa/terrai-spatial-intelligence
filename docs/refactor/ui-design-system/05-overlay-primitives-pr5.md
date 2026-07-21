# PR5 Plan: Overlay Primitives

- Status: Planned
- Refactor: `ui-design-system`
- PR: #5

## Goal

Replace the hand-rolled audit drawer overlay with a real dialog primitive, fixing four accessibility defects that a code review would not catch, and prove it with assertions rather than inspection.

## Scope

1. Introduce shadcn-svelte and take **only** the behaviour-hard primitives that are actually needed now. Dialog is required; Popover, Select, Tooltip and Dropdown are taken only when a component needs them.
2. Restyle each on arrival to the TerrAI theme. shadcn's tokens, radii and shadows do not enter the project.
3. Rebuild `AuditDrawer` on Dialog, fixing:
   - the missing focus trap;
   - `aria-hidden` sitting on the drawer rather than the background;
   - the absent `role="dialog"` and `aria-modal="true"`;
   - focus being moved into an `aria-hidden` subtree.
4. Delete the hand-rolled focus and return-focus handling that the primitive now owns.
5. Turn the stage 01 axe baseline from "recorded" into "asserted" for the states now fixed.

## Non-goals

No decorative components. Card, Badge, Separator and Alert are explicitly not adopted — they are a styled `div`, they are what makes a product look like a template, and each copied file is owned code forever. No visual change to the drawer.

## Implementation notes

- The accessibility behaviour comes from Bits UI underneath, which does not require Tailwind. Depending on the primitives rather than the styling keeps that exit open.
- Review every copied file on arrival as project source, because that is what it becomes.
- Escape-to-close, click-outside-to-close and focus return already work; the primitive must preserve them, not merely replace them.
- The drawer holds long trilingual prose. Check scrolling and focus order with the longest Japanese and English content, not the shortest.

## Acceptance

- The four defects are gone, each asserted by an axe or Playwright check rather than by reading the markup.
- Escape, click-outside and focus return behave as before.
- Stage 01 screenshots of the drawer are unchanged.
- Only behaviour-hard primitives were copied in; no decorative component is present.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
