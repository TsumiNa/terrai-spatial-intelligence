# UI Design System and Review Guardrails

- Status: Completed
- Date: 2026-07-21
- Baseline: `main` / `b8fcfc3`
- Type: frontend styling platform; no change to analytical behaviour, data, or the API
- Depends on: [maplibre-migration](../maplibre-migration/00-overview.md) stages 01–05, which are complete

## Why

Most code in this repository is now written by AI. That changes what a styling system is for.

Hand-written CSS lets each change invent a class name, a color and a spacing value. All of them render plausibly, so a reviewer has to hold the intended design in their head and diff against it by eye. At the current size — ten components (nine under `webapp/src/lib/components/` plus `App.svelte`), 186 lines of CSS, 129 selectors — that is still possible. It stops being possible well before the site scene and the field client exist.

The goal is therefore not tidier CSS. **The goal is that a human can review UI changes they did not write**, by reading rule violations and rendered-output diffs instead of class strings.

The current applications are exploratory. They will be substantially rewritten once the requirements are settled, and the UI will grow well beyond today's ten components. That is the premise this refactor rests on, and it inverts the obvious objection: the guardrails are worth building *before* the rewrite, not after, because the rewrite is when the most code is produced and when reviewing it matters most. Establishing them afterwards means paying to retrofit exactly the code that was written without them.

Three properties deliver that, and none of them is "install Tailwind":

1. Values outside the design system are **impossible to write silently** — they fail a check rather than rendering a slightly-off green. This applies to the **palette only**; see below.
2. Visual change is **visible as an image diff**, because no reviewer can diff CSS in their head.
3. Interaction correctness is **asserted**, because accessible markup and plausible markup look identical in a diff.

## Decision

Adopt **Tailwind CSS v4** with a theme locked to the existing TerrAI tokens, and **Bits UI** for behaviour-hard overlay primitives only.

Tailwind is chosen for the reason above: with a locked `@theme` and the default palette removed, an off-system value has to be written as an arbitrary value (`bg-[#1f7a58]`, `p-[13px]`), which is greppable and therefore enforceable. Plain CSS gives no such signal. Svelte's scoped styles already solve collisions and naming, so that is not what Tailwind is buying here.

Two properties decide it, and both depend on the growth premise. Model output converges on convention, and Tailwind is the convention — an AI writing bespoke CSS invents a class, a scale and a near-miss color every time, while an AI writing Tailwind produces something a reviewer has seen before. And a violation is *visible* rather than merely *detectable*: `bg-[#1f7a58]` reads as an escape hatch at a glance, where a raw hex in a stylesheet looks like ordinary code and its detection depends entirely on the linter's coverage.

Stylelint against plain CSS could enforce the same tokens, and at today's size that would be lighter. It was the better answer while the UI was ten components and stable. It stops being the better answer once most of the UI is yet to be written.

Bits UI is taken directly rather than through shadcn-svelte, which was the earlier intention. shadcn-svelte contributes no behaviour: its components are copy-in wrappers around Bits UI, styled with Tailwind and carrying a specific visual language. Once the plan discards the styling and refuses the decorative components, roughly a tenth of it is left — some composition scaffolding worth a dozen lines to write.

The decisive argument is the update path. Copy-in is an advantage for ordinary components, where nobody wants an upstream change to move their UI. It is a liability for accessibility primitives, where correctness *is* the value and correctness problems are discovered over time: new screen-reader behaviour, new browser semantics, new readings of WCAG. A versioned dependency receives those fixes; a copied snapshot receives them only if somebody tracks the upstream diff. **For this category, being a consumer beats being an owner.**

Only the primitives are taken, and each is wrapped in a thin local component styled from the theme:

- **Take** the primitives whose behaviour is hard and easy to get subtly wrong: Dialog, Popover, Select, Tooltip, Dropdown. Focus trapping, keyboard navigation and ARIA state machines are where hand-written overlays fail.
- **Do not take** anything that is a styled `div` — cards, badges, separators, alerts. They are five lines of local markup and they are what makes a product look like a template.

As of `bits-ui@2.18.1`, its `peerDependencies` are `svelte` and `@internationalized/date` only, so it pulls in no styling framework and the styling decision stays independent of the primitive decision. Recheck on upgrade rather than assuming it holds.

## Evidence this is needed

`webapp/src/lib/components/AuditDrawer.svelte` is the product's core component — the audit trail is the central claim — and its hand-rolled overlay has four defects that read as correct markup:

1. **No focus trap.** Tab from the close button moves into the page behind the drawer.
2. **`aria-hidden` is on the drawer itself, not the background.** While open, the whole application stays exposed to screen readers.
3. **It is not a dialog.** No `role="dialog"`, no `aria-modal="true"`, so assistive technology never announces it as modal.
4. **Focus is moved into an `aria-hidden` subtree.** The `$effect` focuses the close button; browsers now warn about this.

