# UI Design System and Review Guardrails

- Status: Planned
- Date: 2026-07-21
- Baseline: `main` / `b8fcfc3`
- Type: frontend styling platform; no change to analytical behaviour, data, or the API
- Depends on: [maplibre-migration](../maplibre-migration/00-overview.md) stages 01–05, which are complete

## Why

Most code in this repository is now written by AI. That changes what a styling system is for.

Hand-written CSS lets each change invent a class name, a colour and a spacing value. All of them render plausibly, so a reviewer has to hold the intended design in their head and diff against it by eye. At the current size — ten components (nine under `webapp/src/lib/components/` plus `App.svelte`), 186 lines of CSS, 129 selectors — that is still possible. It stops being possible well before the site scene and the field client exist.

The goal is therefore not tidier CSS. **The goal is that a human can review UI changes they did not write**, by reading rule violations and rendered-output diffs instead of class strings.

Three properties deliver that, and none of them is "install Tailwind":

1. Values outside the design system are **impossible to write silently** — they fail a check rather than rendering a slightly-off green.
2. Visual change is **visible as an image diff**, because no reviewer can diff CSS in their head.
3. Interaction correctness is **asserted**, because accessible markup and plausible markup look identical in a diff.

## Decision

Adopt **Tailwind CSS v4** with a theme locked to the existing TerrAI tokens, and **shadcn-svelte** for behaviour-hard overlay primitives only.

Tailwind is chosen for the reason above: with a locked `@theme` and the default palette removed, an off-system value has to be written as an arbitrary value (`bg-[#1f7a58]`, `p-[13px]`), which is greppable and therefore enforceable. Plain CSS gives no such signal. Svelte's scoped styles already solve collisions and naming, so that is not what Tailwind is buying here.

shadcn-svelte components are copy-in, so they become this repository's code on arrival. That cuts both ways and shapes how they are used:

- **Take** the primitives whose behaviour is hard and easy to get subtly wrong: Dialog, Popover, Select, Tooltip, Dropdown. Focus trapping, keyboard navigation and ARIA state machines are where hand-written overlays fail.
- **Do not take** components that are a styled `div` — Card, Badge, Separator, Alert. They are five lines of local markup, they are what makes a product look like a template, and every copied file is code that must be reviewed forever.
- **Restyle on arrival.** The default look is what makes shadcn products indistinguishable. TerrAI already has an identity — forest and lime palette, the serif brand mark, dashed underlines as the "auditable value" affordance. That identity survives; shadcn's does not enter.

Note that the accessibility behaviour comes from Bits UI underneath, which does not depend on Tailwind (`peerDependencies` are `svelte` and `@internationalized/date` only). If Tailwind is ever dropped, the primitives can stay.

## Evidence this is needed

`webapp/src/lib/components/AuditDrawer.svelte` is the product's core component — the audit trail is the central claim — and its hand-rolled overlay has four defects that read as correct markup:

1. **No focus trap.** Tab from the close button moves into the page behind the drawer.
2. **`aria-hidden` is on the drawer itself, not the background.** While open, the whole application stays exposed to screen readers.
3. **It is not a dialog.** No `role="dialog"`, no `aria-modal="true"`, so assistive technology never announces it as modal.
4. **Focus is moved into an `aria-hidden` subtree.** The `$effect` focuses the close button; browsers now warn about this.

None of these are visible in a code diff to a reviewer who is not looking for them. All of them are prevented by a real dialog primitive, and all of them would be caught by an automated accessibility assertion.

## Non-goals

- **No visual redesign.** Every stage before the last must leave the rendered output unchanged; that is what makes the snapshots meaningful. Deliberate design changes come later, as their own work, reviewed against a baseline that exists.
- **No shadcn theme, no shadcn look.** Its tokens, radii and shadows do not enter the project.
- **No component library for layout.** Grid and flex stay local to components.
- **No change to `messages.ts`, `modules.ts`, `layers.ts`, or anything under `terrai_spatial/`.** This is styling and its guardrails only.
- **Not a design-token expansion.** The twelve existing tokens are the system until a real need adds a thirteenth.

## Stage map

Ordered so that the safety net exists before anything it protects is touched.

| Stage | Plan | Purpose |
|---|---|---|
| 01 | [visual and a11y baseline](01-visual-and-a11y-baseline-pr1.md) | Playwright screenshots and axe assertions against today's UI. No production change. |
| 02 | [Tailwind with a locked theme](02-tailwind-locked-theme-pr2.md) | Install v4, express the twelve tokens as `@theme`, remove the default palette. Nothing restyled. |
| 03 | [theme enforcement](03-theme-enforcement-pr3.md) | A check that fails on arbitrary values and off-theme colours. |
| 04 | [port components to the theme](04-port-components-to-theme-pr4.md) | Restyle all ten components; delete the replaced rules from `app.css`. |
| 05 | [overlay primitives](05-overlay-primitives-pr5.md) | shadcn-svelte Dialog for the audit drawer; the four defects above are fixed and asserted. |

Each stage is its own pull request, states its own acceptance commands, and leaves the suite and validation passing when it merges. Stage 01 must merge before 02 begins: without a baseline, "the UI did not change" is an opinion.

## Consequences accepted

- **Screenshot tests need a stable environment.** They fail on font and rendering differences between machines. Pin the Playwright browser version and generate baselines in one place; expect to regenerate them deliberately, and never regenerate them to make a red build green without looking at the diff.
- **The twelve tokens become a hard boundary.** Adding a colour becomes a deliberate act with a review, which is the point, and will feel obstructive the first time it blocks something legitimate.
- **Copied shadcn components are owned code.** They do not update themselves, and each one must be reviewed on arrival like any other source file.
- **Class strings get longer.** Utility-first markup is harder to skim than a semantic class name. That cost is accepted because the reviewer's job moves from reading markup to reading violations and image diffs.

## Constraints that outrank styling

- **Trilingual text length.** The same label differs by more than a factor of two across Chinese, Japanese and English. The sidebar is a fixed `238px` (`205px` under the narrow breakpoint). Fixed widths and `white-space: nowrap` break layouts here far more often than any styling choice; every stage must check the longest English string, not just the Chinese default.
- **The map owns most pixels.** MapLibre, deck.gl and Three.js are styled through their own APIs. Tailwind governs the chrome only, which is a smaller surface than it appears — do not attempt to route map styling through the theme.
- **The audit affordance is product surface, not decoration.** The dashed underline that marks an auditable value must survive every restyle intact.

## Open questions

1. Whether the twelve tokens are sufficient once the site scene lands, or whether a subsurface palette is needed as a separate scale.
2. Whether screenshot baselines are generated in CI or committed from a developer machine. There is no CI workflow in this repository yet, which stage 01 has to resolve one way or the other.
3. Whether the enforcement check lives in the JavaScript toolchain or in `terrai validate` alongside the other repository contracts.
