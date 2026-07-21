# PR2 Plan: Tailwind with a Locked Theme

- Status: Planned
- Refactor: `ui-design-system`
- PR: #2

## Goal

Install Tailwind v4 and express the existing design tokens as the only values it offers, without restyling anything.

## Scope

1. Add Tailwind v4 and its Vite plugin to `webapp`.
2. Declare the twelve existing tokens in `@theme`: `ink`, `muted`, `line`, `paper`, `white`, `forest`, `green`, `lime`, `amber`, `red`, `blue`, `shadow`. They keep their current values; this stage moves them, it does not change them.
3. **Remove Tailwind's default palette** so `bg-blue-500` does not exist. An off-system colour must be a build or lint failure, not a slightly wrong green that renders.
4. Constrain the spacing and radius scales to what the current design actually uses.
5. Leave `app.css` in place and unconverted. Tailwind and the existing stylesheet coexist for one stage.

## Non-goals

No component is restyled. No rule is deleted from `app.css`. No enforcement yet — that is stage 03. No component library.

## Implementation notes

- Tailwind v4 configures through CSS `@theme` rather than a JavaScript config file. Do not add `tailwind.config.js` out of habit.
- Removing the default palette is the point of this stage. If `bg-blue-500` still resolves at the end, the stage has not achieved anything.
- Check the generated CSS is not larger than what it will replace; if the default palette is still being emitted, it was not actually removed.

## Acceptance

- The application builds and serves.
- Stage 01 screenshots are unchanged — this is the whole verification, since the visible result should be identical.
- A scratch component using `bg-blue-500` fails to build or produces no style; a scratch component using `bg-forest` works.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
