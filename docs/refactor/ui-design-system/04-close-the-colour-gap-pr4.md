# PR4 Plan: Close the Colour Gap

- Status: Completed
- Refactor: `ui-design-system`
- PR: #4

## Goal

Close the remaining gap in the colour lock, so that every colour in the web app is either a palette entry or recorded debt.

**This stage was narrowed deliberately.** It was planned as a mechanical port of all ten components to utility classes. Measuring first showed that would be poor value: the port is 129 rules across 84 selectors, its output is about to be replaced by the redesign, and it is not what the technical goal needs. What the goal needed was elsewhere — `app.css` was not scanned by the check at all, and it is where most of the styling lives.

## Scope

1. **Extend the check to stylesheets**, exempting the `@theme` block, which is where colour is supposed to be written.
2. **Collapse the duplicate custom properties.** `:root` restated the twelve palette values instead of referring to them — the mechanism by which `lime` came to mean two different greens. It now aliases the theme tokens, so a colour has exactly one value.
3. **Inventory the stylesheet's inherited colour.** `app.css` holds 59 one-off tints and overlays picked by eye. Turning them into palette entries would make the palette a colour dump rather than a design system, and they disappear with the redesign. They are asserted as an exact set instead: a new one fails, and so does removing one without updating the list.

### Deferred to the redesign, not done here

Porting the ten components to utilities, deleting each `app.css` rule as its component stops needing it, and checking the longest English strings against the sidebar width. Those are worth doing when the components are rewritten rather than twice.

## Non-goals

No redesign. No markup restructuring beyond what styling requires. No accessibility work — stage 05. No new components.

## Implementation notes

- Port one component per commit. A single commit touching all ten makes the screenshot diff unreadable, which defeats the reason the baseline exists.
- **Small visual diffs are acceptable here, and are reviewed rather than forbidden.** The earlier rule demanded pixel neutrality; that was dropped deliberately. The applications are exploratory and about to be rewritten, so preserving spacing that was set by eye costs more than it is worth. What must not happen is a diff nobody looked at: regenerate baselines as part of the review, with the images in the pull request, not to turn a red build green.
- The screenshots still earn their place — they turn "did anything move" from an opinion into an artefact. Their purpose in this stage is disclosure, not prohibition.
- `MapCard` is the largest at 133 lines and interacts with the map canvas; port it last, once the pattern is settled.

## Acceptance

- A colour literal added anywhere — stylesheet, component or TypeScript — fails a check.
- The twelve interface tokens have exactly one definition each.
- Screenshots are unchanged: aliasing custom properties is not supposed to move a pixel.
- The dashed audit affordance renders identically. This one is not negotiable: it is the product's signal that a value is auditable.
- `uv run pytest` and `uv run python -m terrai_spatial validate` pass.
