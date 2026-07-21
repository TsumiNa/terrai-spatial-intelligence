# PR4 Plan: Port Components to the Theme

- Status: Completed
- Refactor: `ui-design-system`
- PR: #4

## Goal

Close the remaining gap in the colour lock, so that every colour in the web app is either a palette entry or recorded debt.

**This stage was narrowed deliberately.** It was planned as a mechanical port of all ten components to utility classes. Measuring first showed that would be poor value: the port is 129 rules across 84 selectors, its output is about to be replaced by the redesign, and it is not what the technical goal needs. What the goal needed was elsewhere — `app.css` was not scanned by the check at all, and it is where most of the styling lives.

## Scope

1. Port all ten: the nine under `webapp/src/lib/components/` — `Sidebar`, `Topbar`, `Hero`, `Metrics`, `QueuePanel`, `MapCard`, `AuditTrigger`, `FeaturePopup`, `AuditDrawer` — plus `webapp/src/App.svelte`.
Deleting each `app.css` rule as its component stops needing it. `app.css` should retain only genuinely global concerns — resets, base typography, and anything the map libraries need.
These are worth doing when the components are rewritten rather than twice.

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