None of these are visible in a code diff to a reviewer who is not looking for them. All of them are prevented by a real dialog primitive, and all of them would be caught by an automated accessibility assertion.

## Non-goals

- **No visual redesign.** Every stage before the last must leave the rendered output unchanged; that is what makes the snapshots meaningful. Deliberate design changes come later, as their own work, reviewed against a baseline that exists.
- **No component library's visual language.** No third-party tokens, radii or shadows enter the project; primitives arrive unstyled and are dressed from the theme.
- **No component library for layout.** Grid and flex stay local to components.
- **No change to `messages.ts`, `modules.ts`, `layers.ts`, or anything under `terrai_spatial/`.** This is styling and its guardrails only.
- **Not a design-token expansion.** The twelve existing tokens are the system until a real need adds a thirteenth.

## Stage map

Ordered so that the safety net exists before anything it protects is touched.

| Stage | Plan | Purpose |
|---|---|---|
| 01 | [visual and a11y baseline](01-visual-and-a11y-baseline-pr1.md) | Playwright screenshots and axe assertions against today's UI. No production change. |
| 02 | [Tailwind with a locked theme](02-tailwind-locked-theme-pr2.md) | Install v4, express the twelve tokens as `@theme`, remove the default palette. Nothing restyled. |
| 03 | [theme enforcement](03-theme-enforcement-pr3.md) | A check that fails on arbitrary values and off-theme colors. |
| 04 | [close the color gap](04-close-the-color-gap-pr4.md) | Extend the check to stylesheets, collapse the duplicated tokens, inventory the inherited color. |
| 05 | [overlay primitives](05-overlay-primitives-pr5.md) | Bits UI Dialog for the audit drawer; the four defects above are fixed and asserted. |

Each stage is its own pull request, states its own acceptance commands, and leaves the suite and validation passing when it merges. Stage 01 must merge before 02 begins: without a baseline, "the UI did not change" is an opinion.

**All five stages run to completion before the applications are redesigned.** They are short, and running them alongside a redesign mixes two kinds of diff — "the styling system moved" and "the design changed" — in the same review, where neither can be read. The guardrails are cheapest to install against a UI that is holding still.

## Consequences accepted

- **Screenshot tests need a stable environment.** They fail on font and rendering differences between machines. Pin the Playwright browser version and generate baselines in one place.
- **Baselines are migration scaffolding with a known expiry.** They exist to prove stages 02–05 changed nothing they did not intend to. They are not a permanent regression suite for these particular screens, which are exploratory and will be replaced. Two cases, and conflating them makes the rule either violated or obstructive:
  - **During this refactor**, a screenshot diff is a defect. Do not regenerate to go green.
  - **During a deliberate redesign**, baselines are regenerated wholesale as part of reviewing that design. That is normal, and the diff is the artefact under review rather than a failure.
- **The twelve colors become a hard boundary, not a fixed set.** They are extracted from the design that exists today. The redesign will need more, and the site scene may need a subsurface scale. Extending the theme is a normal reviewed act; the boundary exists so that extension is *deliberate*, not so that the count stays at twelve. If adding a token feels like fighting the system, the system is being read wrong — the failure mode to prevent is a component reaching past the theme, not the theme growing.
- **Bits UI becomes a runtime dependency.** An upstream change can move behaviour, which is the cost of receiving upstream accessibility fixes. Pin it and read its changelog on upgrade.
- **Class strings get longer.** Utility-first markup is harder to skim than a semantic class name. That cost is accepted because the reviewer's job moves from reading markup to reading violations and image diffs.

## Constraints that outrank styling

- **Trilingual text length.** The same label differs by more than a factor of two across Chinese, Japanese and English. The sidebar is a fixed `238px` (`205px` under the narrow breakpoint). Fixed widths and `white-space: nowrap` break layouts here far more often than any styling choice; every stage must check the longest English string, not just the Chinese default.
- **The map owns most pixels.** MapLibre, deck.gl and Three.js are styled through their own APIs. Tailwind governs the chrome only, which is a smaller surface than it appears — do not attempt to route map styling through the theme.
- **The audit affordance is product surface, not decoration.** The dashed underline that marks an auditable value must survive every restyle intact.

## Open questions

1. What the redesign needs from the theme. The twelve tokens describe today's exploratory applications; the site scene in particular may want a subsurface scale that does not exist yet.
2. ~~Where screenshot baselines are generated.~~ Resolved in stage 01: both platform variants are committed, and the Linux set comes from a `workflow_dispatch` job that uploads for review rather than committing.
3. Whether the enforcement check lives in the JavaScript toolchain or in `terrai validate` alongside the other repository contracts.
