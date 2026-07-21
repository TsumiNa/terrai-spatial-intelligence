# PR2 Plan: Tailwind with a Locked Theme

- Status: Completed
- Refactor: `ui-design-system`
- PR: #2

## Goal

Install Tailwind v4 and express the existing design tokens as the only values it offers, without restyling anything.

## Scope

1. Add Tailwind v4 and its Vite plugin to `webapp`.
2. Declare the twelve existing tokens in `@theme`: `ink`, `muted`, `line`, `paper`, `white`, `forest`, `green`, `lime`, `amber`, `red`, `blue`, `shadow`. They keep their current values; this stage moves them, it does not change them.
3. **Remove Tailwind's default palette** so `bg-blue-500` does not exist. An off-system colour must be a build or lint failure, not a slightly wrong green that renders.
4. Constrain the radius and shadow scales to what the current design actually uses, named by role rather than size.
5. **Leave the spacing scale at Tailwind's default.** Measured while doing this: 32 of the 51 pixel values in `app.css` are not multiples of four — 1, 3, 5, 7, 9, 11, 13, 17, 18, 21 — so 63% of the existing design cannot be expressed on any regular scale. Constraining spacing here would force stage 04 to change pixels, which it is defined not to do. Stages 03 and 04 have to resolve this; see the note below.
5. Leave `app.css` in place and unconverted. Tailwind and the existing stylesheet coexist for one stage.

## Non-goals

No component is restyled. No rule is deleted from `app.css`. No enforcement yet — that is stage 03. No primitives either: Bits UI arrives in stage 05, not here.

## Implementation notes

- Tailwind v4 configures through CSS `@theme` rather than a JavaScript config file. Do not add `tailwind.config.js` out of habit.
- Removing the default palette is the point of this stage. If `bg-blue-500` still resolves at the end, the stage has not achieved anything.
- Check the generated CSS is not larger than what it will replace; if the default palette is still being emitted, it was not actually removed.

## Findings carried forward

- **63% of the existing spacing is off-scale.** The design was written by eye, so stage 04 cannot express it through spacing utilities without arbitrary values, which is what stage 03 rejects. Stage 03 must decide whether its rule targets design-system values (colours, radii, shadows) or all arbitrary values; stage 04 must decide whether ad-hoc spacing stays in component CSS.
- **Preflight is not imported.** Tailwind's reset changed 6% of the pixels on every screenshot — the baseline caught it immediately. Adopting it is worth doing later, as a deliberate change reviewed against regenerated baselines, not as a side effect of installing the framework.

## Acceptance

- The application builds and serves.
- Stage 01 screenshots are unchanged — this is the whole verification, since the visible result should be identical.
- A scratch component using `bg-blue-500` fails to build or produces no style; a scratch component using `bg-forest` works.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
